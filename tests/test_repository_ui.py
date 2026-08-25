import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, CONTRIBUTOR, VIEWER
from app.models.metamodel import ArchitectureObject
from app.repositories.object_repository import ObjectRepository
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService, ObjectValidationError

PASSWORD = "ValidPassword123!"


def csrf_from(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match
    return match.group(1)


def create_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def login(client: TestClient, username: str) -> None:
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


def minimal_properties(type_key: str) -> dict[str, object]:
    if type_key == "architecture_principle":
        return {"statement": "Architecture should prefer open standards."}
    if type_key == "architecture_decision":
        return {"context": "A decision is required.", "decision": "Use the selected platform."}
    return {}


def test_architect_can_create_every_standard_object_type(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    service = ObjectService(db)
    for object_type in ObjectRepository(db).list_object_types():
        obj = service.create_object(
            object_type_key=object_type.key,
            name=f"Test {object_type.name}",
            description="Phase 4 repository test",
            record_status="Draft",
            governance_status=None,
            lifecycle_stage=None,
            criticality=None,
            owner_organization_id=None,
            owner_role_id=None,
            source="Manual",
            confidence="Confirmed",
            valid_from=None,
            valid_until=None,
            aliases="",
            tags="phase4, test",
            properties=minimal_properties(object_type.key),
            actor=architect,
        )
        assert obj.id
        assert obj.object_type.key == object_type.key

    assert len(ObjectRepository(db).list_objects()) == 12


def test_application_form_renders_schema_and_persists_validated_properties(
    client: TestClient, db: Session
) -> None:
    create_user(db, "architect", ARCHITECT)
    login(client, "architect")
    page = client.get("/explore/new/application")
    assert page.status_code == 200
    assert "Technical Fit" in page.text
    assert "Internet Facing" in page.text

    response = client.post(
        "/explore/new/application",
        data={
            "csrf_token": csrf_from(page.text),
            "name": "Customer Portal",
            "description": "Digital customer application",
            "record_status": "Active",
            "lifecycle_stage": "Active",
            "criticality": "Mission Critical",
            "source": "Manual",
            "confidence": "Confirmed",
            "aliases": "Portal, Customer Web",
            "tags": "digital, customer",
            "prop__technical_fit": "Good",
            "prop__internet_facing": "true",
            "prop__rto_hours": "4",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    obj = db.scalar(select(ArchitectureObject).where(ArchitectureObject.name == "Customer Portal"))
    assert obj is not None
    assert obj.lifecycle_stage == "Active"
    assert obj.properties["technical_fit"] == "Good"
    assert obj.properties["internet_facing"] is True
    assert obj.properties["rto_hours"] == "4"


def test_invalid_dynamic_value_rejected_server_side(client: TestClient, db: Session) -> None:
    create_user(db, "architect", ARCHITECT)
    login(client, "architect")
    page = client.get("/explore/new/application")
    response = client.post(
        "/explore/new/application",
        data={
            "csrf_token": csrf_from(page.text),
            "name": "Bad Application",
            "record_status": "Active",
            "prop__technical_fit": "Perfect",
        },
    )
    assert response.status_code == 400
    assert "technical_fit must be one of" in response.text


def test_required_schema_property_is_enforced(client: TestClient, db: Session) -> None:
    create_user(db, "architect", ARCHITECT)
    login(client, "architect")
    page = client.get("/explore/new/architecture_principle")
    response = client.post(
        "/explore/new/architecture_principle",
        data={"csrf_token": csrf_from(page.text), "name": "Open Standards", "record_status": "Draft"},
    )
    assert response.status_code == 400
    assert "Missing required properties: statement" in response.text


def test_archived_object_disappears_from_normal_explore(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    obj = ObjectService(db).create_object(
        object_type_key="technology",
        name="Legacy Runtime",
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage="Aging",
        criticality="High",
        owner_organization_id=None,
        owner_role_id=None,
        source="Manual",
        confidence="High",
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="legacy",
        properties={},
        actor=architect,
    )
    login(client, "architect")
    detail = client.get(f"/explore/{obj.id}")
    token = csrf_from(detail.text)
    archived = client.post(
        f"/explore/{obj.id}/archive", data={"csrf_token": token}, follow_redirects=False
    )
    assert archived.status_code == 303
    assert ObjectRepository(db).get_by_id(obj.id) is None
    assert ObjectRepository(db).get_by_id(obj.id, include_archived=True) is not None
    page = client.get("/explore")
    assert "Legacy Runtime" not in page.text


def test_viewer_is_read_only(client: TestClient, db: Session) -> None:
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    assert client.get("/explore").status_code == 200
    assert client.get("/explore/new").status_code == 403


def test_contributor_can_edit_but_cannot_create_or_archive(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    obj = ObjectService(db).create_object(
        object_type_key="application",
        name="Operations App",
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage="Active",
        criticality="Medium",
        owner_organization_id=None,
        owner_role_id=None,
        source="Manual",
        confidence="Medium",
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="",
        properties={},
        actor=architect,
    )
    create_user(db, "contributor", CONTRIBUTOR)
    login(client, "contributor")
    assert client.get("/explore/new").status_code == 403
    edit_page = client.get(f"/explore/{obj.id}/edit")
    assert edit_page.status_code == 200
    response = client.post(
        f"/explore/{obj.id}/edit",
        data={
            "csrf_token": csrf_from(edit_page.text),
            "name": "Operations Application",
            "record_status": "Active",
            "lifecycle_stage": "Active",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    db.refresh(obj)
    assert obj.name == "Operations Application"
    detail = client.get(f"/explore/{obj.id}")
    archive = client.post(
        f"/explore/{obj.id}/archive",
        data={"csrf_token": csrf_from(detail.text)},
    )
    assert archive.status_code == 403


def test_filters_and_sorting_combine(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    service = ObjectService(db)
    for name, criticality, tags in [
        ("Zulu App", "High", "digital"),
        ("Alpha App", "High", "digital"),
        ("Medium App", "Medium", "digital"),
    ]:
        service.create_object(
            object_type_key="application",
            name=name,
            description="",
            record_status="Active",
            governance_status=None,
            lifecycle_stage="Active",
            criticality=criticality,
            owner_organization_id=None,
            owner_role_id=None,
            source="Manual",
            confidence="High",
            valid_from=None,
            valid_until=None,
            aliases="",
            tags=tags,
            properties={},
            actor=architect,
        )
    results = ObjectRepository(db).list_objects(
        object_type_key="application",
        record_status="Active",
        criticality="High",
        tag="digital",
        sort="name",
        direction="asc",
    )
    assert [item.name for item in results] == ["Alpha App", "Zulu App"]


def test_invalid_owner_reference_type_is_rejected(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    service = ObjectService(db)
    app = service.create_object(
        object_type_key="application",
        name="Not an Organization",
        description="",
        record_status="Draft",
        governance_status=None,
        lifecycle_stage=None,
        criticality=None,
        owner_organization_id=None,
        owner_role_id=None,
        source=None,
        confidence=None,
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="",
        properties={},
        actor=architect,
    )
    with pytest.raises(ObjectValidationError, match="Owner organization is invalid"):
        service.create_object(
            object_type_key="technology",
            name="Bad Owner",
            description="",
            record_status="Draft",
            governance_status=None,
            lifecycle_stage=None,
            criticality=None,
            owner_organization_id=app.id,
            owner_role_id=None,
            source=None,
            confidence=None,
            valid_from=None,
            valid_until=None,
            aliases="",
            tags="",
            properties={},
            actor=architect,
        )
