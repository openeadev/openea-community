from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, VIEWER
from app.models.analytics import ObjectMetric
from app.services.auth_service import AuthenticationService
from app.services.object_service import ObjectService
from app.services.portfolio_service import PortfolioService
from app.services.relationship_service import RelationshipService

PASSWORD = "ValidPassword123!"


def create_user(db: Session, username: str, role: str):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def make_object(db: Session, actor, type_key: str, name: str, *, lifecycle=None, properties=None, valid_from=None, valid_until=None):
    return ObjectService(db).create_object(
        object_type_key=type_key,
        name=name,
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage=lifecycle,
        criticality="Medium",
        owner_organization_id=None,
        owner_role_id=None,
        source="Manual",
        confidence="Confirmed",
        valid_from=valid_from,
        valid_until=valid_until,
        aliases="",
        tags="",
        properties=properties or {},
        actor=actor,
    )


def login(client: TestClient, username: str) -> None:
    import re

    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    response = client.post("/login", data={"username": username, "password": PASSWORD, "csrf_token": token.group(1), "next": "/portfolio"}, follow_redirects=False)
    assert response.status_code == 303


def test_application_portfolio_derives_time_quadrant_and_risk(db: Session) -> None:
    actor = create_user(db, "portfolio_architect", ARCHITECT)
    app = make_object(db, actor, "application", "Customer App", lifecycle="Active", properties={"business_fit": "Good", "technical_fit": "Poor", "strategic_fit": "Good", "hosting_model": "Cloud"})
    db.add(ObjectMetric(object_id=app.id, metric_type="application_risk", score=72, band="High", explanation={}))
    db.commit()
    row = PortfolioService(db).application_portfolio()[0]
    assert row.time_quadrant == "Migrate"
    assert row.risk is not None and row.risk.score == 72
    assert row.hosting_model == "Cloud"


def test_technology_portfolio_counts_dependent_applications(db: Session) -> None:
    actor = create_user(db, "tech_portfolio_architect", ARCHITECT)
    tech = make_object(db, actor, "technology", "Legacy Runtime", lifecycle="End of Support", properties={"strategic_status": "Retire", "vendor_support_end": date.today().isoformat()})
    app = make_object(db, actor, "application", "Runtime Consumer", lifecycle="Active")
    RelationshipService(db).create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=actor)
    row = PortfolioService(db).technology_portfolio()[0]
    assert row.dependent_applications == 1
    assert row.support_end == date.today()


def test_capability_map_builds_hierarchy_and_application_count(db: Session) -> None:
    actor = create_user(db, "capability_architect", ARCHITECT)
    parent = make_object(db, actor, "business_capability", "Customer Management", properties={"maturity": "Managed", "strategic_importance": "High"})
    child = make_object(db, actor, "business_capability", "Customer Service", properties={"parent_capability": parent.id, "maturity": "Defined"})
    app = make_object(db, actor, "application", "Service App", lifecycle="Active")
    RelationshipService(db).create_relationship(relationship_key="supports", source_object_id=app.id, target_object_id=child.id, actor=actor)
    roots = PortfolioService(db).capability_map()
    assert len(roots) == 1
    assert roots[0].object.id == parent.id
    assert roots[0].children[0].object.id == child.id
    assert roots[0].children[0].supporting_applications == 1


def test_roadmaps_are_derived_from_structured_dates(db: Session) -> None:
    actor = create_user(db, "roadmap_architect", ARCHITECT)
    start = date.today()
    end = start + timedelta(days=365)
    make_object(db, actor, "application", "Roadmap App", lifecycle="Planned", properties={"go_live_date": start.isoformat(), "planned_retirement_date": end.isoformat()})
    make_object(db, actor, "initiative", "Modernization", properties={"start_date": start.isoformat(), "target_end_date": end.isoformat(), "status": "In Progress"})
    items = PortfolioService(db).roadmaps()
    assert {item.object.name for item in items} == {"Roadmap App", "Modernization"}
    assert all(item.start == start and item.end == end for item in items)


def test_viewer_can_access_read_only_portfolio_pages(client: TestClient, db: Session) -> None:
    create_user(db, "portfolio_viewer", VIEWER)
    login(client, "portfolio_viewer")
    for path in ("/portfolio", "/portfolio/applications", "/portfolio/technologies", "/portfolio/capabilities", "/roadmaps"):
        response = client.get(path)
        assert response.status_code == 200


def test_portfolio_navigation_is_visible(client: TestClient, db: Session) -> None:
    create_user(db, "portfolio_nav_viewer", VIEWER)
    login(client, "portfolio_nav_viewer")
    page = client.get("/portfolio")
    assert "Application Portfolio" in page.text
    assert "Technology Portfolio" in page.text
    assert "Capability Map" in page.text
    assert "Roadmaps" in page.text


def test_application_portfolio_filters_combine(db: Session) -> None:
    actor = create_user(db, "portfolio_filter_architect", ARCHITECT)
    keep = make_object(db, actor, "application", "Keep App", lifecycle="Active", properties={"business_fit": "Good", "technical_fit": "Good"})
    make_object(db, actor, "application", "Drop App", lifecycle="Sunset", properties={"business_fit": "Good", "technical_fit": "Poor"})
    db.add(ObjectMetric(object_id=keep.id, metric_type="application_risk", score=55, band="High", explanation={}))
    db.commit()
    rows = PortfolioService(db).application_portfolio(lifecycle="Active", risk_band="High")
    assert [row.object.name for row in rows] == ["Keep App"]


def test_capability_overlays_derive_application_and_technology_risk(db: Session) -> None:
    actor = create_user(db, "overlay_architect", ARCHITECT)
    capability = make_object(db, actor, "business_capability", "Digital Service")
    app = make_object(db, actor, "application", "Digital App", lifecycle="Active")
    tech = make_object(db, actor, "technology", "Risk Tech", lifecycle="Aging")
    RelationshipService(db).create_relationship(relationship_key="supports", source_object_id=app.id, target_object_id=capability.id, actor=actor)
    RelationshipService(db).create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=actor)
    db.add_all([
        ObjectMetric(object_id=app.id, metric_type="application_risk", score=61, band="High", explanation={}),
        ObjectMetric(object_id=tech.id, metric_type="technology_risk", score=77, band="Critical", explanation={}),
    ])
    db.commit()
    node = PortfolioService(db).capability_map()[0]
    assert node.application_risk == 61
    assert node.technology_risk == 77
