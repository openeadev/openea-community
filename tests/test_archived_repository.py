import re

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT
from app.repositories.relationship_repository import RelationshipRepository
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService
from app.services.search_service import SearchService

PASSWORD = "ValidPassword123!"


def csrf_from(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match
    return match.group(1)


def create_user(db: Session, username: str = "architect"):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {ARCHITECT})


def login(client: TestClient, username: str = "architect") -> None:
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": PASSWORD,
            "csrf_token": csrf_from(page.text),
            "next": "/explore",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303


def make_object(db: Session, actor, object_type_key: str, name: str, *, record_status: str = "Active"):
    lifecycle = "Active" if object_type_key == "application" else None
    return ObjectService(db).create_object(
        object_type_key=object_type_key,
        name=name,
        description="Archive behavior test",
        record_status=record_status,
        governance_status=None,
        lifecycle_stage=lifecycle,
        criticality="Medium",
        owner_organization_id=None,
        owner_role_id=None,
        source="Manual",
        confidence="High",
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="",
        properties={},
        actor=actor,
    )


def test_search_can_select_current_archived_or_all_records(db: Session) -> None:
    architect = create_user(db)
    current = make_object(db, architect, "business_process", "Current Process")
    archived = make_object(db, architect, "business_process", "Archived Process")
    ObjectService(db).archive_object(archived, actor=architect)

    service = SearchService(db)
    assert [item.id for item in service.search(object_type_key="business_process").items] == [current.id]
    assert [item.id for item in service.search(object_type_key="business_process", archive_scope="archived").items] == [archived.id]
    assert {item.id for item in service.search(object_type_key="business_process", archive_scope="all").items} == {
        current.id,
        archived.id,
    }
    assert [item.id for item in service.search(record_status="Archived").items] == [archived.id]


def test_explore_archived_filter_and_direct_archived_record_view(client: TestClient, db: Session) -> None:
    architect = create_user(db)
    archived = make_object(db, architect, "business_process", "Retired Payment Process")
    ObjectService(db).archive_object(archived, actor=architect)
    login(client)

    normal = client.get("/explore")
    assert "Retired Payment Process" not in normal.text
    assert "All current records" in normal.text
    assert ">Archived</option>" in normal.text
    assert ">All records</option>" in normal.text

    archived_results = client.get("/explore", params={"record_status": "Archived"})
    assert archived_results.status_code == 200
    assert "Retired Payment Process" in archived_results.text
    assert "Archived" in archived_results.text
    assert "table-secondary" not in archived_results.text

    detail = client.get(f"/explore/{archived.id}")
    assert detail.status_code == 200
    assert "Archived record." in detail.text
    assert "Restore" in detail.text
    assert "Analyze Impact" not in detail.text
    assert "View Metrics" not in detail.text


def test_archived_related_objects_are_hidden_by_default_and_theme_neutral(client: TestClient, db: Session) -> None:
    architect = create_user(db)
    application = make_object(db, architect, "application", "Digital Banking")
    current_process = make_object(db, architect, "business_process", "Process Payments")
    archived_process = make_object(db, architect, "business_process", "Legacy Payment Process")

    relationships = RelationshipService(db)
    relationships.create_relationship(
        relationship_key="supports",
        source_object_id=application.id,
        target_object_id=current_process.id,
        actor=architect,
    )
    relationships.create_relationship(
        relationship_key="supports",
        source_object_id=application.id,
        target_object_id=archived_process.id,
        actor=architect,
    )
    ObjectService(db).archive_object(archived_process, actor=architect)
    login(client)

    page = client.get(f"/explore/{application.id}", params={"tab": "relationships"})
    assert page.status_code == 200
    assert "Process Payments" in page.text
    assert "Legacy Payment Process" not in page.text
    assert "Show archived" in page.text

    shown = client.get(
        f"/explore/{application.id}",
        params={"tab": "relationships", "show_archived_related": "true"},
    )
    assert shown.status_code == 200
    assert "Process Payments" in shown.text
    assert "Legacy Payment Process" in shown.text
    assert "Hide archived" in shown.text
    assert ">Archived</span>" in shown.text
    assert "table-secondary" not in shown.text
    assert "text-decoration-line-through" not in shown.text

    current_relationships = RelationshipRepository(db).list_for_object(
        application.id, include_archived_related=False
    )
    assert len(current_relationships) == 1
    assert current_relationships[0].target_object_id == current_process.id


def test_show_archived_also_reveals_archived_relationship_records(client: TestClient, db: Session) -> None:
    architect = create_user(db)
    application = make_object(db, architect, "application", "Payments Hub")
    process = make_object(db, architect, "business_process", "Settle Payments")
    service = RelationshipService(db)
    relationship = service.create_relationship(
        relationship_key="supports",
        source_object_id=application.id,
        target_object_id=process.id,
        actor=architect,
    )
    service.archive_relationship(relationship, actor=architect)
    login(client)

    page = client.get(f"/explore/{application.id}", params={"tab": "relationships"})
    assert page.status_code == 200
    assert "Settle Payments" not in page.text
    assert "Show archived" in page.text

    shown = client.get(
        f"/explore/{application.id}",
        params={"tab": "relationships", "show_archived_related": "true"},
    )
    assert shown.status_code == 200
    assert "Settle Payments" in shown.text
    assert ">Archived</span>" in shown.text
    assert "table-secondary" not in shown.text

    archived_relationships = RelationshipRepository(db).list_for_object(
        application.id,
        include_archived_related=True,
        include_archived_relationships=True,
    )
    assert [item.id for item in archived_relationships] == [relationship.id]


def test_restore_preserves_relationships_and_previous_status(client: TestClient, db: Session) -> None:
    architect = create_user(db)
    application = make_object(db, architect, "application", "Payments Hub")
    process = make_object(db, architect, "business_process", "Settle Payment", record_status="Inactive")
    relationship = RelationshipService(db).create_relationship(
        relationship_key="supports",
        source_object_id=application.id,
        target_object_id=process.id,
        actor=architect,
    )
    ObjectService(db).archive_object(process, actor=architect)
    login(client)

    detail = client.get(f"/explore/{process.id}")
    response = client.post(
        f"/explore/{process.id}/restore",
        data={"csrf_token": csrf_from(detail.text)},
        follow_redirects=False,
    )
    assert response.status_code == 303
    db.refresh(process)
    assert process.archived_at is None
    assert process.record_status == "Inactive"

    restored_relationship = RelationshipRepository(db).get_by_id(relationship.id)
    assert restored_relationship is not None
    assert restored_relationship.target_object_id == process.id

    current_results = SearchService(db).search(query="Settle Payment")
    assert [item.id for item in current_results.items] == [process.id]
