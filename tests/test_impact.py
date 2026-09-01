import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, VIEWER
from app.services.auth_service import AuthenticationService
from app.services.impact_service import ImpactAnalysisError, ImpactService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService

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
        data={"username": username, "password": PASSWORD, "csrf_token": csrf_from(page.text), "next": "/explore"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def make_object(db: Session, actor, type_key: str, name: str):
    return ObjectService(db).create_object(
        object_type_key=type_key,
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


def impact_fixture(db: Session):
    architect = create_user(db, "architect", ARCHITECT)
    technology = make_object(db, architect, "technology", "PostgreSQL 17")
    app = make_object(db, architect, "application", "Kanban Boards")
    capability = make_object(db, architect, "business_capability", "Project Management")
    product = make_object(db, architect, "business_product", "Work Management")
    RelationshipService(db).create_relationship(
        relationship_key="uses", source_object_id=app.id, target_object_id=technology.id, actor=architect
    )
    RelationshipService(db).create_relationship(
        relationship_key="supports", source_object_id=app.id, target_object_id=capability.id, actor=architect
    )
    RelationshipService(db).create_relationship(
        relationship_key="requires", source_object_id=product.id, target_object_id=capability.id, actor=architect
    )
    return architect, technology, app, capability, product


def test_direct_and_indirect_impact_preserves_explanation_path(db: Session) -> None:
    _, technology, app, capability, product = impact_fixture(db)
    analysis = ImpactService(db).analyze(technology.id, depth=3)
    by_id = {item.object.id: item for item in analysis.results}
    assert by_id[app.id].depth == 1
    assert by_id[capability.id].depth == 2
    assert by_id[product.id].depth == 3
    assert [step.label for step in by_id[capability.id].path_steps] == ["used by", "supports"]
    assert by_id[capability.id].path_object_ids == [technology.id, app.id, capability.id]


def test_cycle_detection_terminates_without_returning_root(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    a = make_object(db, architect, "application", "A")
    b = make_object(db, architect, "application", "B")
    c = make_object(db, architect, "application", "C")
    service = RelationshipService(db)
    service.create_relationship(relationship_key="depends_on", source_object_id=a.id, target_object_id=b.id, actor=architect)
    service.create_relationship(relationship_key="depends_on", source_object_id=b.id, target_object_id=c.id, actor=architect)
    service.create_relationship(relationship_key="depends_on", source_object_id=c.id, target_object_id=a.id, actor=architect)
    analysis = ImpactService(db).analyze(a.id, depth=5)
    assert {item.object.id for item in analysis.results} == {b.id, c.id}
    assert max(item.depth for item in analysis.results) <= 2


def test_depth_and_filters_limit_results(db: Session) -> None:
    _, technology, app, capability, _ = impact_fixture(db)
    depth_one = ImpactService(db).analyze(technology.id, depth=1)
    assert [item.object.id for item in depth_one.results] == [app.id]
    capability_only = ImpactService(db).analyze(
        technology.id, depth=3, object_type_keys=["business_capability"]
    )
    assert [item.object.id for item in capability_only.results] == [capability.id]
    uses_only = ImpactService(db).analyze(
        technology.id, depth=3, relationship_type_keys=["uses"]
    )
    assert {item.object.id for item in uses_only.results} == {app.id}


def test_invalid_depth_is_rejected(db: Session) -> None:
    architect = create_user(db, "architect", ARCHITECT)
    obj = make_object(db, architect, "technology", "Tech")
    with pytest.raises(ImpactAnalysisError, match="between 1 and 5"):
        ImpactService(db).analyze(obj.id, depth=6)


def test_viewer_can_run_read_only_impact_analysis(client: TestClient, db: Session) -> None:
    _, technology, app, _, _ = impact_fixture(db)
    create_user(db, "viewer", VIEWER)
    login(client, "viewer")
    response = client.get(f"/impact/{technology.id}?depth=3")
    assert response.status_code == 200
    assert "Impact analysis" in response.text
    assert "Kanban Boards" in response.text
    assert f'/explore/{app.id}' in response.text
    assert "impact-graph-data" in response.text


def test_impact_http_filters_are_parsed_and_combined(client: TestClient, db: Session) -> None:
    _, technology, app, capability, _ = impact_fixture(db)
    create_user(db, "impact_filter_viewer", VIEWER)
    login(client, "impact_filter_viewer")

    response = client.get(
        f"/impact/{app.id}?depth=1&relationship_type=supports&object_type=business_capability"
    )
    assert response.status_code == 200
    assert capability.name in response.text
    assert technology.name not in response.text
    assert "supports" in response.text
    assert 'value="supports" selected' in response.text
    assert 'value="business_capability" selected' in response.text


def test_result_type_filter_preserves_intermediate_explanatory_path(db: Session) -> None:
    _, technology, app, capability, _ = impact_fixture(db)
    analysis = ImpactService(db).analyze(
        technology.id,
        depth=2,
        object_type_keys=["business_capability"],
    )
    assert [item.object.id for item in analysis.results] == [capability.id]
    payload = analysis.graph_payload()
    node_ids = {node["data"]["id"] for node in payload["nodes"]}
    assert node_ids == {technology.id, app.id, capability.id}
