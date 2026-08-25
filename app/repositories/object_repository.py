from __future__ import annotations

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.metamodel import ArchitectureObject, ObjectType, Tag


class ObjectRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_type_by_key(self, key: str) -> ObjectType | None:
        return self.db.scalar(select(ObjectType).where(ObjectType.key == key, ObjectType.is_active.is_(True)))

    def list_object_types(self) -> list[ObjectType]:
        return list(
            self.db.scalars(
                select(ObjectType).where(ObjectType.is_active.is_(True)).order_by(ObjectType.domain, ObjectType.name)
            ).all()
        )

    def get_by_id(self, object_id: str, *, include_archived: bool = False) -> ArchitectureObject | None:
        stmt = (
            select(ArchitectureObject)
            .options(
                selectinload(ArchitectureObject.aliases),
                selectinload(ArchitectureObject.tags),
                selectinload(ArchitectureObject.owner_organization),
                selectinload(ArchitectureObject.owner_role),
            )
            .where(ArchitectureObject.id == object_id)
        )
        if not include_archived:
            stmt = stmt.where(ArchitectureObject.archived_at.is_(None))
        return self.db.scalar(stmt)

    def list_reference_objects(self, object_type_key: str) -> list[ArchitectureObject]:
        return list(
            self.db.scalars(
                select(ArchitectureObject)
                .join(ObjectType)
                .where(
                    ObjectType.key == object_type_key,
                    ArchitectureObject.archived_at.is_(None),
                )
                .order_by(ArchitectureObject.name)
            ).all()
        )

    def list_objects(
        self,
        *,
        object_type_key: str | None = None,
        record_status: str | None = None,
        lifecycle_stage: str | None = None,
        criticality: str | None = None,
        tag: str | None = None,
        sort: str = "name",
        direction: str = "asc",
    ) -> list[ArchitectureObject]:
        stmt: Select[tuple[ArchitectureObject]] = (
            select(ArchitectureObject)
            .options(
                selectinload(ArchitectureObject.aliases),
                selectinload(ArchitectureObject.tags),
                selectinload(ArchitectureObject.owner_organization),
                selectinload(ArchitectureObject.owner_role),
            )
            .join(ObjectType)
            .where(ArchitectureObject.archived_at.is_(None))
        )
        if object_type_key:
            stmt = stmt.where(ObjectType.key == object_type_key)
        if record_status:
            stmt = stmt.where(ArchitectureObject.record_status == record_status)
        if lifecycle_stage:
            stmt = stmt.where(ArchitectureObject.lifecycle_stage == lifecycle_stage)
        if criticality:
            stmt = stmt.where(ArchitectureObject.criticality == criticality)
        if tag:
            stmt = stmt.join(ArchitectureObject.tags).where(func.lower(Tag.name) == tag.strip().lower())

        sort_columns = {
            "name": ArchitectureObject.name,
            "type": ObjectType.name,
            "status": ArchitectureObject.record_status,
            "lifecycle": ArchitectureObject.lifecycle_stage,
            "criticality": ArchitectureObject.criticality,
            "updated": ArchitectureObject.updated_at,
        }
        sort_column = sort_columns.get(sort, ArchitectureObject.name)
        order = desc(sort_column) if direction == "desc" else asc(sort_column)
        stmt = stmt.order_by(order, ArchitectureObject.name)
        return list(self.db.scalars(stmt).unique().all())

    def list_tags(self) -> list[Tag]:
        return list(self.db.scalars(select(Tag).order_by(Tag.name)).all())

    def get_or_create_tag(self, name: str) -> Tag:
        normalized = name.strip()
        existing = self.db.scalar(select(Tag).where(func.lower(Tag.name) == normalized.lower()))
        if existing:
            return existing
        tag = Tag(name=normalized)
        self.db.add(tag)
        self.db.flush()
        return tag

    def add(self, obj: ArchitectureObject) -> ArchitectureObject:
        self.db.add(obj)
        self.db.flush()
        return obj
