from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT
from app.models.analytics import Job, ObjectMetric
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticationService
from app.services.job_service import JobService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService

PASSWORD = "ValidPassword123!"


def create_user(db: Session):
    return AuthenticationService(db).create_user("analytics_architect", "Analytics Architect", PASSWORD, {ARCHITECT})


def make_object(db: Session, actor, type_key: str, name: str, *, lifecycle=None, criticality="Medium", confidence="Confirmed", properties=None):
    return ObjectService(db).create_object(
        object_type_key=type_key,
        name=name,
        description="",
        record_status="Active",
        governance_status=None,
        lifecycle_stage=lifecycle,
        criticality=criticality,
        owner_organization_id=None,
        owner_role_id=None,
        source="Manual",
        confidence=confidence,
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="",
        properties=properties or {},
        actor=actor,
    )


def test_technology_risk_uses_documented_strategy_and_support_horizon(db: Session) -> None:
    actor = create_user(db)
    tech = make_object(
        db,
        actor,
        "technology",
        "Legacy Database",
        lifecycle="End of Support",
        criticality="High",
        properties={
            "strategic_status": "Retire",
            "vendor_support_end": (date.today() - timedelta(days=10)).isoformat(),
        },
    )
    service = AnalyticsService(db)
    service.calculate_all()
    metric = service.metric(tech.id, "technology_risk")
    assert metric is not None
    assert 75 <= metric.score <= 100
    assert metric.band == "Critical"
    assert metric.explanation["components"]["support_horizon"] == 100
    assert metric.explanation["components"]["internal_strategy"] == 100


def test_application_risk_uses_highest_material_technology_risk(db: Session) -> None:
    actor = create_user(db)
    safe = make_object(db, actor, "technology", "Safe Tech", lifecycle="Current", properties={"strategic_status": "Strategic", "vendor_support_end": (date.today() + timedelta(days=1500)).isoformat()})
    risky = make_object(db, actor, "technology", "Risky Tech", lifecycle="End of Support", properties={"strategic_status": "Retire", "vendor_support_end": (date.today() - timedelta(days=1)).isoformat()})
    app = make_object(db, actor, "application", "Critical App", lifecycle="Active", criticality="Mission Critical", properties={"technical_fit": "Poor"})
    rels = RelationshipService(db)
    rels.create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=safe.id, actor=actor)
    rels.create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=risky.id, actor=actor)
    service = AnalyticsService(db)
    service.calculate_all()
    risky_metric = service.metric(risky.id, "technology_risk")
    app_metric = service.metric(app.id, "application_risk")
    assert risky_metric is not None and app_metric is not None
    assert app_metric.explanation["components"]["technology_risk"] == risky_metric.score
    assert app_metric.explanation["criticality_multiplier"] == 1.3


def test_capability_risk_flags_single_point_of_failure(db: Session) -> None:
    actor = create_user(db)
    capability = make_object(db, actor, "business_capability", "Payments", properties={"maturity": "Defined"})
    app = make_object(db, actor, "application", "Payments App", lifecycle="Active", properties={"technical_fit": "Fair"})
    RelationshipService(db).create_relationship(relationship_key="supports", source_object_id=app.id, target_object_id=capability.id, actor=actor)
    service = AnalyticsService(db)
    service.calculate_all()
    metric = service.metric(capability.id, "capability_risk")
    assert metric is not None
    assert metric.explanation["components"]["single_point_of_failure"] == 100
    assert metric.explanation["inputs"]["supporting_application_count"] == 1


def test_data_quality_and_impact_metrics_are_persisted_with_explanations(db: Session) -> None:
    actor = create_user(db)
    app = make_object(db, actor, "application", "Sparse App", lifecycle="Active", confidence="Unknown", properties={})
    service = AnalyticsService(db)
    service.calculate_all()
    metrics = service.metrics_for_object(app.id)
    metric_types = {metric.metric_type for metric in metrics}
    assert {"data_quality", "application_risk", "impact_severity"}.issubset(metric_types)
    for metric in metrics:
        assert 0 <= metric.score <= 100
        assert metric.band in {"Low", "Moderate", "High", "Critical"}
        assert "formula" in metric.explanation
        assert "components" in metric.explanation


def test_relevant_writes_enqueue_deduplicated_recalculation_job(db: Session) -> None:
    actor = create_user(db)
    make_object(db, actor, "technology", "Queued Tech")
    make_object(db, actor, "application", "Queued App")
    jobs = list(db.scalars(select(Job).where(Job.status == "queued", Job.job_type == JobService.METRICS_JOB)).all())
    assert len(jobs) == 1


def test_repository_health_is_visible_after_calculation(db: Session) -> None:
    actor = create_user(db)
    make_object(db, actor, "application", "Health App", lifecycle="Active", properties={"technical_fit": "Good"})
    service = AnalyticsService(db)
    service.calculate_all()
    health = service.repository_health()
    assert health.object_count == 1
    assert health.metrics_count == 1
    assert 0 <= health.score <= 100


def test_worker_processes_queued_metrics_job(db: Session) -> None:
    from app.workers.metrics_worker import run_once

    actor = create_user(db)
    app = make_object(db, actor, "application", "Worker App", lifecycle="Active", properties={"technical_fit": "Good"})
    assert run_once() is True
    db.expire_all()
    metric = db.scalar(select(ObjectMetric).where(ObjectMetric.object_id == app.id, ObjectMetric.metric_type == "application_risk"))
    job = db.scalar(select(Job).where(Job.job_type == JobService.METRICS_JOB))
    assert metric is not None
    assert job is not None and job.status == "completed"


def test_repository_health_dimension_explains_ownership_gaps(db: Session) -> None:
    actor = create_user(db)
    app = make_object(db, actor, "application", "Unowned Health App", lifecycle="Active", properties={"technical_fit": "Good"})
    service = AnalyticsService(db)
    service.calculate_all()

    detail = service.repository_health_dimension("ownership")
    assert detail["label"] == "Ownership"
    assert detail["score"] == 0
    item = next(item for item in detail["items"] if item["object"].id == app.id)
    assert item["score"] == 0
    assert "No owner organization" in item["reason"]


def test_repository_health_cards_link_to_explainable_drilldowns(client, db: Session) -> None:
    import re

    create_user(db)
    service = AnalyticsService(db)
    service.calculate_all()

    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={"username": "analytics_architect", "password": PASSWORD, "csrf_token": token.group(1), "next": "/analytics"},
        follow_redirects=False,
    )

    dashboard = client.get("/analytics")
    assert dashboard.status_code == 200
    assert '/analytics/health/ownership' in dashboard.text
    assert "How many active records have a recognized accountable owner." in dashboard.text

    detail = client.get("/analytics/health/ownership")
    assert detail.status_code == 200
    assert "Objects reducing ownership" in detail.text


def test_metric_view_provides_explainable_guidance_and_actions(db: Session) -> None:
    actor = create_user(db)
    app = make_object(
        db,
        actor,
        "application",
        "Explainable App",
        lifecycle="Active",
        confidence="Unknown",
        properties={"technical_fit": "Poor"},
    )
    service = AnalyticsService(db)
    service.calculate_all()

    dq = service.metric(app.id, "data_quality")
    risk = service.metric(app.id, "application_risk")
    assert dq is not None and risk is not None

    dq_view = service.metric_view(dq)
    assert dq_view["label"] == "Data Quality"
    assert "Higher is better" in dq_view["direction"]
    assert any("owner" in item.lower() or "missing" in item.lower() for item in dq_view["recommendations"])

    risk_view = service.metric_view(risk)
    assert risk_view["label"] == "Application Risk"
    assert "Lower is better" in risk_view["direction"]
    urls = {item["url"] for item in risk_view["actions"]}
    assert f"/explore/{app.id}/edit" in urls
    assert f"/explore/{app.id}?tab=relationships" in urls
    assert f"/explore/{app.id}?tab=lifecycle" in urls


def test_object_metrics_page_exposes_expandable_calculation_details(client, db: Session) -> None:
    import re

    actor = create_user(db)
    app = make_object(
        db,
        actor,
        "application",
        "Metric Help App",
        lifecycle="Active",
        confidence="Unknown",
        properties={"technical_fit": "Fair"},
    )
    AnalyticsService(db).calculate_all()

    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={
            "username": actor.username,
            "password": PASSWORD,
            "csrf_token": token.group(1),
            "next": f"/analytics/objects/{app.id}",
        },
        follow_redirects=False,
    )
    metrics_page = client.get(f"/analytics/objects/{app.id}")
    assert metrics_page.status_code == 200
    assert "How is this calculated and what can I do?" in metrics_page.text
    assert "Current inputs" in metrics_page.text
    assert "How to respond" in metrics_page.text
    assert "Metrics are decision-support signals" in metrics_page.text
    assert f'/explore/{app.id}?tab=relationships' in metrics_page.text
