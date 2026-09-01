import re

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, VIEWER
from app.models.imports import ImportBatch
from app.models.metamodel import ArchitectureObject
from app.services.auth_service import AuthenticationService
from app.services.demo_service import DEMO_TAG, DemoDataService
from app.services.import_service import ImportService

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
        data={"username": username, "password": PASSWORD, "csrf_token": csrf_from(page.text), "next": "/dashboard"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_api_v1_object_create_search_and_get(client: TestClient, db: Session) -> None:
    create_user(db, "architect", ARCHITECT)
    login(client, "architect")
    created = client.post(
        "/api/v1/objects",
        json={
            "object_type_key": "application",
            "name": "Phase 12 API Application",
            "record_status": "Active",
            "lifecycle_stage": "Active",
            "criticality": "High",
            "source": "Manual",
            "confidence": "High",
            "properties": {"technical_fit": "Good", "internet_facing": False},
            "tags": ["api", "phase12"],
        },
    )
    assert created.status_code == 201
    object_id = created.json()["id"]
    fetched = client.get(f"/api/v1/objects/{object_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Phase 12 API Application"
    search = client.get("/api/v1/search", params={"q": "Phase 12 API"})
    assert search.status_code == 200
    assert any(item["id"] == object_id for item in search.json()["items"])


def test_api_v1_viewer_cannot_write(client: TestClient, db: Session) -> None:
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    assert client.get("/api/v1/objects").status_code == 200
    response = client.post("/api/v1/objects", json={"object_type_key": "application", "name": "Forbidden"})
    assert response.status_code == 403


def test_csv_import_preview_commit_update_and_export(client: TestClient, db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    service = ImportService(db)
    csv_content = b"name,record_status,criticality,technical_fit,internet_facing\nImported App,Active,High,Good,true\n"
    batch = service.create_batch(object_type_key="application", filename="applications.csv", content=csv_content, actor=architect)
    assert isinstance(batch, ImportBatch)
    preview = service.validate(
        batch,
        {
            "name": "name",
            "record_status": "record_status",
            "criticality": "criticality",
            "technical_fit": "properties.technical_fit",
            "internet_facing": "properties.internet_facing",
        },
    )
    assert preview["counts"]["New"] == 1
    committed = service.commit(batch, actor=architect)
    assert committed == {"created": 1, "updated": 0, "unchanged": 0}
    obj = db.scalar(select(ArchitectureObject).where(ArchitectureObject.name == "Imported App"))
    assert obj is not None
    assert obj.properties["internet_facing"] is True

    update_batch = service.create_batch(object_type_key="application", filename="update.csv", content=b"name,criticality\nImported App,Mission Critical\n", actor=architect)
    update_preview = service.validate(update_batch, {"name": "name", "criticality": "criticality"})
    assert update_preview["counts"]["Update"] == 1
    service.commit(update_batch, actor=architect)
    db.refresh(obj)
    assert obj.criticality == "Mission Critical"

    login(client, "architect")
    exported = client.get("/exports/objects.csv", params={"object_type": "application"})
    assert exported.status_code == 200
    assert "Imported App" in exported.text
    assert "text/csv" in exported.headers["content-type"]


def test_import_ui_requires_architect_role(client: TestClient, db: Session) -> None:
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    assert client.get("/imports").status_code == 403


def test_demo_dataset_is_idempotent_and_removable(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    service = DemoDataService(db)
    first = service.seed(architect)
    assert first["objects"] >= 80
    assert first["relationships"] >= 30
    second = service.seed(architect)
    assert second["created"] == 0
    demo_objects = list(
        db.scalars(
            select(ArchitectureObject)
            .join(ArchitectureObject.tags)
            .where(ArchitectureObject.tags.any(name=DEMO_TAG), ArchitectureObject.archived_at.is_(None))
        ).unique().all()
    )
    assert len(demo_objects) == first["objects"]
    removed = service.remove(architect)
    assert removed["objects"] == first["objects"]


def test_api_v1_relationship_impact_findings_reviews_and_analytics(client: TestClient, db: Session) -> None:
    create_user(db, "architect2", ARCHITECT)
    login(client, "architect2")
    app = client.post("/api/v1/objects", json={"object_type_key": "application", "name": "API Impact App", "record_status": "Active", "properties": {}}).json()
    cap = client.post("/api/v1/objects", json={"object_type_key": "business_capability", "name": "API Impact Capability", "record_status": "Active", "properties": {}}).json()
    relationship = client.post("/api/v1/relationships", json={"relationship_key": "supports", "source_object_id": app["id"], "target_object_id": cap["id"]})
    assert relationship.status_code == 201
    relationship_id = relationship.json()["id"]
    edited = client.patch(f"/api/v1/relationships/{relationship_id}", json={"description": "API-managed support relationship", "confidence": "High", "properties": {}})
    assert edited.status_code == 200
    assert edited.json()["confidence"] == "High"
    review = client.post(f"/api/v1/reviews/{app['id']}", json={"notes": "Reviewed through API"})
    assert review.status_code == 201
    impact = client.get(f"/api/v1/impact/{app['id']}")
    assert impact.status_code == 200
    assert any(item["object"]["id"] == cap["id"] for item in impact.json()["direct"])
    tech = client.post(
        "/api/v1/objects",
        json={"object_type_key": "technology", "name": "API Runtime", "record_status": "Active", "properties": {}},
    ).json()
    retargeted = client.patch(
        f"/api/v1/relationships/{relationship_id}",
        json={
            "relationship_key": "uses",
            "target_object_id": tech["id"],
            "description": "API-managed technology relationship",
            "confidence": "High",
            "properties": {},
        },
    )
    assert retargeted.status_code == 200
    assert retargeted.json()["relationship_type"]["key"] == "uses"
    assert retargeted.json()["target_object_id"] == tech["id"]
    assert client.get("/api/v1/findings").status_code == 200
    assert client.get("/api/v1/reviews").status_code == 200
    assert client.get("/api/v1/analytics").status_code == 200
    assert client.get("/docs").status_code == 200
