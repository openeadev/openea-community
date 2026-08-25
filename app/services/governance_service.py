from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.governance import Comment, Review
from app.models.metamodel import ArchitectureObject
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.audit_service import AuditService
from app.services.job_service import JobService


class GovernanceError(ValueError):
    pass


PRINCIPLE_TRANSITIONS = {
    "Draft": {"Proposed"}, "Proposed": {"Approved", "Draft"},
    "Approved": {"Deprecated"}, "Deprecated": {"Retired"}, "Retired": set(),
}
DECISION_TRANSITIONS = {
    "Draft": {"Proposed"}, "Proposed": {"Accepted", "Rejected", "Draft"},
    "Accepted": {"Superseded", "Deprecated"}, "Rejected": set(),
    "Superseded": set(), "Deprecated": set(), "Expired": set(),
}


class GovernanceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    def transition(self, obj: ArchitectureObject, new_status: str, actor: User) -> ArchitectureObject:
        before = self.audit.object_state(obj)
        key = obj.object_type.key
        prop = "status" if key == "architecture_principle" else "decision_status" if key == "architecture_decision" else None
        if prop is None:
            allowed = {"Draft": {"Submitted"}, "Submitted": {"Approved", "Rejected", "Needs Review"},
                       "Rejected": {"Draft"}, "Needs Review": {"Submitted", "Draft"}, "Approved": {"Needs Review"}}
            current = obj.governance_status or "Draft"
            if new_status not in allowed.get(current, set()):
                raise GovernanceError(f"Invalid governance transition: {current} → {new_status}")
            obj.governance_status = new_status
        else:
            current = str(obj.properties.get(prop) or "Draft")
            transitions = PRINCIPLE_TRANSITIONS if key == "architecture_principle" else DECISION_TRANSITIONS
            if new_status not in transitions.get(current, set()):
                raise GovernanceError(f"Invalid {key.replace('_', ' ')} transition: {current} → {new_status}")
            properties = dict(obj.properties)
            properties[prop] = new_status
            obj.properties = properties
            obj.governance_status = "Approved" if new_status in {"Approved", "Accepted"} else "Rejected" if new_status == "Rejected" else "Submitted" if new_status == "Proposed" else "Draft" if new_status == "Draft" else "Needs Review"
        obj.updated_by = actor.id
        obj.updated_at = datetime.now(timezone.utc)
        self.audit.record(action="GovernanceStatusChanged", entity_type="object", entity_id=obj.id,
                          actor=actor, before=before, after=self.audit.object_state(obj))
        JobService(self.db).enqueue_metrics_recalculation()
        self.db.commit()
        return obj

    def mark_reviewed(self, obj: ArchitectureObject, *, actor: User, notes: str,
                      next_review_date: str | None = None) -> Review:
        before = self.audit.object_state(obj)
        today = date.today()
        next_date = date.fromisoformat(next_review_date) if next_review_date else self._next_review(today, obj.review_frequency)
        review = Review(object_id=obj.id, reviewed_by=actor.id, next_review_date=next_date, notes=notes.strip())
        obj.last_reviewed_date = today
        obj.next_review_date = next_date
        obj.updated_by = actor.id
        obj.updated_at = datetime.now(timezone.utc)
        self.db.add(review)
        self.db.flush()
        self.audit.record(action="ObjectReviewed", entity_type="object", entity_id=obj.id,
                          actor=actor, before=before, after=self.audit.object_state(obj))
        JobService(self.db).enqueue_metrics_recalculation()
        self.db.commit()
        return review

    def add_comment(self, obj: ArchitectureObject, *, actor: User, body: str) -> Comment:
        cleaned = body.strip()
        if not cleaned:
            raise GovernanceError("Comment cannot be empty")
        comment = Comment(object_id=obj.id, user_id=actor.id, body=cleaned)
        self.db.add(comment)
        self.db.flush()
        self.audit.record(action="CommentAdded", entity_type="object", entity_id=obj.id,
                          actor=actor, after={"comment_id": comment.id, "body": cleaned})
        self.db.commit()
        return comment

    def list_reviews(self, object_id: str) -> list[Review]:
        return list(self.db.scalars(select(Review).where(Review.object_id == object_id).order_by(Review.reviewed_at.desc())).all())

    def list_comments(self, object_id: str) -> list[Comment]:
        return list(self.db.scalars(select(Comment).where(Comment.object_id == object_id).order_by(Comment.created_at.desc())).all())

    def overdue_objects(self) -> list[ArchitectureObject]:
        return list(self.db.scalars(select(ArchitectureObject).where(
            ArchitectureObject.archived_at.is_(None), ArchitectureObject.next_review_date < date.today()
        ).order_by(ArchitectureObject.next_review_date)).all())

    def assign_decision_number(self, obj: ArchitectureObject) -> None:
        if obj.object_type.key != "architecture_decision" or obj.properties.get("decision_number"):
            return
        decision_type = ObjectRepository(self.db).get_type_by_key("architecture_decision")
        if decision_type is None:
            return
        count = self.db.scalar(select(func.count()).select_from(ArchitectureObject).where(
            ArchitectureObject.object_type_id == decision_type.id
        )) or 0
        properties = dict(obj.properties)
        properties["decision_number"] = f"ADR-{count:04d}"
        obj.properties = properties

    @staticmethod
    def _next_review(today: date, frequency: str | None) -> date | None:
        days = {"Monthly": 30, "Quarterly": 90, "Semiannual": 182, "Annual": 365}.get(frequency or "")
        return today + timedelta(days=days) if days else None
