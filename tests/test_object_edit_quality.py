import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT
from app.models.metamodel import ArchitectureObject, ObjectAlias
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService

PASSWORD = "ValidPassword123!"


def csrf_from(text: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', text)
    assert match
    return match.group(1)


def create_user(db: Session, username: str):
    return AuthenticationService(db).create_user(
        username, username.title(), PASSWORD, {ARCHITECT}
    )


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


def create_organization(db: Session, actor, name: str) -> ArchitectureObject:
    return ObjectService(db).create_object(
        object_type_key="organization",
        name=name,
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage=None,
        criticality=None,
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


def test_role_edit_preserves_alias_and_allows_independent_organizations(
    client: TestClient, db: Session
) -> None:
    architect = create_user(db, "architect")
    gis = create_organization(db, architect, "GIS")
    enterprise_architecture = create_organization(db, architect, "Enterprise Architecture")

    role = ObjectService(db).create_object(
        object_type_key="role",
        name="Chief Security Officer",
        description="Security leadership role",
        record_status="Active",
        governance_status=None,
        lifecycle_stage=None,
        criticality="High",
        owner_organization_id=gis.id,
        owner_role_id=None,
        source="Manual",
        confidence="High",
        valid_from=None,
        valid_until=None,
        aliases="gis-security",
        tags="",
        properties={
            "role_type": "Security",
            "organization": gis.id,
            "responsibilities": "Security governance",
        },
        actor=architect,
    )

    login(client, "architect")
    page = client.get(f"/explore/{role.id}/edit")
    assert page.status_code == 200
    assert "Role organization" in page.text
    assert "repository Owner organization" in page.text

    response = client.post(
        f"/explore/{role.id}/edit",
        data={
            "csrf_token": csrf_from(page.text),
            "name": "Chief Security Officer",
            "description": "Security leadership role",
            "record_status": "Active",
            "criticality": "High",
            "owner_organization_id": enterprise_architecture.id,
            "source": "Manual",
            "confidence": "High",
            "aliases": "gis-security, GIS-SECURITY, gis-security",
            "tags": "",
            "prop__role_type": "Security",
            "prop__organization": gis.id,
            "prop__responsibilities": "Security governance",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    db.expire_all()
    updated = db.scalar(select(ArchitectureObject).where(ArchitectureObject.id == role.id))
    assert updated is not None
    assert updated.owner_organization_id == enterprise_architecture.id
    assert updated.properties["organization"] == gis.id

    aliases = list(
        db.scalars(select(ObjectAlias).where(ObjectAlias.object_id == role.id)).all()
    )
    assert len(aliases) == 1
    assert aliases[0].alias == "gis-security"

    detail = client.get(f"/explore/{role.id}")
    assert detail.status_code == 200
    assert "Role Organization" in detail.text
    assert ">GIS<" in detail.text
    assert gis.id not in detail.text


def test_role_edit_can_keep_same_owner_and_role_organization(
    client: TestClient, db: Session
) -> None:
    architect = create_user(db, "architect")
    gis = create_organization(db, architect, "GIS")
    role = ObjectService(db).create_object(
        object_type_key="role",
        name="Security Architect",
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage=None,
        criticality=None,
        owner_organization_id=gis.id,
        owner_role_id=None,
        source="Manual",
        confidence="High",
        valid_from=None,
        valid_until=None,
        aliases="security-architect",
        tags="",
        properties={"organization": gis.id},
        actor=architect,
    )

    login(client, "architect")
    page = client.get(f"/explore/{role.id}/edit")
    response = client.post(
        f"/explore/{role.id}/edit",
        data={
            "csrf_token": csrf_from(page.text),
            "name": "Security Architect",
            "record_status": "Active",
            "owner_organization_id": gis.id,
            "source": "Manual",
            "confidence": "High",
            "aliases": "security-architect",
            "prop__organization": gis.id,
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
