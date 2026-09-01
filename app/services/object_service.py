from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.governance import AuditEvent
from app.models.metamodel import ArchitectureObject, ObjectAlias
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.audit_service import AuditService
from app.services.governance_service import GovernanceService
from app.services.job_service import JobService
from app.services.metamodel_service import MetamodelService, PropertyValidationError


class ObjectValidationError(ValueError):
    pass


class ObjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.objects = ObjectRepository(db)
        self.metamodel = MetamodelService(db)
        self.audit = AuditService(db)

    def create_object(
        self,
        *,
        object_type_key: str,
        name: str,
        description: str,
        record_status: str,
        governance_status: str | None,
        lifecycle_stage: str | None,
        criticality: str | None,
        owner_organization_id: str | None,
        owner_role_id: str | None,
        source: str | None,
        confidence: str | None,
        valid_from: str | None,
        valid_until: str | None,
        aliases: str,
        tags: str,
        properties: dict[str, Any],
        actor: User,
        review_frequency: str | None = None,
        correlation_id: str | None = None,
        audit_source: str = "Web",
    ) -> ArchitectureObject:
        if review_frequency and review_frequency not in {"Monthly", "Quarterly", "Semiannual", "Annual"}:
            raise ObjectValidationError("Invalid review frequency")
        object_type = self.objects.get_type_by_key(object_type_key)
        if object_type is None:
            raise ObjectValidationError("Unknown object type")
        validated = self._validate_common(
            object_type_key=object_type_key,
            name=name,
            record_status=record_status,
            governance_status=governance_status,
            lifecycle_stage=lifecycle_stage,
            criticality=criticality,
            owner_organization_id=owner_organization_id,
            owner_role_id=owner_role_id,
            source=source,
            confidence=confidence,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        try:
            validated_properties = self.metamodel.validate_object_properties(object_type_key, properties)
        except PropertyValidationError as exc:
            raise ObjectValidationError(str(exc)) from exc
        self._validate_property_references(object_type, validated_properties)

        governance_status = "Draft"
        if object_type_key == "architecture_principle":
            validated_properties["status"] = "Draft"
            governance_status = "Draft"
        elif object_type_key == "architecture_decision":
            validated_properties["decision_status"] = "Draft"
            validated_properties.pop("decision_number", None)
            governance_status = "Draft"

        obj = ArchitectureObject(
            object_type=object_type,
            name=name.strip(),
            description=description.strip(),
            record_status=record_status,
            governance_status=governance_status or None,
            lifecycle_stage=lifecycle_stage or None,
            criticality=criticality or None,
            owner_organization_id=owner_organization_id or None,
            owner_role_id=owner_role_id or None,
            source=source or None,
            confidence=confidence or None,
            valid_from=validated["valid_from"],
            valid_until=validated["valid_until"],
            properties=validated_properties,
            review_frequency=review_frequency or None,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.objects.add(obj)
        GovernanceService(self.db).assign_decision_number(obj)
        obj.aliases = [ObjectAlias(alias=value) for value in self._split_values(aliases)]
        obj.tags = [self.objects.get_or_create_tag(value) for value in self._split_values(tags)]
        self.audit.record(action="ObjectCreated", entity_type="object", entity_id=obj.id, actor=actor, after=self.audit.object_state(obj), source=audit_source, correlation_id=correlation_id)
        JobService(self.db).enqueue_metrics_recalculation(correlation_id=correlation_id)
        self._commit_object_changes()
        return obj

    def update_object(
        self,
        obj: ArchitectureObject,
        *,
        actor: User,
        correlation_id: str | None = None,
        audit_source: str = "Web",
        **values: Any,
    ) -> ArchitectureObject:
        before = self.audit.object_state(obj)
        if values.get("review_frequency") and values.get("review_frequency") not in {"Monthly", "Quarterly", "Semiannual", "Annual"}:
            raise ObjectValidationError("Invalid review frequency")
        object_type_key = obj.object_type.key
        validated = self._validate_common(
            object_type_key=object_type_key,
            name=str(values["name"]),
            record_status=str(values["record_status"]),
            governance_status=values.get("governance_status"),
            lifecycle_stage=values.get("lifecycle_stage"),
            criticality=values.get("criticality"),
            owner_organization_id=values.get("owner_organization_id"),
            owner_role_id=values.get("owner_role_id"),
            source=values.get("source"),
            confidence=values.get("confidence"),
            valid_from=values.get("valid_from"),
            valid_until=values.get("valid_until"),
        )
        try:
            properties = self.metamodel.validate_object_properties(object_type_key, values.get("properties", {}))
        except PropertyValidationError as exc:
            raise ObjectValidationError(str(exc)) from exc

        values["governance_status"] = obj.governance_status
        if object_type_key == "architecture_principle":
            properties["status"] = obj.properties.get("status", "Draft")
            values["governance_status"] = obj.governance_status
        elif object_type_key == "architecture_decision":
            properties["decision_status"] = obj.properties.get("decision_status", "Draft")
            properties["decision_number"] = obj.properties.get("decision_number")
            values["governance_status"] = obj.governance_status

        obj.name = str(values["name"]).strip()
        obj.description = str(values.get("description", "")).strip()
        obj.record_status = str(values["record_status"])
        obj.governance_status = values.get("governance_status") or None
        obj.lifecycle_stage = values.get("lifecycle_stage") or None
        obj.criticality = values.get("criticality") or None
        obj.owner_organization_id = values.get("owner_organization_id") or None
        obj.owner_role_id = values.get("owner_role_id") or None
        obj.source = values.get("source") or None
        obj.confidence = values.get("confidence") or None
        obj.valid_from = validated["valid_from"]
        obj.valid_until = validated["valid_until"]
        obj.properties = properties
        obj.review_frequency = values.get("review_frequency") or None
        self._replace_aliases(obj, str(values.get("aliases", "")))
        obj.tags = [self.objects.get_or_create_tag(value) for value in self._split_values(str(values.get("tags", "")))]
        obj.updated_by = actor.id
        obj.updated_at = datetime.now(timezone.utc)
        self.audit.record(action="ObjectUpdated", entity_type="object", entity_id=obj.id, actor=actor, before=before, after=self.audit.object_state(obj), source=audit_source, correlation_id=correlation_id)
        JobService(self.db).enqueue_metrics_recalculation(correlation_id=correlation_id)
        self._commit_object_changes()
        return obj

    def archive_object(self, obj: ArchitectureObject, *, actor: User) -> None:
        before = self.audit.object_state(obj)
        now = datetime.now(timezone.utc)
        obj.archived_at = now
        obj.record_status = "Archived"
        obj.updated_at = now
        obj.updated_by = actor.id
        self.audit.record(action="ObjectArchived", entity_type="object", entity_id=obj.id, actor=actor, before=before, after=self.audit.object_state(obj))
        JobService(self.db).enqueue_metrics_recalculation()
        self.db.commit()

    def restore_object(self, obj: ArchitectureObject, *, actor: User) -> None:
        """Restore a soft-archived object while preserving its relationships and history."""
        if obj.archived_at is None:
            raise ObjectValidationError("Object is not archived")

        before = self.audit.object_state(obj)
        previous_event = self.db.scalar(
            select(AuditEvent)
            .where(
                AuditEvent.entity_type == "object",
                AuditEvent.entity_id == obj.id,
                AuditEvent.action == "ObjectArchived",
            )
            .order_by(AuditEvent.timestamp.desc())
            .limit(1)
        )
        previous_status = None
        if previous_event is not None and previous_event.before_state:
            candidate = previous_event.before_state.get("record_status")
            if isinstance(candidate, str) and candidate != "Archived":
                previous_status = candidate

        obj.archived_at = None
        obj.record_status = previous_status or "Inactive"
        obj.updated_at = datetime.now(timezone.utc)
        obj.updated_by = actor.id
        self.audit.record(
            action="ObjectRestored",
            entity_type="object",
            entity_id=obj.id,
            actor=actor,
            before=before,
            after=self.audit.object_state(obj),
        )
        JobService(self.db).enqueue_metrics_recalculation()
        self.db.commit()

    def _replace_aliases(self, obj: ArchitectureObject, raw_aliases: str) -> None:
        """Replace aliases without recreating unchanged rows.

        Reusing existing ObjectAlias rows avoids an INSERT-before-DELETE flush order
        that can violate uq_object_alias when an object is edited without changing
        its aliases. Submitted aliases are normalized and deduplicated
        case-insensitively by _split_values.
        """
        existing_by_key = {alias.alias.casefold(): alias for alias in obj.aliases}
        updated_aliases: list[ObjectAlias] = []

        for value in self._split_values(raw_aliases):
            existing = existing_by_key.get(value.casefold())
            if existing is None:
                existing = ObjectAlias(alias=value)
            else:
                existing.alias = value
            updated_aliases.append(existing)

        obj.aliases = updated_aliases

    def _commit_object_changes(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            diag = getattr(getattr(exc, "orig", None), "diag", None)
            if getattr(diag, "constraint_name", None) == "uq_object_alias":
                raise ObjectValidationError(
                    "Aliases must be unique within a record. Remove duplicate aliases and try again."
                ) from exc
            raise

    def _validate_common(
        self,
        *,
        object_type_key: str,
        name: str,
        record_status: str,
        governance_status: str | None,
        lifecycle_stage: str | None,
        criticality: str | None,
        owner_organization_id: str | None,
        owner_role_id: str | None,
        source: str | None,
        confidence: str | None,
        valid_from: str | None,
        valid_until: str | None,
    ) -> dict[str, date | None]:
        if not name.strip():
            raise ObjectValidationError("Name is required")
        self._validate_enum("record_status", record_status)
        if governance_status:
            self._validate_enum("governance_status", governance_status)
        if criticality:
            self._validate_enum("criticality", criticality)
        if source:
            self._validate_enum("source", source)
        if confidence:
            self._validate_enum("confidence", confidence)
        if lifecycle_stage:
            lifecycle_enum = self._lifecycle_enum_for_type(object_type_key)
            if lifecycle_enum:
                self._validate_enum(lifecycle_enum, lifecycle_stage)
        self._validate_reference(owner_organization_id, "organization", "Owner organization")
        self._validate_reference(owner_role_id, "role", "Owner role")
        start = self._parse_date(valid_from, "Valid from")
        end = self._parse_date(valid_until, "Valid until")
        if start and end and end < start:
            raise ObjectValidationError("Valid until cannot be before valid from")
        return {"valid_from": start, "valid_until": end}

    def _validate_enum(self, key: str, value: str) -> None:
        if value not in self.metamodel._enumeration_values(key):
            raise ObjectValidationError(f"Invalid value for {key.replace('_', ' ')}")

    def _validate_reference(self, object_id: str | None, expected_type: str, label: str) -> None:
        if not object_id:
            return
        ref = self.objects.get_by_id(object_id)
        if ref is None or ref.object_type.key != expected_type:
            raise ObjectValidationError(f"{label} is invalid")


    def _validate_property_references(self, object_type: Any, properties: dict[str, Any]) -> None:
        for name, spec in object_type.schema_definition.items():
            if not isinstance(spec, dict) or spec.get("type") != "object_reference":
                continue
            value = properties.get(name)
            expected_type = spec.get("target_object_type")
            if not value or not expected_type:
                continue
            ref = self.objects.get_by_id(str(value))
            if ref is None or ref.object_type.key != expected_type:
                raise ObjectValidationError(f"{name.replace('_', ' ').title()} references an invalid object")

    @staticmethod
    def _parse_date(value: str | None, label: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ObjectValidationError(f"{label} must be a valid date") from exc

    @staticmethod
    def _split_values(raw: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for item in raw.split(","):
            value = item.strip()
            key = value.casefold()
            if value and key not in seen:
                seen.add(key)
                result.append(value)
        return result

    @staticmethod
    def _lifecycle_enum_for_type(object_type_key: str) -> str | None:
        return {
            "business_product": "business_product_lifecycle",
            "business_process": "business_process_lifecycle",
            "application": "application_lifecycle",
            "application_service": "application_service_lifecycle",
            "technology": "technology_lifecycle",
        }.get(object_type_key)
