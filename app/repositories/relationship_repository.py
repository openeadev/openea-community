from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.metamodel import ArchitectureRelationship, RelationshipRule, RelationshipType


class RelationshipRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, relationship_id: str, *, include_archived: bool = False) -> ArchitectureRelationship | None:
        stmt = select(ArchitectureRelationship).where(ArchitectureRelationship.id == relationship_id)
        if not include_archived:
            stmt = stmt.where(ArchitectureRelationship.archived_at.is_(None))
        return self.db.scalar(stmt)

    def list_for_object(
        self,
        object_id: str,
        *,
        include_archived_related: bool = True,
    ) -> list[ArchitectureRelationship]:
        relationships = list(
            self.db.scalars(
                select(ArchitectureRelationship)
                .where(
                    ArchitectureRelationship.archived_at.is_(None),
                    or_(
                        ArchitectureRelationship.source_object_id == object_id,
                        ArchitectureRelationship.target_object_id == object_id,
                    ),
                )
                .order_by(ArchitectureRelationship.created_at)
            ).unique().all()
        )
        if include_archived_related:
            return relationships

        return [
            relationship
            for relationship in relationships
            if (
                relationship.target_object
                if relationship.source_object_id == object_id
                else relationship.source_object
            ).archived_at
            is None
        ]

    def list_valid_types_for_source_type(self, source_type_id: str) -> list[RelationshipType]:
        return list(self.db.scalars(
            select(RelationshipType)
            .join(RelationshipRule)
            .options(selectinload(RelationshipType.rules))
            .where(RelationshipRule.source_object_type_id == source_type_id, RelationshipType.is_active.is_(True))
            .order_by(RelationshipType.name)
        ).unique().all())

    def add(self, relationship: ArchitectureRelationship) -> ArchitectureRelationship:
        self.db.add(relationship)
        self.db.flush()
        return relationship
