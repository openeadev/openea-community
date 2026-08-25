from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.findings import RuleDefinition
from app.models.metamodel import ObjectType, RelationshipRule, RelationshipType
from app.models.user import User
from app.services.audit_service import AuditService

SUPPORTED_RULE_TYPES = (
    "missing_field",
    "date_threshold",
    "missing_relationship",
    "relationship_count",
    "related_object_status",
    "risk_threshold",
    "review_overdue",
    "duplicate_name",
)
SEVERITIES = ("Low", "Medium", "High", "Critical")
DIRECTIONS = ("outbound", "inbound")
DATE_MODES = ("past", "within")
METRIC_TYPES = (
    "application_risk",
    "technology_risk",
    "capability_risk",
    "data_quality",
    "impact_severity",
)
UNIVERSAL_FIELDS = {
    "name",
    "description",
    "record_status",
    "governance_status",
    "lifecycle_stage",
    "criticality",
    "owner_organization_id",
    "owner_role_id",
    "source",
    "confidence",
    "valid_from",
    "valid_until",
    "last_reviewed_date",
    "next_review_date",
    "review_frequency",
}
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class CustomRuleValidationError(ValueError):
    pass


class CustomRuleService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_rule(self, *, payload: dict[str, Any], actor: User) -> RuleDefinition:
        normalized = self._normalize(payload)
        rule = RuleDefinition(
            rule_id=self._next_custom_rule_id(),
            name=normalized["name"],
            description=normalized["description"],
            rule_type=normalized["rule_type"],
            severity=normalized["severity"],
            config=normalized["config"],
            enabled=normalized["enabled"],
            is_system=False,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(rule)
        self.db.flush()
        AuditService(self.db).record(
            action="FindingRuleCreated",
            entity_type="rule_definition",
            entity_id=rule.id,
            actor=actor,
            after=self._state(rule),
        )
        self.db.commit()
        return rule

    def update_rule(self, rule: RuleDefinition, *, payload: dict[str, Any], actor: User) -> RuleDefinition:
        if rule.archived_at is not None:
            raise CustomRuleValidationError("Archived rules cannot be edited")
        before = self._state(rule)
        if rule.is_system:
            self._update_system_parameters(rule, payload)
        else:
            normalized = self._normalize(payload)
            rule.name = normalized["name"]
            rule.description = normalized["description"]
            rule.rule_type = normalized["rule_type"]
            rule.severity = normalized["severity"]
            rule.config = normalized["config"]
            rule.enabled = normalized["enabled"]
        rule.updated_by = actor.id
        AuditService(self.db).record(
            action="FindingRuleUpdated",
            entity_type="rule_definition",
            entity_id=rule.id,
            actor=actor,
            before=before,
            after=self._state(rule),
        )
        self.db.commit()
        return rule

    def archive_custom_rule(self, rule: RuleDefinition, *, actor: User) -> None:
        if rule.is_system:
            raise CustomRuleValidationError("Built-in rules cannot be deleted")
        if rule.archived_at is not None:
            return
        before = self._state(rule)
        rule.enabled = False
        rule.archived_at = datetime.now(timezone.utc)
        rule.updated_by = actor.id
        AuditService(self.db).record(
            action="FindingRuleArchived",
            entity_type="rule_definition",
            entity_id=rule.id,
            actor=actor,
            before=before,
            after=self._state(rule),
        )
        self.db.commit()

    def _update_system_parameters(self, rule: RuleDefinition, payload: dict[str, Any]) -> None:
        severity = str(payload.get("severity", rule.severity)).strip()
        if severity not in SEVERITIES:
            raise CustomRuleValidationError("Invalid severity")
        config = dict(rule.config)
        if rule.rule_type == "date_threshold":
            if "days" in config:
                config["days"] = self._integer(payload.get("days"), "Days", minimum=0, default=int(config.get("days", 0)))
            mode = str(payload.get("date_mode", config.get("mode", "within"))).strip()
            if mode not in DATE_MODES:
                raise CustomRuleValidationError("Invalid date threshold mode")
            config["mode"] = mode
        elif rule.rule_type == "relationship_count":
            if "min" in config:
                config["min"] = self._integer(payload.get("min_count"), "Minimum count", minimum=0, default=int(config["min"]))
            if "max" in config:
                config["max"] = self._integer(payload.get("max_count"), "Maximum count", minimum=0, default=int(config["max"]))
            if "min" in config and "max" in config and int(config["min"]) > int(config["max"]):
                raise CustomRuleValidationError("Minimum count cannot exceed maximum count")
        elif rule.rule_type == "risk_threshold":
            config["threshold"] = self._integer(payload.get("threshold"), "Risk threshold", minimum=0, maximum=100, default=int(config.get("threshold", 50)))
        elif rule.rule_type == "related_object_status":
            if "values" in config and payload.get("related_values") is not None:
                config["values"] = self._csv_values(payload.get("related_values"))
            if "lifecycle_values" in config and payload.get("lifecycle_values") is not None:
                config["lifecycle_values"] = self._csv_values(payload.get("lifecycle_values"))
        rule.severity = severity
        rule.config = config
        if "enabled" in payload:
            rule.enabled = self._bool(payload.get("enabled"))

    def _normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()
        rule_type = str(payload.get("rule_type", "")).strip()
        severity = str(payload.get("severity", "Medium")).strip()
        if not name:
            raise CustomRuleValidationError("Rule name is required")
        if len(name) > 180:
            raise CustomRuleValidationError("Rule name is too long")
        if rule_type not in SUPPORTED_RULE_TYPES:
            raise CustomRuleValidationError("Unsupported declarative rule type")
        if severity not in SEVERITIES:
            raise CustomRuleValidationError("Invalid severity")
        object_types = self._object_types(payload.get("object_types"))
        config: dict[str, Any] = {}
        if object_types:
            if len(object_types) == 1:
                config["object_type"] = object_types[0]
            else:
                config["object_types"] = object_types

        if rule_type == "missing_field":
            self._require_object_types(object_types)
            config["field"] = self._field_name(payload.get("field_name"), object_types)
        elif rule_type == "date_threshold":
            self._require_object_types(object_types)
            config["field"] = self._field_name(payload.get("field_name"), object_types)
            mode = str(payload.get("date_mode", "within")).strip()
            if mode not in DATE_MODES:
                raise CustomRuleValidationError("Invalid date threshold mode")
            config["mode"] = mode
            config["days"] = self._integer(payload.get("days"), "Days", minimum=0, default=0)
        elif rule_type in {"missing_relationship", "relationship_count"}:
            self._require_object_types(object_types)
            config.update(self._relationship_config(payload, object_types))
            if rule_type == "relationship_count":
                minimum = self._optional_integer(payload.get("min_count"), "Minimum count", minimum=0)
                maximum = self._optional_integer(payload.get("max_count"), "Maximum count", minimum=0)
                if minimum is None and maximum is None:
                    raise CustomRuleValidationError("Relationship count requires a minimum and/or maximum")
                if minimum is not None:
                    config["min"] = minimum
                if maximum is not None:
                    config["max"] = maximum
                if minimum is not None and maximum is not None and minimum > maximum:
                    raise CustomRuleValidationError("Minimum count cannot exceed maximum count")
        elif rule_type == "related_object_status":
            if len(object_types) != 1:
                raise CustomRuleValidationError("Related-object status rules require exactly one source object type")
            config["relationship"] = self._relationship_key(payload.get("relationship"))
            related_type = self._single_object_type(payload.get("related_type"), "Related object type")
            config["related_type"] = related_type
            self._validate_relationship_combination(object_types[0], config["relationship"], related_type)
            object_lifecycle = str(payload.get("object_lifecycle", "")).strip()
            if object_lifecycle:
                config["object_lifecycle"] = object_lifecycle
            property_name = str(payload.get("related_property", "")).strip()
            values = self._csv_values(payload.get("related_values"))
            lifecycle_values = self._csv_values(payload.get("lifecycle_values"))
            if property_name:
                self._validate_identifier(property_name, "Related property")
                self._field_name(property_name, [related_type])
                if not values:
                    raise CustomRuleValidationError("Related property values are required")
                config["property"] = property_name
                config["values"] = values
            if lifecycle_values:
                config["lifecycle_values"] = lifecycle_values
            if not property_name and not lifecycle_values:
                raise CustomRuleValidationError("Choose related property values and/or lifecycle values")
        elif rule_type == "risk_threshold":
            if len(object_types) != 1:
                raise CustomRuleValidationError("Risk threshold rules require exactly one object type")
            metric_type = str(payload.get("metric_type", "")).strip()
            if metric_type not in METRIC_TYPES:
                raise CustomRuleValidationError("Invalid metric type")
            config["metric_type"] = metric_type
            config["threshold"] = self._integer(payload.get("threshold"), "Risk threshold", minimum=0, maximum=100)
            criticality = str(payload.get("criticality", "")).strip()
            if criticality:
                config["criticality"] = criticality
        elif rule_type == "review_overdue":
            # Empty object scope means all object types, matching the built-in rule semantics.
            pass
        elif rule_type == "duplicate_name":
            self._require_object_types(object_types)

        return {
            "name": name,
            "description": description,
            "rule_type": rule_type,
            "severity": severity,
            "enabled": self._bool(payload.get("enabled", True)),
            "config": config,
        }

    def _relationship_config(
        self, payload: dict[str, Any], object_types: list[str]
    ) -> dict[str, Any]:
        direction = str(payload.get("direction", "outbound")).strip()
        if direction not in DIRECTIONS:
            raise CustomRuleValidationError("Invalid relationship direction")
        config: dict[str, Any] = {
            "relationship": self._relationship_key(payload.get("relationship")),
            "direction": direction,
        }
        source_type = str(payload.get("source_type", "")).strip()
        target_type = str(payload.get("target_type", "")).strip()
        if source_type:
            config["source_type"] = self._single_object_type(source_type, "Source type filter")
        if target_type:
            config["target_type"] = self._single_object_type(target_type, "Target type filter")
        if len(object_types) == 1:
            if direction == "outbound" and config.get("target_type"):
                self._validate_relationship_combination(
                    object_types[0], config["relationship"], str(config["target_type"])
                )
            if direction == "inbound" and config.get("source_type"):
                self._validate_relationship_combination(
                    str(config["source_type"]), config["relationship"], object_types[0]
                )
        return config

    def _object_types(self, raw: Any) -> list[str]:
        if raw is None:
            return []
        values = raw if isinstance(raw, (list, tuple)) else self._csv_values(raw)
        result: list[str] = []
        for value in values:
            key = str(value).strip()
            if not key:
                continue
            self._single_object_type(key, "Object type")
            if key not in result:
                result.append(key)
        return result

    def _single_object_type(self, value: Any, label: str) -> str:
        key = str(value or "").strip()
        if not key or self.db.scalar(select(ObjectType.id).where(ObjectType.key == key, ObjectType.is_active.is_(True))) is None:
            raise CustomRuleValidationError(f"{label} is invalid")
        return key

    def _relationship_key(self, value: Any) -> str:
        key = str(value or "").strip()
        if not key or self.db.scalar(select(RelationshipType.id).where(RelationshipType.key == key, RelationshipType.is_active.is_(True))) is None:
            raise CustomRuleValidationError("Relationship type is invalid")
        return key

    def _field_name(self, value: Any, object_types: list[str]) -> str:
        field = str(value or "").strip()
        self._validate_identifier(field, "Field/property")
        if field in UNIVERSAL_FIELDS:
            return field
        for key in object_types:
            obj_type = self.db.scalar(select(ObjectType).where(ObjectType.key == key))
            schema = obj_type.schema_definition if obj_type else {}
            if field not in schema:
                raise CustomRuleValidationError(
                    "Field/property is not defined for every selected object type"
                )
        return field


    def _validate_relationship_combination(
        self, source_type_key: str, relationship_key: str, target_type_key: str
    ) -> None:
        relationship = self.db.scalar(
            select(RelationshipType).where(RelationshipType.key == relationship_key)
        )
        source_type = self.db.scalar(select(ObjectType).where(ObjectType.key == source_type_key))
        target_type = self.db.scalar(select(ObjectType).where(ObjectType.key == target_type_key))
        if relationship is None or source_type is None or target_type is None:
            raise CustomRuleValidationError("Invalid relationship applicability")
        allowed = self.db.scalar(
            select(RelationshipRule.id).where(
                RelationshipRule.relationship_type_id == relationship.id,
                RelationshipRule.source_object_type_id == source_type.id,
                RelationshipRule.target_object_type_id == target_type.id,
            )
        )
        if allowed is None:
            raise CustomRuleValidationError(
                "Relationship is not valid for the selected source and related object types"
            )

    @staticmethod
    def _validate_identifier(value: str, label: str) -> None:
        if not value or not _IDENTIFIER_RE.match(value):
            raise CustomRuleValidationError(f"{label} must be a valid internal field name")

    @staticmethod
    def _require_object_types(values: list[str]) -> None:
        if not values:
            raise CustomRuleValidationError("Select at least one object type")

    @staticmethod
    def _csv_values(raw: Any) -> list[str]:
        return [value.strip() for value in str(raw or "").split(",") if value.strip()]

    @staticmethod
    def _bool(raw: Any) -> bool:
        if isinstance(raw, bool):
            return raw
        return str(raw or "").lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _integer(raw: Any, label: str, *, minimum: int | None = None, maximum: int | None = None, default: int | None = None) -> int:
        value = default if raw in (None, "") and default is not None else raw
        try:
            result = int(value)
        except (TypeError, ValueError) as exc:
            raise CustomRuleValidationError(f"{label} must be an integer") from exc
        if minimum is not None and result < minimum:
            raise CustomRuleValidationError(f"{label} must be at least {minimum}")
        if maximum is not None and result > maximum:
            raise CustomRuleValidationError(f"{label} must be no more than {maximum}")
        return result

    @classmethod
    def _optional_integer(cls, raw: Any, label: str, *, minimum: int | None = None) -> int | None:
        if raw in (None, ""):
            return None
        return cls._integer(raw, label, minimum=minimum)

    def _next_custom_rule_id(self) -> str:
        existing = self.db.scalars(select(RuleDefinition.rule_id).where(RuleDefinition.rule_id.like("CUSTOM-%"))).all()
        numbers = []
        for rule_id in existing:
            try:
                numbers.append(int(str(rule_id).split("-")[-1]))
            except ValueError:
                continue
        return f"CUSTOM-{max(numbers, default=0) + 1:04d}"

    @staticmethod
    def _state(rule: RuleDefinition) -> dict[str, Any]:
        return {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "severity": rule.severity,
            "config": dict(rule.config),
            "enabled": rule.enabled,
            "is_system": rule.is_system,
            "archived_at": rule.archived_at.isoformat() if rule.archived_at else None,
        }
