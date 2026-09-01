from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import ARCHITECT, CONTRIBUTOR, VIEWER
from app.models.governance import AuditEvent, Comment, Review
from app.models.user import User
from app.services.auth_service import AuthenticationService
from app.services.governance_service import GovernanceError, GovernanceService
from app.services.object_service import ObjectService


def user_with_role(db: Session, username: str, role: str) -> User:
    return AuthenticationService(db).create_user(username, username.title(), "VeryStrongPass123!", {role})


def create_object(db: Session, actor: User, object_type: str, name: str, properties: dict[str, object]):
    return ObjectService(db).create_object(
        object_type_key=object_type, name=name, description="", record_status="Draft",
        governance_status=None, lifecycle_stage=None, criticality=None, owner_organization_id=None,
        owner_role_id=None, source=None, confidence=None, valid_from=None, valid_until=None,
        aliases="", tags="", properties=properties, review_frequency="Annual", actor=actor,
    )


def test_decision_number_and_workflow_are_governed(db: Session) -> None:
    actor = user_with_role(db, "architect7", ARCHITECT)
    decision = create_object(db, actor, "architecture_decision", "Choose Database", {"context": "Need DB", "decision": "Use PostgreSQL"})
    assert decision.properties["decision_number"] == "ADR-0001"
    assert decision.properties["decision_status"] == "Draft"
    service = GovernanceService(db)
    service.transition(decision, "Proposed", actor)
    service.transition(decision, "Accepted", actor)
    assert decision.properties["decision_status"] == "Accepted"
    with pytest.raises(GovernanceError):
        service.transition(decision, "Draft", actor)


def test_principle_workflow(db: Session) -> None:
    actor = user_with_role(db, "architectp", ARCHITECT)
    principle = create_object(db, actor, "architecture_principle", "Cloud First", {"statement": "Prefer cloud"})
    service = GovernanceService(db)
    service.transition(principle, "Proposed", actor)
    service.transition(principle, "Approved", actor)
    assert principle.properties["status"] == "Approved"
    assert principle.governance_status == "Approved"


def test_review_updates_dates_and_is_audited(db: Session) -> None:
    actor = user_with_role(db, "architectr", ARCHITECT)
    obj = create_object(db, actor, "application", "Review Me", {})
    review = GovernanceService(db).mark_reviewed(obj, actor=actor, notes="Reviewed")
    assert review.reviewed_by == actor.id
    assert obj.last_reviewed_date == date.today()
    assert obj.next_review_date == date.today() + timedelta(days=365)
    assert db.scalar(select(Review).where(Review.object_id == obj.id)) is not None
    assert db.scalar(select(AuditEvent).where(AuditEvent.entity_id == obj.id, AuditEvent.action == "ObjectReviewed")) is not None


def test_comments_are_persisted_and_audited(db: Session) -> None:
    actor = user_with_role(db, "contributor7", CONTRIBUTOR)
    obj = create_object(db, actor, "application", "Comment Me", {})
    comment = GovernanceService(db).add_comment(obj, actor=actor, body="Architecture note")
    assert comment.body == "Architecture note"
    assert db.scalar(select(Comment).where(Comment.object_id == obj.id)) is not None
    assert db.scalar(select(AuditEvent).where(AuditEvent.entity_id == obj.id, AuditEvent.action == "CommentAdded")) is not None


def test_object_update_generates_before_after_audit(db: Session) -> None:
    actor = user_with_role(db, "architecta", ARCHITECT)
    obj = create_object(db, actor, "application", "Before", {})
    ObjectService(db).update_object(obj, actor=actor, name="After", description="", record_status="Draft",
        governance_status="Approved", lifecycle_stage=None, criticality=None, owner_organization_id=None,
        owner_role_id=None, source=None, confidence=None, valid_from=None, valid_until=None, aliases="", tags="",
        properties={}, review_frequency="Annual")
    event = db.scalar(select(AuditEvent).where(AuditEvent.entity_id == obj.id, AuditEvent.action == "ObjectUpdated"))
    assert event is not None
    assert event.before_state["name"] == "Before"
    assert event.after_state["name"] == "After"
    assert obj.governance_status == "Draft"  # direct form edits cannot bypass governance workflow


def test_overdue_reviews_identified(db: Session) -> None:
    actor = user_with_role(db, "architecto", ARCHITECT)
    obj = create_object(db, actor, "application", "Overdue", {})
    obj.next_review_date = date.today() - timedelta(days=1)
    db.commit()
    assert obj.id in {item.id for item in GovernanceService(db).overdue_objects()}


def test_superseding_decision_records_relationship_and_status(db: Session) -> None:
    from app.services.relationship_service import RelationshipService

    actor = user_with_role(db, "architects", ARCHITECT)
    old = create_object(db, actor, "architecture_decision", "Old Decision", {"context": "Old", "decision": "Old"})
    new = create_object(db, actor, "architecture_decision", "New Decision", {"context": "New", "decision": "New"})
    service = GovernanceService(db)
    for item in (old, new):
        service.transition(item, "Proposed", actor)
        service.transition(item, "Accepted", actor)
    RelationshipService(db).create_relationship(relationship_key="supersedes", source_object_id=new.id, target_object_id=old.id, actor=actor)
    service.transition(old, "Superseded", actor)
    assert old.properties["decision_status"] == "Superseded"
    assert len(db.scalars(select(AuditEvent).where(AuditEvent.entity_id == old.id)).all()) >= 1


def test_viewer_cannot_govern_but_can_view_history(client, db: Session) -> None:
    architect = user_with_role(db, "architectv", ARCHITECT)
    obj = create_object(db, architect, "application", "Governed App", {})
    viewer = user_with_role(db, "viewer7", VIEWER)
    with client as _:
        # authenticate by placing the same signed session structure used by the app through login
        response = client.get("/login")
        import re
        token = re.search(r'name="csrf_token" value="([^"]+)"', response.text).group(1)
        client.post("/login", data={"username": viewer.username, "password": "VeryStrongPass123!", "csrf_token": token})
        page = client.get(f"/explore/{obj.id}?tab=history")
        assert page.status_code == 200
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        denied = client.post(f"/explore/{obj.id}/governance", data={"status": "Submitted", "csrf_token": token})
        assert denied.status_code == 403


def test_reviews_workspace_explains_all_applicable_attention_reasons(client, db: Session) -> None:
    actor = user_with_role(db, "review_reason_architect", ARCHITECT)
    obj = create_object(db, actor, "application", "Review Reason App", {})
    obj.next_review_date = date.today() - timedelta(days=3)
    obj.last_reviewed_date = None
    obj.governance_status = "Needs Review"
    obj.confidence = "Low"
    db.commit()

    item = next(
        item
        for item in GovernanceService(db).review_attention_items()
        if item.object.id == obj.id
    )
    assert any("overdue by 3 days" in reason for reason in item.reasons)
    assert "No completed review has been recorded." in item.reasons
    assert "Governance status is Needs Review." in item.reasons
    assert "Confidence is Low." in item.reasons

    response = client.get("/login")
    import re
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert token
    client.post(
        "/login",
        data={
            "username": actor.username,
            "password": "VeryStrongPass123!",
            "csrf_token": token.group(1),
            "next": "/reviews",
        },
        follow_redirects=False,
    )
    page = client.get("/reviews")
    assert page.status_code == 200
    assert "Attention reason" in page.text
    assert "Review overdue by 3 days" in page.text
    assert "Governance status is Needs Review." in page.text
    assert "Confidence is Low." in page.text
