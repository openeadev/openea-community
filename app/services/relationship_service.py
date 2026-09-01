from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.metamodel import ArchitectureRelationship
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.services.audit_service import AuditService
from app.services.job_service import JobService
from app.services.metamodel_service import (
    MetamodelService,
    PropertyValidationError,
    RelationshipValidationError,
)


class RelationshipServiceError(ValueError):
    pass


class RelationshipService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.objects = ObjectRepository(db)
        self.relationships = RelationshipRepository(db)
        self.metamodel = MetamodelService(db)
        self.audit = AuditService(db)

    def create_relationship(self, *, relationship_key: str, source_object_id: str, target_object_id: str,
                            description: str = "", criticality: str | None = None, confidence: str | None = None,
                            valid_from: str | None = None, valid_until: str | None = None, source: str | None = None,
                            properties: dict[str, Any] | None = None, actor: User, audit_source: str = "Web",
                            correlation_id: str | None = None) -> ArchitectureRelationship:
        source_obj = self.objects.get_by_id(source_object_id)
        target_obj = self.objects.get_by_id(target_object_id)
        if source_obj is None or target_obj is None:
            raise RelationshipServiceError("Source and target objects must be active repository objects")
        try:
            rel_type = self.metamodel.validate_relationship_rule(relationship_key, source_obj.object_type.key, target_obj.object_type.key)
            validated_properties = self.metamodel.validate_relationship_properties(relationship_key, properties or {})
        except (RelationshipValidationError, PropertyValidationError) as exc:
            raise RelationshipServiceError(str(exc)) from exc
        start = self._parse_date(valid_from, "Valid from")
        end = self._parse_date(valid_until, "Valid until")
        if start and end and end < start:
            raise RelationshipServiceError("Valid until cannot be before valid from")
        self._validate_enum("criticality", criticality)
        self._validate_enum("confidence", confidence)
        self._validate_enum("source", source)
        rel = ArchitectureRelationship(
            relationship_type=rel_type, source_object=source_obj, target_object=target_obj,
            description=description.strip(), criticality=criticality or None, confidence=confidence or None,
            valid_from=start, valid_until=end, source=source or None, properties=validated_properties,
            provenance={}, created_by=actor.id, updated_by=actor.id,
        )
        try:
            self.relationships.add(rel)
            self.audit.record(action="RelationshipCreated", entity_type="relationship", entity_id=rel.id, actor=actor, after=self.audit.relationship_state(rel), source=audit_source, correlation_id=correlation_id)
            self.audit.record(action="RelationshipCreated", entity_type="object", entity_id=source_obj.id, actor=actor, after={"relationship_id": rel.id, "target_object_id": target_obj.id, "relationship_type": rel_type.key}, source=audit_source, correlation_id=correlation_id)
            self.audit.record(action="RelationshipCreated", entity_type="object", entity_id=target_obj.id, actor=actor, after={"relationship_id": rel.id, "source_object_id": source_obj.id, "relationship_type": rel_type.key}, source=audit_source, correlation_id=correlation_id)
            JobService(self.db).enqueue_metrics_recalculation()
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise RelationshipServiceError("This relationship already exists") from exc
        return rel

    def update_relationship(
        self,
        rel: ArchitectureRelationship,
        *,
        description: str,
        criticality: str | None,
        confidence: str | None,
        valid_from: str | None,
        valid_until: str | None,
        source: str | None,
        properties: dict[str, Any],
        actor: User,
        relationship_key: str | None = None,
        target_object_id: str | None = None,
        audit_source: str = "Web",
        correlation_id: str | None = None,
    ) -> ArchitectureRelationship:
        before = self.audit.relationship_state(rel)
        old_target_id = rel.target_object_id

        target_obj = rel.target_object
        if target_object_id is not None:
            target_obj = self.objects.get_by_id(target_object_id)
            if target_obj is None:
                raise RelationshipServiceError("Target object must be an active repository object")

        selected_relationship_key = relationship_key or rel.relationship_type.key
        try:
            rel_type = self.metamodel.validate_relationship_rule(
                selected_relationship_key,
                rel.source_object.object_type.key,
                target_obj.object_type.key,
            )
            validated = self.metamodel.validate_relationship_properties(
                selected_relationship_key, properties
            )
        except (RelationshipValidationError, PropertyValidationError) as exc:
            raise RelationshipServiceError(str(exc)) from exc

        start = self._parse_date(valid_from, "Valid from")
        end = self._parse_date(valid_until, "Valid until")
        if start and end and end < start:
            raise RelationshipServiceError("Valid until cannot be before valid from")
        self._validate_enum("criticality", criticality)
        self._validate_enum("confidence", confidence)
        self._validate_enum("source", source)

        rel.relationship_type = rel_type
        rel.target_object = target_obj
        rel.description = description.strip()
        rel.criticality = criticality or None
        rel.confidence = confidence or None
        rel.valid_from = start
        rel.valid_until = end
        rel.source = source or None
        rel.properties = validated
        rel.updated_by = actor.id
        rel.updated_at = datetime.now(timezone.utc)

        try:
            self.db.flush()
            self.audit.record(
                action="RelationshipUpdated",
                entity_type="relationship",
                entity_id=rel.id,
                actor=actor,
                before=before,
                after=self.audit.relationship_state(rel),
                source=audit_source,
                correlation_id=correlation_id,
            )
            self.audit.record(
                action="RelationshipUpdated",
                entity_type="object",
                entity_id=rel.source_object_id,
                actor=actor,
                after={"relationship_id": rel.id},
                source=audit_source,
                correlation_id=correlation_id,
            )
            target_ids = {old_target_id, rel.target_object_id}
            for object_id in target_ids:
                self.audit.record(
                    action="RelationshipUpdated",
                    entity_type="object",
                    entity_id=object_id,
                    actor=actor,
                    after={"relationship_id": rel.id},
                    source=audit_source,
                    correlation_id=correlation_id,
                )
            JobService(self.db).enqueue_metrics_recalculation()
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise RelationshipServiceError("This relationship already exists") from exc
        return rel

    def archive_relationship(self, rel: ArchitectureRelationship, *, actor: User) -> None:
        before = self.audit.relationship_state(rel)
        rel.archived_at = datetime.now(timezone.utc)
        rel.updated_at = rel.archived_at
        rel.updated_by = actor.id
        self.audit.record(action="RelationshipArchived", entity_type="relationship", entity_id=rel.id, actor=actor, before=before, after=self.audit.relationship_state(rel))
        self.audit.record(action="RelationshipArchived", entity_type="object", entity_id=rel.source_object_id, actor=actor, after={"relationship_id": rel.id})
        self.audit.record(action="RelationshipArchived", entity_type="object", entity_id=rel.target_object_id, actor=actor, after={"relationship_id": rel.id})
        JobService(self.db).enqueue_metrics_recalculation()
        self.db.commit()

    def _validate_enum(self, key: str, value: str | None) -> None:
        if value and value not in self.metamodel._enumeration_values(key):
            raise RelationshipServiceError(f"Invalid value for {key}")

    @staticmethod
    def _parse_date(value: str | None, label: str) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise RelationshipServiceError(f"{label} must be a valid date") from exc
