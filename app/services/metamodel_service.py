from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.metamodel import EnumerationDefinition, ObjectType, RelationshipType


class PropertyValidationError(ValueError):
    pass


class RelationshipValidationError(ValueError):
    pass


class MetamodelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_object_type(self, key: str) -> ObjectType | None:
        return self.db.scalar(select(ObjectType).where(ObjectType.key == key))

    def validate_object_properties(self, object_type_key: str, properties: dict[str, object]) -> dict[str, object]:
        object_type = self.get_object_type(object_type_key)
        if object_type is None or not object_type.is_active:
            raise PropertyValidationError(f"Unknown object type: {object_type_key}")
        return self._validate_properties(object_type.schema_definition, properties)

    def validate_relationship_properties(self, relationship_key: str, properties: dict[str, object]) -> dict[str, object]:
        relationship_type = self.db.scalar(select(RelationshipType).where(RelationshipType.key == relationship_key))
        if relationship_type is None or not relationship_type.is_active:
            raise PropertyValidationError(f"Unknown relationship type: {relationship_key}")
        return self._validate_properties(relationship_type.properties_schema, properties)

    def validate_relationship_rule(self, relationship_key: str, source_type_key: str, target_type_key: str) -> RelationshipType:
        relationship_type = self.db.scalar(
            select(RelationshipType)
            .options(selectinload(RelationshipType.rules))
            .where(RelationshipType.key == relationship_key, RelationshipType.is_active.is_(True))
        )
        if relationship_type is None:
            raise RelationshipValidationError(f"Unknown relationship type: {relationship_key}")
        source = self.get_object_type(source_type_key)
        target = self.get_object_type(target_type_key)
        if source is None or target is None:
            raise RelationshipValidationError("Unknown source or target object type")
        valid = any(
            rule.source_object_type_id == source.id and rule.target_object_type_id == target.id
            for rule in relationship_type.rules
        )
        if not valid:
            raise RelationshipValidationError(
                f"{relationship_type.name} is not valid from {source.name} to {target.name}"
            )
        return relationship_type

    def _validate_properties(self, schema: dict[str, object], properties: dict[str, object]) -> dict[str, object]:
        if not isinstance(properties, dict):
            raise PropertyValidationError("Properties must be an object")
        unknown = sorted(set(properties) - set(schema))
        if unknown:
            raise PropertyValidationError(f"Unknown properties: {', '.join(unknown)}")
        missing = [name for name, spec in schema.items() if isinstance(spec, dict) and spec.get("required") and (name not in properties or properties[name] in (None, ""))]
        if missing:
            raise PropertyValidationError(f"Missing required properties: {', '.join(sorted(missing))}")
        validated: dict[str, object] = {}
        for name, value in properties.items():
            if value is None:
                validated[name] = None
                continue
            spec = schema[name]
            if not isinstance(spec, dict):
                raise PropertyValidationError(f"Invalid schema definition for {name}")
            validated[name] = self._validate_value(name, value, spec)
        return validated

    def _validate_value(self, name: str, value: object, spec: dict[str, object]) -> object:
        kind = spec.get("type")
        if kind in {"text", "long_text"}:
            if not isinstance(value, str):
                raise PropertyValidationError(f"{name} must be text")
            return value
        if kind == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                raise PropertyValidationError(f"{name} must be an integer")
            return value
        if kind == "decimal":
            if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
                raise PropertyValidationError(f"{name} must be a decimal")
            try:
                return str(Decimal(str(value)))
            except InvalidOperation as exc:
                raise PropertyValidationError(f"{name} must be a decimal") from exc
        if kind == "boolean":
            if not isinstance(value, bool):
                raise PropertyValidationError(f"{name} must be a boolean")
            return value
        if kind == "date":
            if isinstance(value, date) and not isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, str):
                try:
                    return date.fromisoformat(value).isoformat()
                except ValueError as exc:
                    raise PropertyValidationError(f"{name} must be an ISO date") from exc
            raise PropertyValidationError(f"{name} must be an ISO date")
        if kind == "datetime":
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
                except ValueError as exc:
                    raise PropertyValidationError(f"{name} must be an ISO date/time") from exc
            raise PropertyValidationError(f"{name} must be an ISO date/time")
        if kind == "url":
            if not isinstance(value, str) or urlparse(value).scheme not in {"http", "https"}:
                raise PropertyValidationError(f"{name} must be an HTTP(S) URL")
            return value
        if kind == "select":
            if not isinstance(value, str):
                raise PropertyValidationError(f"{name} must be a string selection")
            enum_key = spec.get("enum")
            allowed = self._enumeration_values(str(enum_key))
            if value not in allowed:
                raise PropertyValidationError(f"{name} must be one of: {', '.join(allowed)}")
            return value
        if kind == "multi_select":
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise PropertyValidationError(f"{name} must be a list of selections")
            allowed = set(self._enumeration_values(str(spec.get("enum"))))
            if any(item not in allowed for item in value):
                raise PropertyValidationError(f"{name} contains an invalid selection")
            return value
        if kind == "object_reference":
            if not isinstance(value, str):
                raise PropertyValidationError(f"{name} must be an object UUID")
            try:
                UUID(value)
            except ValueError as exc:
                raise PropertyValidationError(f"{name} must be an object UUID") from exc
            return value
        raise PropertyValidationError(f"Unsupported property type for {name}: {kind}")

    def _enumeration_values(self, key: str) -> list[str]:
        definition = self.db.scalar(
            select(EnumerationDefinition)
            .options(selectinload(EnumerationDefinition.values))
            .where(EnumerationDefinition.key == key)
        )
        if definition is None:
            raise PropertyValidationError(f"Unknown enumeration: {key}")
        return [item.value for item in sorted(definition.values, key=lambda item: item.sort_order) if item.is_active]
