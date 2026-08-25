from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT
from app.models.governance import AuditEvent
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship, ObjectAlias
from app.services.auth_service import AuthenticationService
from app.services.import_service import RelationshipImportService

PASSWORD = "ValidPassword123!"


def user(db: Session):
    return AuthenticationService(db).create_user("relimport", "Relationship Import", PASSWORD, {ARCHITECT})


def obj(db: Session, type_key: str, name: str, *, alias: str | None = None, external_id: str | None = None) -> ArchitectureObject:
    from app.repositories.object_repository import ObjectRepository

    object_type = ObjectRepository(db).get_type_by_key(type_key)
    assert object_type is not None
    row = ArchitectureObject(
        object_type_id=object_type.id,
        name=name,
        description="",
        record_status="Active",
        properties={"external_id": external_id} if external_id else {},
    )
    db.add(row)
    db.flush()
    if alias:
        db.add(ObjectAlias(object_id=row.id, alias=alias))
    db.commit()
    db.refresh(row)
    return row


def test_relationship_csv_import_by_name_preview_commit_and_update(db: Session) -> None:
    actor = user(db)
    app = obj(db, "application", "Payments Portal")
    tech = obj(db, "technology", "Python 3.12")
    service = RelationshipImportService(db)
    content = (
        b"source_type,source_name,relationship_type,target_type,target_name,criticality,confidence\n"
        b"Application,Payments Portal,uses,Technology,Python 3.12,High,Confirmed\n"
    )
    batch = service.create_batch(filename="relationships.csv", content=content, actor=actor)
    preview = service.validate(batch, batch.mapping)
    assert preview["counts"]["New"] == 1
    result = service.commit(batch, actor=actor)
    assert result == {"created": 1, "updated": 0, "unchanged": 0}
    rel = db.scalar(select(ArchitectureRelationship).where(ArchitectureRelationship.source_object_id == app.id))
    assert rel is not None
    assert rel.target_object_id == tech.id
    assert rel.relationship_type.key == "uses"
    assert rel.criticality == "High"
    assert rel.confidence == "Confirmed"
    audit = list(db.scalars(select(AuditEvent).where(AuditEvent.entity_id == rel.id)).all())
    assert any(event.source == "CSV Import" and event.correlation_id == f"relationship-csv-import:{batch.id}" for event in audit)

    update = service.create_batch(
        filename="relationships-update.csv",
        content=(
            b"source_type,source_name,relationship_type,target_type,target_name,criticality,confidence\n"
            b"application,Payments Portal,uses,technology,Python 3.12,Mission Critical,High\n"
        ),
        actor=actor,
    )
    update_preview = service.validate(update, update.mapping)
    assert update_preview["counts"]["Update"] == 1
    service.commit(update, actor=actor)
    db.refresh(rel)
    assert rel.criticality == "Mission Critical"
    assert rel.confidence == "High"


def test_relationship_import_resolves_external_id_then_alias(db: Session) -> None:
    actor = user(db)
    app = obj(db, "application", "Customer Portal", external_id="APP-100")
    tech = obj(db, "technology", "PostgreSQL 17", alias="PG17")
    service = RelationshipImportService(db)
    content = (
        b"source_type,source_external_id,relationship_type,target_type,target_name\n"
        b"application,APP-100,uses,technology,PG17\n"
    )
    batch = service.create_batch(filename="resolution.csv", content=content, actor=actor)
    preview = service.validate(batch, batch.mapping)
    assert preview["counts"]["New"] == 1
    row = preview["rows"][0]
    assert row["values"]["source_object_id"] == app.id
    assert row["values"]["target_object_id"] == tech.id
    assert any("external ID" in warning for warning in row["warnings"])
    assert any("alias" in warning for warning in row["warnings"])


def test_relationship_import_rejects_invalid_metamodel_combination(db: Session) -> None:
    actor = user(db)
    obj(db, "technology", "Java 21")
    obj(db, "business_capability", "Customer Service")
    service = RelationshipImportService(db)
    batch = service.create_batch(
        filename="invalid.csv",
        content=(
            b"source_type,source_name,relationship_type,target_type,target_name\n"
            b"technology,Java 21,supports,business_capability,Customer Service\n"
        ),
        actor=actor,
    )
    preview = service.validate(batch, batch.mapping)
    assert preview["counts"]["Error"] == 1
    assert "not valid" in "; ".join(preview["rows"][0]["errors"])


def test_relationship_import_ambiguous_name_stops_preview(db: Session) -> None:
    actor = user(db)
    obj(db, "application", "Shared Name")
    obj(db, "application", "Shared Name")
    obj(db, "technology", "Go 1.24")
    service = RelationshipImportService(db)
    batch = service.create_batch(
        filename="ambiguous.csv",
        content=(
            b"source_type,source_name,relationship_type,target_type,target_name\n"
            b"application,Shared Name,uses,technology,Go 1.24\n"
        ),
        actor=actor,
    )
    preview = service.validate(batch, batch.mapping)
    assert preview["counts"]["Error"] == 1
    assert "Ambiguous" in "; ".join(preview["rows"][0]["errors"])
