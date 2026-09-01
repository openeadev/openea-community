from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from difflib import SequenceMatcher

from sqlalchemy import exists, func, literal, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.metamodel import ArchitectureObject, ObjectAlias, ObjectType, Tag, object_tags


@dataclass(frozen=True)
class SearchPage:
    items: list[ArchitectureObject]
    total: int
    page: int
    per_page: int

    @property
    def pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)


class SearchService:
    """Repository search abstraction. External identifiers can be added here later."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        *,
        query: str | None = None,
        object_type_key: str | None = None,
        record_status: str | None = None,
        lifecycle_stage: str | None = None,
        criticality: str | None = None,
        governance_status: str | None = None,
        owner_id: str | None = None,
        tag: str | None = None,
        review_status: str | None = None,
        archive_scope: str = "current",
        sort: str = "name",
        direction: str = "asc",
        page: int = 1,
        per_page: int = 25,
    ) -> SearchPage:
        page = max(1, page)
        per_page = min(max(1, per_page), 100)
        dialect = self.db.bind.dialect.name if self.db.bind is not None else ""
        if dialect == "postgresql":
            return self._search_postgres(
                query=query,
                object_type_key=object_type_key,
                record_status=record_status,
                lifecycle_stage=lifecycle_stage,
                criticality=criticality,
                governance_status=governance_status,
                owner_id=owner_id,
                tag=tag,
                review_status=review_status,
                archive_scope=archive_scope,
                sort=sort,
                direction=direction,
                page=page,
                per_page=per_page,
            )
        return self._search_portable(
            query=query,
            object_type_key=object_type_key,
            record_status=record_status,
            lifecycle_stage=lifecycle_stage,
            criticality=criticality,
            governance_status=governance_status,
            owner_id=owner_id,
            tag=tag,
            review_status=review_status,
            archive_scope=archive_scope,
            sort=sort,
            direction=direction,
            page=page,
            per_page=per_page,
        )

    def _base(self, archive_scope: str = "current"):
        if archive_scope not in {"current", "archived", "all"}:
            raise ValueError("archive_scope must be current, archived, or all")

        stmt = (
            select(ArchitectureObject)
            .options(
                selectinload(ArchitectureObject.aliases),
                selectinload(ArchitectureObject.tags),
                selectinload(ArchitectureObject.owner_organization),
                selectinload(ArchitectureObject.owner_role),
            )
            .join(ObjectType)
        )
        if archive_scope == "current":
            stmt = stmt.where(ArchitectureObject.archived_at.is_(None))
        elif archive_scope == "archived":
            stmt = stmt.where(ArchitectureObject.archived_at.is_not(None))
        return stmt

    def _filters(self, stmt, **filters):
        if filters.get("object_type_key"):
            stmt = stmt.where(ObjectType.key == filters["object_type_key"])
        if filters.get("record_status"):
            stmt = stmt.where(ArchitectureObject.record_status == filters["record_status"])
        if filters.get("lifecycle_stage"):
            stmt = stmt.where(ArchitectureObject.lifecycle_stage == filters["lifecycle_stage"])
        if filters.get("criticality"):
            stmt = stmt.where(ArchitectureObject.criticality == filters["criticality"])
        if filters.get("governance_status"):
            stmt = stmt.where(ArchitectureObject.governance_status == filters["governance_status"])
        if filters.get("owner_id"):
            stmt = stmt.where(
                or_(
                    ArchitectureObject.owner_organization_id == filters["owner_id"],
                    ArchitectureObject.owner_role_id == filters["owner_id"],
                )
            )
        if filters.get("tag"):
            stmt = stmt.where(
                exists(
                    select(literal(1))
                    .select_from(object_tags.join(Tag, object_tags.c.tag_id == Tag.id))
                    .where(
                        object_tags.c.object_id == ArchitectureObject.id,
                        func.lower(Tag.name) == str(filters["tag"]).strip().lower(),
                    )
                )
            )
        review_status = filters.get("review_status")
        today = date.today()
        if review_status == "overdue":
            stmt = stmt.where(ArchitectureObject.next_review_date < today)
        elif review_status == "current":
            stmt = stmt.where(ArchitectureObject.next_review_date >= today)
        elif review_status == "unscheduled":
            stmt = stmt.where(ArchitectureObject.next_review_date.is_(None))
        return stmt

    def _search_postgres(self, *, query: str | None, sort: str, direction: str, page: int, per_page: int, **filters) -> SearchPage:
        archive_scope = str(filters.pop("archive_scope", "current"))
        if filters.get("record_status") == "Archived" and archive_scope == "current":
            archive_scope = "archived"
        stmt = self._filters(self._base(archive_scope), **filters)
        q = (query or "").strip()
        rank = literal(0.0)
        if q:
            document = func.to_tsvector(
                "simple", func.coalesce(ArchitectureObject.name, "") + " " + func.coalesce(ArchitectureObject.description, "")
            )
            tsquery = func.websearch_to_tsquery("simple", q)
            alias_match = exists(select(literal(1)).where(ObjectAlias.object_id == ArchitectureObject.id, ObjectAlias.alias.op("%") (q)))
            tag_match = exists(
                select(literal(1)).select_from(object_tags.join(Tag, object_tags.c.tag_id == Tag.id)).where(
                    object_tags.c.object_id == ArchitectureObject.id, Tag.name.op("%") (q)
                )
            )
            stmt = stmt.where(or_(document.op("@@")(tsquery), ArchitectureObject.name.op("%") (q), alias_match, tag_match))
            rank = func.greatest(func.ts_rank(document, tsquery), func.similarity(ArchitectureObject.name, q))

        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total = int(self.db.scalar(count_stmt) or 0)
        stmt = self._order(stmt, sort=sort, direction=direction, relevance=rank if q else None)
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        return SearchPage(list(self.db.scalars(stmt).unique().all()), total, page, per_page)

    def _search_portable(self, *, query: str | None, sort: str, direction: str, page: int, per_page: int, **filters) -> SearchPage:
        archive_scope = str(filters.pop("archive_scope", "current"))
        if filters.get("record_status") == "Archived" and archive_scope == "current":
            archive_scope = "archived"
        stmt = self._filters(self._base(archive_scope), **filters)
        items = list(self.db.scalars(stmt).unique().all())
        q = (query or "").strip().casefold()
        if q:
            def score(obj: ArchitectureObject) -> float:
                values = [obj.name, obj.description, *(a.alias for a in obj.aliases), *(t.name for t in obj.tags)]
                normalized = [str(v or "").casefold() for v in values]
                if any(q in value for value in normalized):
                    return 1.0
                return max((SequenceMatcher(None, q, value).ratio() for value in normalized if value), default=0.0)
            scored = [(score(obj), obj) for obj in items]
            items = [obj for value, obj in scored if value >= 0.55]
            if sort == "relevance":
                items.sort(key=lambda obj: score(obj), reverse=True)
        if sort != "relevance" or not q:
            reverse = direction == "desc"
            key_map = {
                "name": lambda o: o.name.casefold(),
                "type": lambda o: o.object_type.name.casefold(),
                "status": lambda o: o.record_status.casefold(),
                "lifecycle": lambda o: (o.lifecycle_stage or "").casefold(),
                "criticality": lambda o: (o.criticality or "").casefold(),
                "updated": lambda o: o.updated_at,
            }
            items.sort(key=key_map.get(sort, key_map["name"]), reverse=reverse)
        total = len(items)
        start = (page - 1) * per_page
        return SearchPage(items[start:start + per_page], total, page, per_page)

    @staticmethod
    def _order(stmt, *, sort: str, direction: str, relevance=None):
        if relevance is not None and sort == "relevance":
            return stmt.order_by(relevance.desc(), ArchitectureObject.name.asc())
        columns = {
            "name": ArchitectureObject.name,
            "type": ObjectType.name,
            "status": ArchitectureObject.record_status,
            "lifecycle": ArchitectureObject.lifecycle_stage,
            "criticality": ArchitectureObject.criticality,
            "updated": ArchitectureObject.updated_at,
        }
        column = columns.get(sort, ArchitectureObject.name)
        return stmt.order_by(column.desc() if direction == "desc" else column.asc(), ArchitectureObject.name.asc())
