import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, CONTRIBUTOR, VIEWER
from app.repositories.relationship_repository import RelationshipRepository
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService, RelationshipServiceError

PASSWORD = "ValidPassword123!"


def csrf_from(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match
    return match.group(1)


def create_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def login(client: TestClient, username: str) -> None:
    page = client.get("/login")
    response = client.post("/login", data={"username": username, "password": PASSWORD, "csrf_token": csrf_from(page.text), "next": "/explore"}, follow_redirects=False)
    assert response.status_code == 303


def make_object(db: Session, actor, type_key: str, name: str):
    return ObjectService(db).create_object(
        object_type_key=type_key, name=name, description="", record_status="Active",
        governance_status=None, lifecycle_stage=None, criticality=None,
        owner_organization_id=None, owner_role_id=None, source="Manual", confidence="High",
        valid_from=None, valid_until=None, aliases="", tags="", properties={}, actor=actor,
    )


def test_valid_relationship_is_stored_once_and_inverse_is_displayed(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "Customer Portal")
    capability = make_object(db, architect, "business_capability", "Customer Service")
    rel = RelationshipService(db).create_relationship(
        relationship_key="supports", source_object_id=app.id, target_object_id=capability.id,
        description="Primary support", criticality="High", confidence="Confirmed",
        source="Manual", actor=architect,
    )
    assert len(RelationshipRepository(db).list_for_object(app.id)) == 1
    assert len(RelationshipRepository(db).list_for_object(capability.id)) == 1
    assert rel.source_object_id == app.id
    assert rel.target_object_id == capability.id

    login(client, "architect")
    outbound = client.get(f"/explore/{app.id}?tab=relationships")
    inbound = client.get(f"/explore/{capability.id}?tab=relationships")
    assert "supports" in outbound.text and "Customer Service" in outbound.text
    assert "supported by" in inbound.text and "Customer Portal" in inbound.text


def test_invalid_source_target_combination_is_rejected(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "App")
    tech = make_object(db, architect, "technology", "PostgreSQL")
    with pytest.raises(RelationshipServiceError, match="not valid"):
        RelationshipService(db).create_relationship(
            relationship_key="supports", source_object_id=app.id, target_object_id=tech.id, actor=architect
        )


def test_duplicate_relationship_is_rejected(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "App")
    tech = make_object(db, architect, "technology", "PostgreSQL")
    service = RelationshipService(db)
    service.create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=architect)
    with pytest.raises(RelationshipServiceError, match="already exists"):
        service.create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=architect)


def test_relationship_metadata_can_be_edited_and_archived(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "App")
    tech = make_object(db, architect, "technology", "Java 21")
    service = RelationshipService(db)
    rel = service.create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=architect)
    service.update_relationship(rel, description="Runtime", criticality="High", confidence="Confirmed", valid_from="2026-01-01", valid_until=None, source="Manual", properties={}, actor=architect)
    assert rel.description == "Runtime" and rel.criticality == "High"
    service.archive_relationship(rel, actor=architect)
    assert RelationshipRepository(db).get_by_id(rel.id) is None
    assert RelationshipRepository(db).get_by_id(rel.id, include_archived=True) is not None


def test_integration_relationship_properties_are_validated(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    a = make_object(db, architect, "application", "App A")
    b = make_object(db, architect, "application", "App B")
    rel = RelationshipService(db).create_relationship(
        relationship_key="integrates_with", source_object_id=a.id, target_object_id=b.id,
        properties={"protocol": "HTTPS", "criticality": "High", "data_exchanged": "Customer"}, actor=architect,
    )
    assert rel.properties["protocol"] == "HTTPS"
    with pytest.raises(RelationshipServiceError):
        RelationshipService(db).create_relationship(
            relationship_key="integrates_with", source_object_id=b.id, target_object_id=a.id,
            properties={"unknown": "bad"}, actor=architect,
        )


def test_guided_creation_only_offers_valid_relationship_choices(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "App")
    make_object(db, architect, "business_capability", "Payments")
    make_object(db, architect, "technology", "PostgreSQL")
    login(client, "architect")
    page = client.get(f"/explore/{app.id}/relationships/new")
    assert page.status_code == 200
    assert "supports → Business Capability" in page.text
    assert "uses → Technology" in page.text
    assert "requires → Business Capability" not in page.text


def test_contributor_can_maintain_relationship_but_viewer_cannot(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    app = make_object(db, architect, "application", "App")
    make_object(db, architect, "technology", "PostgreSQL")
    create_user(db, "contributor", CONTRIBUTOR)
    login(client, "contributor")
    assert client.get(f"/explore/{app.id}/relationships/new").status_code == 200
    client.get("/logout")
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    assert client.get(f"/explore/{app.id}?tab=relationships").status_code == 200
    assert client.get(f"/explore/{app.id}/relationships/new").status_code == 403
