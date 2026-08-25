from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analytics import ObjectMetric
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship

FIT_VALUE = {"Poor": 1, "Fair": 2, "Unknown": 2, "Good": 3, "Excellent": 4}


@dataclass
class ApplicationPortfolioRow:
    object: ArchitectureObject
    risk: ObjectMetric | None
    business_fit: str
    technical_fit: str
    strategic_fit: str
    hosting_model: str
    time_quadrant: str


@dataclass
class TechnologyPortfolioRow:
    object: ArchitectureObject
    risk: ObjectMetric | None
    support_end: date | None
    dependent_applications: int


@dataclass
class CapabilityNode:
    object: ArchitectureObject
    risk: ObjectMetric | None
    supporting_applications: int
    application_risk: int
    technology_risk: int
    maturity: str
    strategic_importance: str
    children: list[CapabilityNode] = field(default_factory=list)


@dataclass
class RoadmapItem:
    object: ArchitectureObject
    category: str
    start: date | None
    end: date | None
    label: str


class PortfolioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def application_portfolio(self, *, lifecycle: str | None = None, risk_band: str | None = None) -> list[ApplicationPortfolioRow]:
        apps = self._objects("application")
        metrics = self._metric_map("application_risk")
        rows = []
        for obj in apps:
            business_fit = str(obj.properties.get("business_fit") or "Unknown")
            technical_fit = str(obj.properties.get("technical_fit") or "Unknown")
            rows.append(
                ApplicationPortfolioRow(
                    object=obj,
                    risk=metrics.get(obj.id),
                    business_fit=business_fit,
                    technical_fit=technical_fit,
                    strategic_fit=str(obj.properties.get("strategic_fit") or "Unknown"),
                    hosting_model=str(obj.properties.get("hosting_model") or "Not set"),
                    time_quadrant=self._time_quadrant(business_fit, technical_fit),
                )
            )
        if lifecycle:
            rows = [row for row in rows if row.object.lifecycle_stage == lifecycle]
        if risk_band:
            rows = [row for row in rows if row.risk is not None and row.risk.band == risk_band]
        return rows

    def technology_portfolio(self, *, lifecycle: str | None = None, strategic_status: str | None = None) -> list[TechnologyPortfolioRow]:
        technologies = self._objects("technology")
        metrics = self._metric_map("technology_risk")
        rows = [
            TechnologyPortfolioRow(
                object=obj,
                risk=metrics.get(obj.id),
                support_end=self._date(obj.properties.get("vendor_support_end")),
                dependent_applications=self._dependent_applications(obj.id),
            )
            for obj in technologies
        ]
        if lifecycle:
            rows = [row for row in rows if row.object.lifecycle_stage == lifecycle]
        if strategic_status:
            rows = [row for row in rows if str(row.object.properties.get("strategic_status") or "") == strategic_status]
        return rows

    def capability_map(self) -> list[CapabilityNode]:
        capabilities = self._objects("business_capability")
        metrics = self._metric_map("capability_risk")
        nodes = {
            obj.id: CapabilityNode(
                object=obj,
                risk=metrics.get(obj.id),
                supporting_applications=self._supporting_applications(obj.id),
                application_risk=self._capability_application_risk(obj.id),
                technology_risk=self._capability_technology_risk(obj.id),
                maturity=str(obj.properties.get("maturity") or "Unknown"),
                strategic_importance=str(obj.properties.get("strategic_importance") or "Not set"),
            )
            for obj in capabilities
        }
        roots: list[CapabilityNode] = []
        for obj in capabilities:
            parent_id = str(obj.properties.get("parent_capability") or "")
            if parent_id and parent_id in nodes and parent_id != obj.id:
                nodes[parent_id].children.append(nodes[obj.id])
            else:
                roots.append(nodes[obj.id])
        self._sort_capabilities(roots)
        return roots

    def roadmaps(self) -> list[RoadmapItem]:
        rows: list[RoadmapItem] = []
        for obj in self._active_objects():
            key = obj.object_type.key
            if key == "application":
                start = self._date(obj.properties.get("go_live_date")) or obj.valid_from
                end = self._date(obj.properties.get("actual_retirement_date")) or self._date(obj.properties.get("planned_retirement_date")) or obj.valid_until
                if start or end:
                    rows.append(RoadmapItem(obj, "Application", start, end, obj.lifecycle_stage or "Application lifecycle"))
            elif key == "initiative":
                start = self._date(obj.properties.get("start_date")) or obj.valid_from
                end = self._date(obj.properties.get("actual_end_date")) or self._date(obj.properties.get("target_end_date")) or obj.valid_until
                if start or end:
                    rows.append(RoadmapItem(obj, "Initiative", start, end, str(obj.properties.get("status") or "Initiative")))
            elif key == "technology":
                support = self._date(obj.properties.get("vendor_support_end")) or self._date(obj.properties.get("extended_support_end")) or self._date(obj.properties.get("internal_support_end"))
                if support:
                    rows.append(RoadmapItem(obj, "Technology", obj.valid_from, support, obj.lifecycle_stage or "Support horizon"))
            elif obj.valid_from or obj.valid_until:
                rows.append(RoadmapItem(obj, obj.object_type.name, obj.valid_from, obj.valid_until, obj.lifecycle_stage or "Validity"))
        rows.sort(key=lambda item: (item.start or item.end or date.max, item.object.name.lower()))
        return rows

    def _objects(self, object_type_key: str) -> list[ArchitectureObject]:
        return list(
            self.db.scalars(
                select(ArchitectureObject)
                .where(
                    ArchitectureObject.archived_at.is_(None),
                    ArchitectureObject.object_type.has(key=object_type_key),
                )
                .order_by(ArchitectureObject.name)
            ).unique().all()
        )

    def _active_objects(self) -> list[ArchitectureObject]:
        return list(self.db.scalars(select(ArchitectureObject).where(ArchitectureObject.archived_at.is_(None))).unique().all())

    def _metric_map(self, metric_type: str) -> dict[str, ObjectMetric]:
        return {
            metric.object_id: metric
            for metric in self.db.scalars(select(ObjectMetric).where(ObjectMetric.metric_type == metric_type)).all()
        }

    def _dependent_applications(self, technology_id: str) -> int:
        rows = self.db.scalars(
            select(ArchitectureRelationship)
            .where(
                ArchitectureRelationship.target_object_id == technology_id,
                ArchitectureRelationship.archived_at.is_(None),
                ArchitectureRelationship.relationship_type.has(key="uses"),
            )
        ).all()
        app_ids = {row.source_object_id for row in rows}
        if not app_ids:
            return 0
        return len(
            self.db.scalars(
                select(ArchitectureObject.id).where(
                    ArchitectureObject.id.in_(app_ids),
                    ArchitectureObject.archived_at.is_(None),
                    ArchitectureObject.object_type.has(key="application"),
                )
            ).all()
        )


    def _capability_application_ids(self, capability_id: str) -> set[str]:
        return set(
            self.db.scalars(
                select(ArchitectureRelationship.source_object_id).where(
                    ArchitectureRelationship.target_object_id == capability_id,
                    ArchitectureRelationship.archived_at.is_(None),
                    ArchitectureRelationship.relationship_type.has(key="supports"),
                )
            ).all()
        )

    def _capability_application_risk(self, capability_id: str) -> int:
        app_ids = self._capability_application_ids(capability_id)
        if not app_ids:
            return 0
        scores = self.db.scalars(
            select(ObjectMetric.score).where(
                ObjectMetric.object_id.in_(app_ids), ObjectMetric.metric_type == "application_risk"
            )
        ).all()
        return max(scores, default=0)

    def _capability_technology_risk(self, capability_id: str) -> int:
        app_ids = self._capability_application_ids(capability_id)
        if not app_ids:
            return 0
        tech_ids = set(
            self.db.scalars(
                select(ArchitectureRelationship.target_object_id).where(
                    ArchitectureRelationship.source_object_id.in_(app_ids),
                    ArchitectureRelationship.archived_at.is_(None),
                    ArchitectureRelationship.relationship_type.has(key="uses"),
                )
            ).all()
        )
        if not tech_ids:
            return 0
        scores = self.db.scalars(
            select(ObjectMetric.score).where(
                ObjectMetric.object_id.in_(tech_ids), ObjectMetric.metric_type == "technology_risk"
            )
        ).all()
        return max(scores, default=0)

    def _supporting_applications(self, capability_id: str) -> int:
        return len(
            set(
                self.db.scalars(
                    select(ArchitectureRelationship.source_object_id).where(
                        ArchitectureRelationship.target_object_id == capability_id,
                        ArchitectureRelationship.archived_at.is_(None),
                        ArchitectureRelationship.relationship_type.has(key="supports"),
                    )
                ).all()
            )
        )

    @staticmethod
    def _time_quadrant(business_fit: str, technical_fit: str) -> str:
        business = FIT_VALUE.get(business_fit, 2)
        technical = FIT_VALUE.get(technical_fit, 2)
        if business >= 3 and technical >= 3:
            return "Invest"
        if business >= 3 and technical < 3:
            return "Migrate"
        if business < 3 and technical >= 3:
            return "Tolerate"
        return "Eliminate"

    @classmethod
    def _sort_capabilities(cls, nodes: list[CapabilityNode]) -> None:
        nodes.sort(key=lambda node: node.object.name.lower())
        for node in nodes:
            cls._sort_capabilities(node.children)

    @staticmethod
    def _date(value: object) -> date | None:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None
