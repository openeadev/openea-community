from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.governance import AuditEvent
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship
from app.models.user import User


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def object_state(obj: ArchitectureObject) -> dict[str, Any]:
        return {
            "id": obj.id, "object_type": obj.object_type.key, "name": obj.name,
            "description": obj.description, "record_status": obj.record_status,
            "governance_status": obj.governance_status, "lifecycle_stage": obj.lifecycle_stage,
            "criticality": obj.criticality, "owner_organization_id": obj.owner_organization_id,
            "owner_role_id": obj.owner_role_id, "source": obj.source, "confidence": obj.confidence,
            "valid_from": AuditService._json(obj.valid_from), "valid_until": AuditService._json(obj.valid_until),
            "last_reviewed_date": AuditService._json(obj.last_reviewed_date),
            "next_review_date": AuditService._json(obj.next_review_date), "review_frequency": obj.review_frequency,
            "properties": obj.properties, "archived_at": AuditService._json(obj.archived_at),
        }

    @staticmethod
    def relationship_state(rel: ArchitectureRelationship) -> dict[str, Any]:
        return {
            "id": rel.id, "relationship_type": rel.relationship_type.key,
            "source_object_id": rel.source_object_id, "target_object_id": rel.target_object_id,
            "description": rel.description, "criticality": rel.criticality,
            "confidence": rel.confidence, "valid_from": AuditService._json(rel.valid_from),
            "valid_until": AuditService._json(rel.valid_until), "properties": rel.properties,
            "source": rel.source, "archived_at": AuditService._json(rel.archived_at),
        }

    def record(self, *, action: str, entity_type: str, entity_id: str, actor: User | None,
               before: dict[str, Any] | None = None, after: dict[str, Any] | None = None,
               source: str = "Web", correlation_id: str | None = None) -> AuditEvent:
        event = AuditEvent(action=action, entity_type=entity_type, entity_id=entity_id,
                           user_id=actor.id if actor else None, before_state=before,
                           after_state=after, source=source, correlation_id=correlation_id)
        self.db.add(event)
        self.db.flush()
        return event

    def list_for_object(self, object_id: str) -> list[AuditEvent]:
        return list(self.db.scalars(select(AuditEvent).where(
            AuditEvent.entity_id == object_id
        ).order_by(AuditEvent.timestamp.desc())).all())

    @staticmethod
    def _json(value: Any) -> Any:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return value
