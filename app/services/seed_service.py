import uuid

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.findings_rules import STANDARD_FINDING_RULES
from app.metamodel.standard import (
    STANDARD_ENUMERATIONS,
    STANDARD_OBJECT_TYPES,
    STANDARD_RELATIONSHIPS,
)
from app.models.findings import RuleDefinition
from app.models.metamodel import (
    EnumerationDefinition,
    EnumerationValue,
    ObjectType,
    RelationshipRule,
    RelationshipType,
)

SEED_NAMESPACE = uuid.UUID("8c697f19-c128-4fd3-9ed7-b967289f1d88")


def stable_id(kind: str, key: str) -> str:
    return str(uuid.uuid5(SEED_NAMESPACE, f"{kind}:{key}"))


class SystemSeedService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def seed(
        self, *, commit: bool = True, include_finding_rules: bool = True
    ) -> dict[str, int]:
        self._seed_enumerations()
        object_types = self._seed_object_types()
        self._seed_relationships(object_types)
        finding_rules_seeded = 0
        bind = self.db.get_bind()
        if include_finding_rules and inspect(bind).has_table("rule_definitions"):
            self._seed_finding_rules()
            finding_rules_seeded = len(STANDARD_FINDING_RULES)
        if commit:
            self.db.commit()
        else:
            self.db.flush()
        return {
            "object_types": len(STANDARD_OBJECT_TYPES),
            "relationship_types": len(STANDARD_RELATIONSHIPS),
            "relationship_rules": sum(len(item["rules"]) for item in STANDARD_RELATIONSHIPS),
            "enumerations": len(STANDARD_ENUMERATIONS),
            "finding_rules": finding_rules_seeded,
        }

    def _seed_enumerations(self) -> None:
        for enum_key, (label, values) in STANDARD_ENUMERATIONS.items():
            definition = self.db.scalar(select(EnumerationDefinition).where(EnumerationDefinition.key == enum_key))
            if definition is None:
                definition = EnumerationDefinition(id=stable_id("enum", enum_key), key=enum_key, label=label, description="OpenEA standard enumeration", is_system=True)
                self.db.add(definition)
                self.db.flush()
            else:
                definition.label = label
                definition.is_system = True
            existing = {value.value: value for value in definition.values}
            for index, value in enumerate(values):
                row = existing.get(value)
                if row is None:
                    self.db.add(EnumerationValue(id=stable_id("enum_value", f"{enum_key}:{value}"), enumeration_id=definition.id, value=value, label=value, sort_order=index, is_active=True))
                else:
                    row.label = value
                    row.sort_order = index
                    row.is_active = True

    def _seed_object_types(self) -> dict[str, ObjectType]:
        result: dict[str, ObjectType] = {}
        for item in STANDARD_OBJECT_TYPES:
            key = str(item["key"])
            row = self.db.scalar(select(ObjectType).where(ObjectType.key == key))
            if row is None:
                row = ObjectType(id=stable_id("object_type", key), key=key, name=str(item["name"]), domain=str(item["domain"]), description=str(item["description"]), schema_definition=dict(item["schema"]), is_system=True, is_active=True)
                self.db.add(row)
                self.db.flush()
            else:
                row.name = str(item["name"])
                row.domain = str(item["domain"])
                row.description = str(item["description"])
                row.schema_definition = dict(item["schema"])
                row.is_system = True
                row.is_active = True
            result[key] = row
        return result

    def _seed_relationships(self, object_types: dict[str, ObjectType]) -> None:
        for item in STANDARD_RELATIONSHIPS:
            key = str(item["key"])
            row = self.db.scalar(select(RelationshipType).where(RelationshipType.key == key))
            if row is None:
                row = RelationshipType(id=stable_id("relationship_type", key), key=key, name=str(item["name"]), inverse_label=str(item["inverse"]), description=f"OpenEA standard relationship: {item['name']}", properties_schema=dict(item.get("properties", {})), is_system=True, is_active=True)
                self.db.add(row)
                self.db.flush()
            else:
                row.name = str(item["name"])
                row.inverse_label = str(item["inverse"])
                row.properties_schema = dict(item.get("properties", {}))
                row.is_system = True
                row.is_active = True
            existing = {(rule.source_object_type_id, rule.target_object_type_id) for rule in row.rules}
            for source_key, target_key in item["rules"]:
                source_id = object_types[source_key].id
                target_id = object_types[target_key].id
                if (source_id, target_id) not in existing:
                    self.db.add(RelationshipRule(id=stable_id("relationship_rule", f"{key}:{source_key}:{target_key}"), relationship_type_id=row.id, source_object_type_id=source_id, target_object_type_id=target_id))

    def _seed_finding_rules(self) -> None:
        for item in STANDARD_FINDING_RULES:
            row = self.db.scalar(select(RuleDefinition).where(RuleDefinition.rule_id == item["rule_id"]))
            if row is None:
                row = RuleDefinition(
                    id=stable_id("finding_rule", str(item["rule_id"])),
                    rule_id=str(item["rule_id"]),
                    name=str(item["name"]),
                    description=str(item["description"]),
                    rule_type=str(item["rule_type"]),
                    severity=str(item["severity"]),
                    config=dict(item["config"]),
                    enabled=True,
                    is_system=True,
                )
                self.db.add(row)
                row.is_system = True
