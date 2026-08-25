from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, ARCHITECTURE_ADMIN
from app.findings_rules import STANDARD_FINDING_RULES
from app.models.findings import Finding, RuleDefinition
from app.models.governance import AuditEvent
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticationService
from app.services.findings_service import FindingsService
from app.services.job_service import JobService
from app.services.object_service import ObjectService
from app.services.relationship_service import RelationshipService

PASSWORD = "ValidPassword123!"


def create_user(db: Session, username: str = "finding_architect", role: str = ARCHITECT):
    return AuthenticationService(db).create_user(username, username.title(), PASSWORD, {role})


def make_object(db: Session, actor, type_key: str, name: str, *, lifecycle=None, criticality="Medium", properties=None, next_review_date=None):
    obj = ObjectService(db).create_object(
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
        confidence="Confirmed",
        valid_from=None,
        valid_until=None,
        aliases="",
        tags="",
        properties=properties or {},
        actor=actor,
    )
    if next_review_date is not None:
        obj.next_review_date = next_review_date
        db.commit()
    return obj


def test_fifteen_standard_rules_are_seeded_idempotently(db: Session) -> None:
    service = FindingsService(db)
    service.seed_rules()
    service.seed_rules()
    rules = list(db.scalars(select(RuleDefinition)).all())
    assert len(rules) == len(STANDARD_FINDING_RULES) == 16
    assert {r.rule_type for r in rules}.issubset({"date_threshold", "missing_field", "missing_relationship", "related_object_status", "relationship_count", "risk_threshold", "review_overdue", "duplicate_name"})


def test_past_eos_technology_creates_one_finding_without_duplicates(db: Session) -> None:
    actor = create_user(db)
    tech = make_object(db, actor, "technology", "Python 2.7", lifecycle="End of Support", properties={"strategic_status": "Retire", "vendor_support_end": (date.today() - timedelta(days=10)).isoformat()})
    service = FindingsService(db)
    first = service.evaluate_all()
    second = service.evaluate_all()
    rows = list(db.scalars(select(Finding).where(Finding.related_object_id == tech.id, Finding.rule.has(rule_id="TECH-EOS-001"))).all())
    assert first >= 1 and second >= 1
    assert len(rows) == 1
    assert rows[0].status == "Open"
    assert rows[0].severity == "Critical"


def test_application_using_retiring_technology_is_detected(db: Session) -> None:
    actor = create_user(db)
    tech = make_object(db, actor, "technology", "Legacy Runtime", lifecycle="End of Support", properties={"strategic_status": "Retire"})
    app = make_object(db, actor, "application", "Customer App", lifecycle="Active", properties={"technical_fit": "Good"})
    RelationshipService(db).create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=actor)
    FindingsService(db).evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.related_object_id == app.id, Finding.rule.has(rule_id="APP-TECH-001")))
    assert finding is not None
    assert finding.evidence["related_object"] == "Legacy Runtime"


def test_capability_single_dependency_and_data_sor_rules(db: Session) -> None:
    actor = create_user(db)
    cap = make_object(db, actor, "business_capability", "Payments")
    app = make_object(db, actor, "application", "Payments App", lifecycle="Active")
    data = make_object(db, actor, "data_object", "Payment")
    rels = RelationshipService(db)
    rels.create_relationship(relationship_key="supports", source_object_id=app.id, target_object_id=cap.id, actor=actor)
    FindingsService(db).evaluate_all()
    assert db.scalar(select(Finding).where(Finding.related_object_id == cap.id, Finding.rule.has(rule_id="CAP-APP-002"))) is not None
    assert db.scalar(select(Finding).where(Finding.related_object_id == data.id, Finding.rule.has(rule_id="DATA-SOR-001"))) is not None



def test_duplicate_application_services_are_flagged_for_review(db: Session) -> None:
    actor = create_user(db)
    first = make_object(db, actor, "application_service", "Customer Lookup")
    second = make_object(db, actor, "application_service", "  customer   lookup  ")
    FindingsService(db).evaluate_all()
    findings = list(
        db.scalars(
            select(Finding).where(
                Finding.related_object_id.in_([first.id, second.id]),
                Finding.rule.has(rule_id="APP-SVC-DUP-001"),
            )
        ).all()
    )
    assert len(findings) == 2


def test_overdue_review_and_missing_review_date_are_detected(db: Session) -> None:
    actor = create_user(db)
    overdue = make_object(db, actor, "technology", "Overdue Tech", next_review_date=date.today() - timedelta(days=1))
    missing = make_object(db, actor, "application", "Never Reviewed")
    FindingsService(db).evaluate_all()
    assert db.scalar(select(Finding).where(Finding.related_object_id == overdue.id, Finding.rule.has(rule_id="REVIEW-001"))) is not None
    assert db.scalar(select(Finding).where(Finding.related_object_id == missing.id, Finding.rule.has(rule_id="REVIEW-002"))) is not None


def test_high_risk_mission_critical_application_uses_persisted_metric(db: Session) -> None:
    actor = create_user(db)
    tech = make_object(db, actor, "technology", "Dangerous Tech", lifecycle="End of Support", properties={"strategic_status": "Retire", "vendor_support_end": (date.today() - timedelta(days=1)).isoformat()})
    app = make_object(db, actor, "application", "Core Banking", lifecycle="Sunset", criticality="Mission Critical", properties={"technical_fit": "Poor"})
    RelationshipService(db).create_relationship(relationship_key="uses", source_object_id=app.id, target_object_id=tech.id, actor=actor)
    AnalyticsService(db).calculate_all()
    FindingsService(db).evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.related_object_id == app.id, Finding.rule.has(rule_id="APP-RISK-001")))
    assert finding is not None
    assert finding.evidence["score"] >= 50


def test_cleared_condition_resolves_open_finding(db: Session) -> None:
    actor = create_user(db)
    app = make_object(db, actor, "application", "Ownerless App")
    service = FindingsService(db)
    service.evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.related_object_id == app.id, Finding.rule.has(rule_id="APP-OWNER-001")))
    assert finding is not None and finding.status == "Open"
    org = make_object(db, actor, "organization", "Business Unit")
    app.owner_organization_id = org.id
    db.commit()
    service.evaluate_all()
    db.refresh(finding)
    assert finding.status == "Resolved"
    assert finding.resolution_notes == "Condition no longer detected by rule evaluation."


def test_dismissal_requires_reason_and_is_audited(db: Session) -> None:
    actor = create_user(db)
    app = make_object(db, actor, "application", "No Fit App")
    service = FindingsService(db)
    service.evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.related_object_id == app.id, Finding.rule.has(rule_id="APP-FIT-001")))
    assert finding is not None
    with pytest.raises(ValueError, match="Dismissal requires a reason"):
        service.update_status(finding, status="Dismissed", actor=actor)
    service.update_status(finding, status="Dismissed", actor=actor, dismissal_reason="Accepted exception")
    assert finding.status == "Dismissed"
    assert finding.dismissal_reason == "Accepted exception"
    event = db.scalar(
        select(AuditEvent).where(
            AuditEvent.entity_type == "finding",
            AuditEvent.entity_id == finding.id,
            AuditEvent.action == "FindingStatusChanged",
        )
    )
    assert event is not None


def test_architecture_admin_can_disable_rule(db: Session) -> None:
    admin = create_user(db, "architecture_admin", ARCHITECTURE_ADMIN)
    service = FindingsService(db)
    rule = db.scalar(select(RuleDefinition).where(RuleDefinition.rule_id == "APP-FIT-001"))
    assert rule is not None
    service.set_rule_enabled(rule, False, admin)
    assert rule.enabled is False


def test_worker_processes_findings_job(db: Session) -> None:
    from app.workers.metrics_worker import run_once

    actor = create_user(db)
    tech = make_object(db, actor, "technology", "Worker Legacy", lifecycle="End of Support", properties={"vendor_support_end": (date.today() - timedelta(days=1)).isoformat()})
    # Object creation queues metrics first and findings second. Process both.
    assert run_once() is True
    assert run_once() is True
    db.expire_all()
    job = db.scalar(select(__import__("app.models.analytics", fromlist=["Job"]).Job).where(__import__("app.models.analytics", fromlist=["Job"]).Job.job_type == JobService.FINDINGS_JOB))
    finding = db.scalar(select(Finding).where(Finding.related_object_id == tech.id, Finding.rule.has(rule_id="TECH-EOS-001")))
    assert job is not None and job.status == "completed"
    assert finding is not None


def test_findings_dashboard_renders_for_authenticated_user(client, db: Session) -> None:
    import re

    create_user(db, "findings_ui", ARCHITECT)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    response = client.post(
        "/login",
        data={"username": "findings_ui", "password": PASSWORD, "csrf_token": token.group(1), "next": "/findings"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    dashboard = client.get("/findings")
    assert dashboard.status_code == 200
    assert "Architecture findings" in dashboard.text


def test_architecture_admin_rule_page_is_server_side_protected(client, db: Session) -> None:
    import re

    create_user(db, "ordinary_architect", ARCHITECT)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={"username": "ordinary_architect", "password": PASSWORD, "csrf_token": token.group(1), "next": "/findings"},
        follow_redirects=False,
    )
    assert client.get("/admin/finding-rules").status_code == 403


def test_custom_missing_field_rule_can_be_created_and_evaluated(db: Session) -> None:
    from app.services.custom_rule_service import CustomRuleService

    admin = create_user(db, "rule_admin", ARCHITECTURE_ADMIN)
    app = make_object(db, admin, "application", "Custom Rule App", properties={"business_fit": "Good"})
    rule = CustomRuleService(db).create_rule(
        payload={
            "name": "Custom missing technical fit",
            "description": "Applications should have technical fit.",
            "rule_type": "missing_field",
            "severity": "Medium",
            "enabled": True,
            "object_types": ["application"],
            "field_name": "technical_fit",
        },
        actor=admin,
    )
    assert rule.rule_id == "CUSTOM-0001"
    assert rule.is_system is False
    FindingsService(db).evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.rule_definition_id == rule.id, Finding.related_object_id == app.id))
    assert finding is not None
    assert finding.title == "Custom missing technical fit: Custom Rule App"


def test_custom_rule_rejects_arbitrary_rule_type_and_unknown_field(db: Session) -> None:
    from app.services.custom_rule_service import CustomRuleService, CustomRuleValidationError

    admin = create_user(db, "rule_validator", ARCHITECTURE_ADMIN)
    service = CustomRuleService(db)
    with pytest.raises(CustomRuleValidationError, match="Unsupported declarative rule type"):
        service.create_rule(
            payload={"name": "No Python", "rule_type": "python_expression", "severity": "High", "object_types": ["application"]},
            actor=admin,
        )
    with pytest.raises(CustomRuleValidationError, match="not defined"):
        service.create_rule(
            payload={"name": "Unknown field", "rule_type": "missing_field", "severity": "Low", "object_types": ["application"], "field_name": "totally_unknown"},
            actor=admin,
        )


def test_custom_rule_delete_is_soft_and_resolves_active_finding(db: Session) -> None:
    from app.services.custom_rule_service import CustomRuleService

    admin = create_user(db, "rule_delete", ARCHITECTURE_ADMIN)
    app = make_object(db, admin, "application", "Archive Rule App", properties={})
    custom = CustomRuleService(db)
    rule = custom.create_rule(
        payload={"name": "Missing technical fit custom", "rule_type": "missing_field", "severity": "Low", "enabled": True, "object_types": ["application"], "field_name": "technical_fit"},
        actor=admin,
    )
    FindingsService(db).evaluate_all()
    finding = db.scalar(select(Finding).where(Finding.rule_definition_id == rule.id, Finding.related_object_id == app.id))
    assert finding is not None and finding.status == "Open"
    custom.archive_custom_rule(rule, actor=admin)
    assert rule.archived_at is not None and rule.enabled is False
    FindingsService(db).evaluate_all()
    db.refresh(finding)
    assert finding.status == "Resolved"


def test_builtin_rule_cannot_be_deleted_but_threshold_can_change(db: Session) -> None:
    from app.services.custom_rule_service import CustomRuleService, CustomRuleValidationError

    admin = create_user(db, "builtin_admin", ARCHITECTURE_ADMIN)
    rule = db.scalar(select(RuleDefinition).where(RuleDefinition.rule_id == "TECH-EOS-002"))
    assert rule is not None
    service = CustomRuleService(db)
    with pytest.raises(CustomRuleValidationError, match="Built-in rules cannot be deleted"):
        service.archive_custom_rule(rule, actor=admin)
    original_name = rule.name
    original_severity = rule.severity
    original_config = dict(rule.config)
    service.update_rule(rule, payload={"severity": "Critical", "days": "90", "date_mode": "within", "enabled": True}, actor=admin)
    assert rule.name == original_name
    assert rule.severity == "Critical"
    assert rule.config["days"] == 90
    FindingsService(db).seed_rules()
    db.refresh(rule)
    assert rule.severity == "Critical"
    assert rule.config["days"] == 90
    rule.severity = original_severity
    rule.config = original_config
    db.commit()


def test_architecture_admin_can_create_custom_rule_from_ui(client, db: Session) -> None:
    import re

    create_user(db, "rule_ui_admin", ARCHITECTURE_ADMIN)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={"username": "rule_ui_admin", "password": PASSWORD, "csrf_token": token.group(1), "next": "/admin/finding-rules"},
        follow_redirects=False,
    )
    form_page = client.get("/admin/finding-rules/new")
    assert form_page.status_code == 200
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', form_page.text)
    assert csrf
    response = client.post(
        "/admin/finding-rules/new",
        data={
            "csrf_token": csrf.group(1),
            "name": "UI Missing Technical Fit",
            "description": "Created through UI",
            "rule_type": "missing_field",
            "severity": "Medium",
            "enabled": "on",
            "object_types": "application",
            "field_name": "technical_fit",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    rule = db.scalar(select(RuleDefinition).where(RuleDefinition.name == "UI Missing Technical Fit"))
    assert rule is not None and rule.is_system is False


def test_builtin_rule_delete_endpoint_is_rejected(client, db: Session) -> None:
    import re

    create_user(db, "rule_delete_admin", ARCHITECTURE_ADMIN)
    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={"username": "rule_delete_admin", "password": PASSWORD, "csrf_token": token.group(1), "next": "/admin/finding-rules"},
        follow_redirects=False,
    )
    rules_page = client.get("/admin/finding-rules")
    csrf = re.search(r'name="csrf_token" value="([^"]+)"', rules_page.text)
    assert csrf
    rule = db.scalar(select(RuleDefinition).where(RuleDefinition.rule_id == "APP-FIT-001"))
    assert rule is not None
    response = client.post(
        f"/admin/finding-rules/{rule.id}/delete",
        data={"csrf_token": csrf.group(1)},
        follow_redirects=False,
    )
    assert response.status_code == 422


def test_findings_dashboard_hides_resolved_by_default_but_can_show_all(client, db: Session) -> None:
    import re

    actor = create_user(db, "findings_history", ARCHITECT)
    obj = make_object(db, actor, "technology", "Resolved History Tech")
    rule = RuleDefinition(
        rule_id="CUSTOM-HISTORY-TEST",
        name="History test rule",
        description="Test rule",
        rule_type="missing_field",
        severity="Low",
        config={"object_type": "technology", "field": "internal_support_end"},
        enabled=False,
        is_system=False,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.add(rule)
    db.flush()
    db.add(
        Finding(
            finding_type="missing_field",
            severity="Low",
            title="Resolved finding should be historical",
            description="History test",
            rule_definition_id=rule.id,
            related_object_id=obj.id,
            status="Resolved",
        )
    )
    db.commit()

    page = client.get("/login")
    token = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
    assert token
    client.post(
        "/login",
        data={"username": "findings_history", "password": PASSWORD, "csrf_token": token.group(1), "next": "/findings"},
        follow_redirects=False,
    )

    current = client.get("/findings")
    assert current.status_code == 200
    assert "Resolved finding should be historical" not in current.text
    assert "Current findings (hide Resolved)" in current.text

    historical = client.get("/findings?status_filter=all")
    assert historical.status_code == 200
    assert "Resolved finding should be historical" in historical.text
