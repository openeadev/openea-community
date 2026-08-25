from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.metamodel.standard import STANDARD_OBJECT_TYPES, STANDARD_RELATIONSHIPS
from app.models.findings import RuleDefinition
from app.models.metamodel import (
    EnumerationDefinition,
    ObjectType,
    RelationshipRule,
    RelationshipType,
)
from app.services.metamodel_service import (
    MetamodelService,
    PropertyValidationError,
    RelationshipValidationError,
)
from app.services.seed_service import SystemSeedService


def test_system_seed_is_idempotent(db):
    service = SystemSeedService(db)
    first = service.seed()
    second = service.seed()

    assert first == second
    assert db.scalar(select(func.count()).select_from(ObjectType)) == 12
    assert db.scalar(select(func.count()).select_from(RelationshipType)) == len(STANDARD_RELATIONSHIPS)
    assert db.scalar(select(func.count()).select_from(RelationshipRule)) == sum(len(item["rules"]) for item in STANDARD_RELATIONSHIPS)
    assert db.scalar(select(func.count()).select_from(EnumerationDefinition)) >= 20


def test_all_twelve_standard_object_types_are_seeded(db):
    SystemSeedService(db).seed()
    keys = set(db.scalars(select(ObjectType.key)).all())
    assert keys == {str(item["key"]) for item in STANDARD_OBJECT_TYPES}


def test_application_properties_are_validated(db):
    SystemSeedService(db).seed()
    service = MetamodelService(db)
    values = service.validate_object_properties(
        "application",
        {
            "technical_fit": "Good",
            "internet_facing": True,
            "go_live_date": "2026-08-24",
            "rto_hours": 4,
        },
    )
    assert values["technical_fit"] == "Good"
    assert values["internet_facing"] is True
    assert values["go_live_date"] == "2026-08-24"
    assert values["rto_hours"] == "4"


def test_unknown_object_property_is_rejected(db):
    SystemSeedService(db).seed()
    service = MetamodelService(db)
    try:
        service.validate_object_properties("application", {"uncontrolled_json": "no"})
    except PropertyValidationError as exc:
        assert "Unknown properties" in str(exc)
    else:
        raise AssertionError("Unknown property was accepted")


def test_invalid_enumeration_value_is_rejected(db):
    SystemSeedService(db).seed()
    service = MetamodelService(db)
    try:
        service.validate_object_properties("technology", {"strategic_status": "Whatever"})
    except PropertyValidationError as exc:
        assert "must be one of" in str(exc)
    else:
        raise AssertionError("Invalid enumeration value was accepted")


def test_required_schema_property_is_enforced(db):
    SystemSeedService(db).seed()
    service = MetamodelService(db)
    try:
        service.validate_object_properties("architecture_decision", {"context": "Need a database"})
    except PropertyValidationError as exc:
        assert "decision" in str(exc)
    else:
        raise AssertionError("Missing required property was accepted")


def test_valid_relationship_rule_is_accepted(db):
    SystemSeedService(db).seed()
    relationship = MetamodelService(db).validate_relationship_rule(
        "supports", "application", "business_capability"
    )
    assert relationship.inverse_label == "supported by"


def test_invalid_relationship_direction_is_rejected(db):
    SystemSeedService(db).seed()
    try:
        MetamodelService(db).validate_relationship_rule(
            "supports", "business_capability", "application"
        )
    except RelationshipValidationError as exc:
        assert "not valid" in str(exc)
    else:
        raise AssertionError("Invalid relationship direction was accepted")


def test_integration_relationship_properties_are_governed(db):
    SystemSeedService(db).seed()
    service = MetamodelService(db)
    values = service.validate_relationship_properties(
        "integrates_with",
        {"protocol": "HTTPS", "criticality": "High", "direction": "Bidirectional"},
    )
    assert values["criticality"] == "High"


def test_system_seed_skips_finding_rules_before_phase10_table_exists(tmp_path):
    db_path = tmp_path / "phase3_seed_regression.db"
    engine = create_engine(f"sqlite+pysqlite:///{db_path}")
    phase3_table_names = {
        "enumeration_definitions",
        "enumeration_values",
        "object_types",
        "relationship_types",
        "relationship_rules",
    }
    tables = [
        table
        for table in Base.metadata.sorted_tables
        if table.name in phase3_table_names
    ]
    Base.metadata.create_all(engine, tables=tables)

    with Session(engine) as session:
        result = SystemSeedService(session).seed(include_finding_rules=False)
        assert result["object_types"] == 12
        assert result["finding_rules"] == 0
        assert not inspect(engine).has_table("rule_definitions")

    RuleDefinition.__table__.create(engine)
    with Session(engine) as session:
        result = SystemSeedService(session).seed()
        assert result["finding_rules"] > 0

    engine.dispose()
