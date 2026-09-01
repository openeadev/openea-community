from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.analytics import ObjectMetric
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship
from app.services.impact_service import ImpactService

RISK_BANDS = ((24, "Low"), (49, "Moderate"), (74, "High"), (100, "Critical"))
FIT_RISK = {"Excellent": 0, "Good": 20, "Fair": 50, "Poor": 80, "Unknown": 40}
APP_LIFECYCLE_RISK = {"Proposed": 10, "Planned": 10, "Development": 15, "Active": 10, "Tolerated": 50, "Sunset": 80, "Retired": 100}
TECH_STRATEGY_RISK = {"Adopt": 0, "Strategic": 5, "Tolerate": 30, "Contain": 50, "Migrate": 75, "Retire": 100}
TECH_LIFECYCLE_RISK = {"Emerging": 0, "Current": 5, "Aging": 50, "End of Support": 100, "Retired": 100}
CRITICALITY_MULTIPLIER = {"Low": 0.75, "Medium": 1.0, "High": 1.15, "Mission Critical": 1.30}
MATURITY_RISK = {"Initial": 100, "Developing": 75, "Defined": 50, "Managed": 25, "Optimized": 0}
CONFIDENCE_SCORE = {"Unknown": 20, "Low": 40, "Medium": 60, "High": 80, "Confirmed": 100}

EXPECTED_RELATIONSHIPS = {
    "application": {"supports", "uses"},
    "technology": set(),
    "business_capability": {"supports"},
    "business_process": {"supports", "realizes"},
    "data_object": {"system_of_record_for"},
}
RECOMMENDED_FIELDS = {
    "application": ["technical_fit", "business_fit", "strategic_fit", "hosting_model"],
    "technology": ["strategic_status", "vendor_support_end", "vendor", "product"],
    "business_capability": ["maturity", "strategic_importance"],
}

METRIC_GUIDANCE = {
    "data_quality": {
        "label": "Data Quality",
        "description": "Measures how complete, owned, connected, current, and trustworthy this repository record is.",
        "direction": "Higher is better. A low score indicates missing or stale architecture information that can usually be corrected in the repository.",
        "component_note": "Component values are quality/coverage scores. Higher values improve Data Quality.",
    },
    "application_risk": {
        "label": "Application Risk",
        "description": "Estimates application concern from technology exposure, technical fit, lifecycle, dependencies, data quality, review freshness, and criticality.",
        "direction": "Lower is better. Higher scores indicate more conditions that deserve architecture attention.",
        "component_note": "Component values are risk signals. Higher values increase Application Risk before the criticality multiplier is applied.",
    },
    "technology_risk": {
        "label": "Technology Risk",
        "description": "Estimates technology concern from lifecycle, internal strategy, vendor support horizon, review freshness, and data quality.",
        "direction": "Lower is better. Higher scores indicate greater lifecycle, support, strategy, or information-quality concern.",
        "component_note": "Component values are risk signals. Higher values increase Technology Risk.",
    },
    "capability_risk": {
        "label": "Capability Risk",
        "description": "Estimates business-capability concern from supporting applications, technology exposure, support concentration, maturity, and data quality.",
        "direction": "Lower is better. Higher scores indicate greater application, technology, resilience, maturity, or information-quality concern.",
        "component_note": "Component values are risk signals. Higher values increase Capability Risk.",
    },
    "impact_severity": {
        "label": "Impact Severity",
        "description": "Measures the breadth and significance of repository reach within three relationship hops.",
        "direction": "This is not a quality score. A high value can be completely valid for a central or critical architecture object.",
        "component_note": "Component values are impact signals. Higher values indicate broader or more significant architectural reach.",
    },
}

HEALTH_DIMENSIONS = {
    "completeness": {
        "label": "Completeness",
        "description": "Measures whether required fields defined by each object type are populated.",
    },
    "freshness": {
        "label": "Freshness",
        "description": "Measures whether architecture records have current review dates or sufficiently recent completed reviews.",
    },
    "ownership": {
        "label": "Ownership",
        "description": "Measures whether records have an owner organization, owner role, or recognized object-specific owner field.",
    },
    "relationship_coverage": {
        "label": "Relationship coverage",
        "description": "Measures whether records have the expected governed relationship types for their object type.",
    },
    "governance": {
        "label": "Governance",
        "description": "Measures the percentage of active repository records in an approved or accepted governance state.",
    },
}



@dataclass
class RepositoryHealth:
    score: int
    band: str
    object_count: int
    metrics_count: int
    completeness: int
    freshness: int
    ownership: int
    relationship_coverage: int
    governance: int


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def band(score: int) -> str:
        for maximum, band in RISK_BANDS:
            if score <= maximum:
                return band
        return "Critical"

    @staticmethod
    def _bounded(value: float) -> int:
        return max(0, min(100, int(round(value))))

    def calculate_all(self) -> int:
        objects = list(self.db.scalars(select(ArchitectureObject).where(ArchitectureObject.archived_at.is_(None))).unique().all())
        calculated = 0
        # Data quality first because risk formulas depend on it.
        for obj in objects:
            self._persist(obj, "data_quality", *self.calculate_data_quality(obj))
            calculated += 1
        for obj in objects:
            key = obj.object_type.key
            if key == "technology":
                self._persist(obj, "technology_risk", *self.calculate_technology_risk(obj))
                calculated += 1
        for obj in objects:
            if obj.object_type.key == "application":
                self._persist(obj, "application_risk", *self.calculate_application_risk(obj))
                calculated += 1
        for obj in objects:
            if obj.object_type.key == "business_capability":
                self._persist(obj, "capability_risk", *self.calculate_capability_risk(obj))
                calculated += 1
        for obj in objects:
            self._persist(obj, "impact_severity", *self.calculate_impact_severity(obj))
            calculated += 1
        self.db.commit()
        return calculated

    def _persist(self, obj: ArchitectureObject, metric_type: str, score: int, explanation: dict[str, object]) -> ObjectMetric:
        metric = self.db.scalar(select(ObjectMetric).where(ObjectMetric.object_id == obj.id, ObjectMetric.metric_type == metric_type))
        if metric is None:
            metric = ObjectMetric(object_id=obj.id, metric_type=metric_type, score=score, band=self.band(score), explanation=explanation)
            self.db.add(metric)
        else:
            metric.score = score
            metric.band = self.band(score)
            metric.explanation = explanation
            metric.calculated_at = datetime.now(timezone.utc)
        self.db.flush()
        return metric

    def metric(self, object_id: str, metric_type: str) -> ObjectMetric | None:
        return self.db.scalar(select(ObjectMetric).where(ObjectMetric.object_id == object_id, ObjectMetric.metric_type == metric_type))

    def metrics_for_object(self, object_id: str) -> list[ObjectMetric]:
        return list(self.db.scalars(select(ObjectMetric).where(ObjectMetric.object_id == object_id).order_by(ObjectMetric.metric_type)).all())

    def metric_view(self, metric: ObjectMetric) -> dict[str, object]:
        guidance = METRIC_GUIDANCE.get(
            metric.metric_type,
            {
                "label": metric.metric_type.replace("_", " ").title(),
                "description": "Deterministic metric calculated from the current repository state.",
                "direction": "Review the formula and component values to interpret this metric.",
                "component_note": "Component values are the deterministic inputs persisted with this metric.",
            },
        )
        return {
            "metric": metric,
            "label": guidance["label"],
            "description": guidance["description"],
            "direction": guidance["direction"],
            "component_note": guidance["component_note"],
            "recommendations": self._metric_recommendations(metric),
            "actions": self._metric_actions(metric),
        }

    def _metric_recommendations(self, metric: ObjectMetric) -> list[str]:
        explanation = metric.explanation or {}
        components = explanation.get("components", {})
        missing = explanation.get("missing", [])
        recommendations: list[str] = []

        if metric.metric_type == "data_quality":
            if missing:
                recommendations.append("Correct the listed missing or stale repository information where the architecture evidence supports the change.")
            if int(components.get("ownership", 100)) < 100:
                recommendations.append("Assign an owner organization, owner role, or supported object-specific owner field.")
            if int(components.get("relationship_coverage", 100)) < 100:
                recommendations.append("Add the expected governed relationships that accurately describe this object.")
            if int(components.get("review_freshness", 100)) < 100:
                recommendations.append("Complete or schedule a current architecture review from the Lifecycle tab.")
            if int(components.get("source_confidence", 100)) < 100:
                recommendations.append("Raise confidence only when stronger evidence supports the repository record.")
            if not recommendations:
                recommendations.append("No data-quality remediation is indicated by the current calculation. Continue normal review and governance maintenance.")

        elif metric.metric_type == "application_risk":
            if int(components.get("technology_risk", 0)) > 0:
                recommendations.append("Review the application's Technology relationships and remediate high-risk technologies through upgrade, migration, or replacement where appropriate.")
            if int(components.get("technical_fit", 0)) > 0:
                recommendations.append("Review Technical Fit. Improve the architecture where needed, then update the field only when the evidence supports a better fit rating.")
            if int(components.get("lifecycle_risk", 0)) >= 50:
                recommendations.append("Review the application lifecycle and any planned modernization or retirement activity.")
            if int(components.get("dependency_risk", 0)) > 0:
                recommendations.append("Review application dependencies. Reduce unnecessary coupling when architecturally justified; do not remove accurate relationships merely to lower the score.")
            if int(components.get("data_quality_risk", 0)) > 0:
                recommendations.append("Improve the application's Data Quality inputs, including ownership, expected relationships, required/recommended fields, and confidence.")
            if int(components.get("review_freshness", 0)) > 0:
                recommendations.append("Complete or schedule a current architecture review from the Lifecycle tab.")

        elif metric.metric_type == "technology_risk":
            if int(components.get("vendor_lifecycle", 0)) > 0:
                recommendations.append("Verify the technology lifecycle. For aging or unsupported technology, plan upgrade, migration, containment, or retirement as appropriate.")
            if int(components.get("internal_strategy", 0)) > 0:
                recommendations.append("Review Strategic Status and align use of the technology with the organization's approved technology strategy.")
            if int(components.get("support_horizon", 0)) > 0:
                recommendations.append("Verify Vendor Support End and plan remediation before support expires.")
            if int(components.get("review_freshness", 0)) > 0:
                recommendations.append("Complete or schedule a current architecture review from the Lifecycle tab.")
            if int(components.get("data_quality_risk", 0)) > 0:
                recommendations.append("Improve the technology record's Data Quality inputs and supporting evidence.")

        elif metric.metric_type == "capability_risk":
            if int(components.get("supporting_application_risk", 0)) > 0:
                recommendations.append("Review the applications supporting this capability and remediate the highest application risks first.")
            if int(components.get("technology_exposure", 0)) > 0:
                recommendations.append("Trace supporting applications to their technologies and address material technology risk.")
            if int(components.get("single_point_of_failure", 0)) > 0:
                recommendations.append("The capability has a single supporting application. Evaluate resilience, recovery, substitution, or additional support where the business need justifies it.")
            if int(components.get("application_redundancy", 0)) > 0:
                recommendations.append("Review the number of supporting applications for rationalization or intentional resilience. This signal is not proof of duplication by itself.")
            if int(components.get("capability_maturity", 0)) > 0:
                recommendations.append("Review capability maturity and improve the operating model before changing the maturity rating.")
            if int(components.get("data_quality_risk", 0)) > 0:
                recommendations.append("Improve the capability record's Data Quality inputs and expected relationships.")

        elif metric.metric_type == "impact_severity":
            recommendations.extend([
                "Validate that the relationships and criticality values driving the reach are accurate.",
                "Use a high score to prioritize change analysis, dependency coordination, testing, and recovery planning; a high Impact Severity score is not automatically a defect.",
                "Reduce unnecessary dependencies only as a real architecture improvement, not simply to lower the metric.",
            ])

        if not recommendations:
            recommendations.append("Review the current inputs and component values. Change repository data only when it reflects a real architecture change or better evidence.")
        return recommendations

    @staticmethod
    def _metric_actions(metric: ObjectMetric) -> list[dict[str, str]]:
        object_id = metric.object_id
        actions = [
            {"label": "Open object", "url": f"/explore/{object_id}"},
            {"label": "Review relationships", "url": f"/explore/{object_id}?tab=relationships"},
            {"label": "Review lifecycle", "url": f"/explore/{object_id}?tab=lifecycle"},
        ]
        if metric.metric_type != "impact_severity":
            actions.insert(1, {"label": "Edit object", "url": f"/explore/{object_id}/edit"})
        if metric.metric_type == "impact_severity":
            actions.append({"label": "Analyze impact", "url": f"/impact/{object_id}"})
        return actions

    def calculate_data_quality(self, obj: ArchitectureObject) -> tuple[int, dict[str, object]]:
        schema = obj.object_type.schema_definition or {}
        required_names = [name for name, spec in schema.items() if isinstance(spec, dict) and spec.get("required")]
        required_present = sum(1 for name in required_names if self._present(obj.properties.get(name)))
        required_score = 100 if not required_names else 100 * required_present / len(required_names)

        recommended_names = RECOMMENDED_FIELDS.get(obj.object_type.key, [])
        recommended_present = sum(1 for name in recommended_names if self._present(obj.properties.get(name)))
        recommended_score = 100 if not recommended_names else 100 * recommended_present / len(recommended_names)

        ownership_score = 100 if self._has_owner(obj) else 0
        relationship_score = self._relationship_coverage(obj)
        freshness_score = 100 - self._review_freshness_risk(obj)
        confidence_score = CONFIDENCE_SCORE.get(obj.confidence or "Unknown", 20)
        score = self._bounded(
            required_score * 0.30
            + recommended_score * 0.15
            + ownership_score * 0.15
            + relationship_score * 0.20
            + freshness_score * 0.15
            + confidence_score * 0.05
        )
        explanation = {
            "formula": "required 30% + recommended 15% + ownership 15% + relationship coverage 20% + review freshness 15% + source confidence 5%",
            "components": {
                "required_fields": self._bounded(required_score),
                "recommended_fields": self._bounded(recommended_score),
                "ownership": ownership_score,
                "relationship_coverage": relationship_score,
                "review_freshness": freshness_score,
                "source_confidence": confidence_score,
            },
            "missing": self._missing_quality_items(obj, required_names, recommended_names),
        }
        return score, explanation

    def calculate_technology_risk(self, obj: ArchitectureObject) -> tuple[int, dict[str, object]]:
        lifecycle = str(obj.lifecycle_stage or obj.properties.get("lifecycle_stage") or "Current")
        vendor_lifecycle = TECH_LIFECYCLE_RISK.get(lifecycle, 30)
        strategy = str(obj.properties.get("strategic_status") or "Tolerate")
        strategy_risk = TECH_STRATEGY_RISK.get(strategy, 30)
        support_end = self._date_value(obj.properties.get("vendor_support_end"))
        horizon = self._support_horizon_risk(support_end)
        review = self._review_freshness_risk(obj)
        dq = self.metric(obj.id, "data_quality")
        dq_risk = 100 - (dq.score if dq else self.calculate_data_quality(obj)[0])
        score = self._bounded(vendor_lifecycle * 0.30 + strategy_risk * 0.30 + horizon * 0.25 + review * 0.10 + dq_risk * 0.05)
        return score, {
            "formula": "vendor lifecycle 30% + internal strategy 30% + support horizon 25% + review freshness 10% + data quality risk 5%",
            "components": {"vendor_lifecycle": vendor_lifecycle, "internal_strategy": strategy_risk, "support_horizon": horizon, "review_freshness": review, "data_quality_risk": dq_risk},
            "inputs": {"lifecycle": lifecycle, "strategic_status": strategy, "vendor_support_end": support_end.isoformat() if support_end else None},
        }

    def calculate_application_risk(self, obj: ArchitectureObject) -> tuple[int, dict[str, object]]:
        tech_metrics = self._related_technology_metrics(obj)
        technology_risk = max((metric.score for metric in tech_metrics), default=30)
        tech_fit = str(obj.properties.get("technical_fit") or "Unknown")
        fit_risk = FIT_RISK.get(tech_fit, 40)
        lifecycle = str(obj.lifecycle_stage or obj.properties.get("lifecycle_stage") or "Active")
        lifecycle_risk = APP_LIFECYCLE_RISK.get(lifecycle, 40)
        dependency_count = self._application_dependency_count(obj)
        dependency_risk = 0 if dependency_count == 0 else 25 if dependency_count <= 2 else 50 if dependency_count <= 5 else 75
        dq = self.metric(obj.id, "data_quality")
        dq_risk = 100 - (dq.score if dq else self.calculate_data_quality(obj)[0])
        review = self._review_freshness_risk(obj)
        raw = technology_risk * 0.30 + fit_risk * 0.20 + lifecycle_risk * 0.15 + dependency_risk * 0.15 + dq_risk * 0.10 + review * 0.10
        multiplier = CRITICALITY_MULTIPLIER.get(obj.criticality or "Medium", 1.0)
        score = self._bounded(raw * multiplier)
        return score, {
            "formula": "(technology 30% + technical fit 20% + lifecycle 15% + dependency 15% + data quality risk 10% + review freshness 10%) × criticality multiplier",
            "components": {"technology_risk": technology_risk, "technical_fit": fit_risk, "lifecycle_risk": lifecycle_risk, "dependency_risk": dependency_risk, "data_quality_risk": dq_risk, "review_freshness": review},
            "criticality_multiplier": multiplier,
            "inputs": {"technical_fit": tech_fit, "lifecycle": lifecycle, "dependency_count": dependency_count, "material_technology_count": len(tech_metrics)},
        }

    def calculate_capability_risk(self, obj: ArchitectureObject) -> tuple[int, dict[str, object]]:
        apps = self._supporting_applications(obj)
        app_risks = [self.metric(app.id, "application_risk") for app in apps]
        supporting_risk = max((metric.score for metric in app_risks if metric), default=100 if not apps else 40)
        technology_exposure = 0
        for app in apps:
            technology_exposure = max(technology_exposure, max((m.score for m in self._related_technology_metrics(app)), default=0))
        redundancy = 100 if not apps else 0 if len(apps) == 1 else 30 if len(apps) <= 3 else 60
        single_point = 100 if len(apps) == 1 else 0
        maturity = str(obj.properties.get("maturity") or "Unknown")
        maturity_risk = MATURITY_RISK.get(maturity, 50)
        dq = self.metric(obj.id, "data_quality")
        dq_risk = 100 - (dq.score if dq else self.calculate_data_quality(obj)[0])
        score = self._bounded(supporting_risk * 0.40 + technology_exposure * 0.20 + redundancy * 0.10 + single_point * 0.15 + maturity_risk * 0.10 + dq_risk * 0.05)
        return score, {
            "formula": "supporting application risk 40% + technology exposure 20% + application redundancy 10% + single point of failure 15% + maturity 10% + data quality risk 5%",
            "components": {"supporting_application_risk": supporting_risk, "technology_exposure": technology_exposure, "application_redundancy": redundancy, "single_point_of_failure": single_point, "capability_maturity": maturity_risk, "data_quality_risk": dq_risk},
            "inputs": {"supporting_application_count": len(apps), "maturity": maturity},
        }

    def calculate_impact_severity(self, obj: ArchitectureObject) -> tuple[int, dict[str, object]]:
        analysis = ImpactService(self.db).analyze(obj.id, depth=3)
        direct = [item for item in analysis.results if item.depth == 1]
        critical = [item for item in analysis.results if item.object.criticality in {"High", "Mission Critical"}]
        business_reach = len({item.object.id for item in analysis.results if item.object.object_type.domain == "Business"})
        max_depth = max((item.depth for item in analysis.results), default=0)
        direct_score = min(100, len(direct) * 20)
        critical_score = min(100, len(critical) * 25)
        reach_score = min(100, business_reach * 20)
        depth_score = {0: 0, 1: 25, 2: 60, 3: 100}.get(max_depth, 100)
        strategic = 100 if str(obj.properties.get("strategic_importance", "")).lower() in {"high", "critical", "mission critical"} else 50 if obj.criticality in {"High", "Mission Critical"} else 20
        score = self._bounded(direct_score * 0.25 + critical_score * 0.25 + reach_score * 0.20 + depth_score * 0.15 + strategic * 0.15)
        return score, {
            "formula": "direct dependents 25% + critical dependents 25% + business reach 20% + dependency depth 15% + strategic importance 15%",
            "components": {"direct_dependents": direct_score, "critical_dependents": critical_score, "business_reach": reach_score, "dependency_depth": depth_score, "strategic_importance": strategic},
            "inputs": {"direct_count": len(direct), "critical_count": len(critical), "business_object_count": business_reach, "maximum_depth": max_depth},
        }

    def repository_health(self) -> RepositoryHealth:
        objects = list(self.db.scalars(select(ArchitectureObject).where(ArchitectureObject.archived_at.is_(None))).unique().all())
        dq_metrics = list(self.db.scalars(select(ObjectMetric).where(ObjectMetric.metric_type == "data_quality")).all())
        score = self._bounded(sum(m.score for m in dq_metrics) / len(dq_metrics)) if dq_metrics else 0
        completeness_values = [int(m.explanation.get("components", {}).get("required_fields", 0)) for m in dq_metrics]
        freshness_values = [int(m.explanation.get("components", {}).get("review_freshness", 0)) for m in dq_metrics]
        ownership_values = [int(m.explanation.get("components", {}).get("ownership", 0)) for m in dq_metrics]
        rel_values = [int(m.explanation.get("components", {}).get("relationship_coverage", 0)) for m in dq_metrics]
        governance = self._bounded(100 * sum(1 for obj in objects if obj.governance_status in {"Approved", "Accepted"}) / len(objects)) if objects else 0
        def average(values: list[int]) -> int:
            return self._bounded(sum(values) / len(values)) if values else 0

        return RepositoryHealth(
            score,
            self.band(score),
            len(objects),
            len(dq_metrics),
            average(completeness_values),
            average(freshness_values),
            average(ownership_values),
            average(rel_values),
            governance,
        )

    def repository_health_dimension(self, dimension: str) -> dict[str, object]:
        definition = HEALTH_DIMENSIONS.get(dimension)
        if definition is None:
            raise ValueError("Unknown repository health dimension")

        objects = list(
            self.db.scalars(
                select(ArchitectureObject)
                .where(ArchitectureObject.archived_at.is_(None))
                .order_by(ArchitectureObject.name)
            ).unique().all()
        )
        metric_by_object = {
            metric.object_id: metric
            for metric in self.db.scalars(
                select(ObjectMetric).where(ObjectMetric.metric_type == "data_quality")
            ).all()
        }
        items: list[dict[str, object]] = []
        for obj in objects:
            score, reason = self._health_dimension_object_result(obj, dimension, metric_by_object.get(obj.id))
            if score < 100:
                items.append({"object": obj, "score": score, "reason": reason})

        health = self.repository_health()
        overall = int(getattr(health, dimension))
        return {
            "key": dimension,
            "label": definition["label"],
            "description": definition["description"],
            "score": overall,
            "affected_count": len(items),
            "object_count": len(objects),
            "items": items,
        }

    def _health_dimension_object_result(
        self,
        obj: ArchitectureObject,
        dimension: str,
        metric: ObjectMetric | None,
    ) -> tuple[int, str]:
        components = metric.explanation.get("components", {}) if metric else {}
        if dimension == "completeness":
            score = int(components.get("required_fields", self.calculate_data_quality(obj)[1]["components"]["required_fields"]))
            schema = obj.object_type.schema_definition or {}
            required = [
                name
                for name, spec in schema.items()
                if isinstance(spec, dict) and spec.get("required")
            ]
            missing = [name.replace("_", " ").title() for name in required if not self._present(obj.properties.get(name))]
            reason = "Missing required fields: " + ", ".join(missing) if missing else "Required-field metric is not current; recalculate metrics."
            return score, reason

        if dimension == "freshness":
            score = int(components.get("review_freshness", 100 - self._review_freshness_risk(obj)))
            today = date.today()
            if obj.next_review_date and obj.next_review_date < today:
                return score, f"Review overdue since {obj.next_review_date.isoformat()}."
            if obj.next_review_date:
                return score, f"Next review is {obj.next_review_date.isoformat()}."
            if obj.last_reviewed_date:
                return score, f"No next review date; last reviewed {obj.last_reviewed_date.isoformat()}."
            return score, "No completed review or next review date."

        if dimension == "ownership":
            score = int(components.get("ownership", 100 if self._has_owner(obj) else 0))
            return score, "No owner organization, owner role, or recognized object-specific owner field."

        if dimension == "relationship_coverage":
            score = int(components.get("relationship_coverage", self._relationship_coverage(obj)))
            expected = EXPECTED_RELATIONSHIPS.get(obj.object_type.key) or set()
            rows = self.db.scalars(
                select(ArchitectureRelationship).where(
                    or_(
                        ArchitectureRelationship.source_object_id == obj.id,
                        ArchitectureRelationship.target_object_id == obj.id,
                    ),
                    ArchitectureRelationship.archived_at.is_(None),
                )
            ).unique().all()
            present = {rel.relationship_type.key for rel in rows}
            missing = sorted(expected - present)
            reason = "Missing expected relationships: " + ", ".join(missing) if missing else "Relationship-coverage metric is not current; recalculate metrics."
            return score, reason

        score = 100 if obj.governance_status in {"Approved", "Accepted"} else 0
        return score, f"Governance status is {obj.governance_status or 'Not set'}; Approved or Accepted counts as covered."

    def _related_technology_metrics(self, app: ArchitectureObject) -> list[ObjectMetric]:
        tech_ids = self.db.scalars(
            select(ArchitectureRelationship.target_object_id)
            .where(ArchitectureRelationship.source_object_id == app.id, ArchitectureRelationship.archived_at.is_(None))
            .join(ArchitectureRelationship.relationship_type)
            .where(ArchitectureRelationship.relationship_type.has(key="uses"))
        ).all()
        if not tech_ids:
            return []
        return list(self.db.scalars(select(ObjectMetric).where(ObjectMetric.object_id.in_(tech_ids), ObjectMetric.metric_type == "technology_risk")).all())

    def _supporting_applications(self, capability: ArchitectureObject) -> list[ArchitectureObject]:
        return list(self.db.scalars(
            select(ArchitectureObject)
            .join(ArchitectureRelationship, ArchitectureRelationship.source_object_id == ArchitectureObject.id)
            .where(ArchitectureRelationship.target_object_id == capability.id, ArchitectureRelationship.archived_at.is_(None), ArchitectureRelationship.relationship_type.has(key="supports"), ArchitectureObject.archived_at.is_(None), ArchitectureObject.object_type.has(key="application"))
        ).unique().all())

    def _application_dependency_count(self, app: ArchitectureObject) -> int:
        return int(self.db.scalar(select(func.count()).select_from(ArchitectureRelationship).where(ArchitectureRelationship.source_object_id == app.id, ArchitectureRelationship.archived_at.is_(None), ArchitectureRelationship.relationship_type.has(key="depends_on"))) or 0)

    def _relationship_coverage(self, obj: ArchitectureObject) -> int:
        expected = EXPECTED_RELATIONSHIPS.get(obj.object_type.key)
        if not expected:
            return 100
        rows = self.db.scalars(select(ArchitectureRelationship).where(or_(ArchitectureRelationship.source_object_id == obj.id, ArchitectureRelationship.target_object_id == obj.id), ArchitectureRelationship.archived_at.is_(None))).unique().all()
        present = {rel.relationship_type.key for rel in rows}
        return self._bounded(100 * len(expected.intersection(present)) / len(expected))

    def _has_owner(self, obj: ArchitectureObject) -> bool:
        if obj.owner_organization_id or obj.owner_role_id:
            return True
        return any(self._present(obj.properties.get(key)) for key in ("business_owner", "technical_owner", "service_owner", "process_owner", "data_owner", "decision_owner", "owner"))

    def _missing_quality_items(self, obj: ArchitectureObject, required: list[str], recommended: list[str]) -> list[str]:
        missing = [name.replace("_", " ").title() for name in required + recommended if not self._present(obj.properties.get(name))]
        if not self._has_owner(obj):
            missing.append("Owner")
        if self._review_freshness_risk(obj) >= 75:
            missing.append("Current review")
        if self._relationship_coverage(obj) < 100:
            missing.append("Expected relationships")
        return missing

    def _review_freshness_risk(self, obj: ArchitectureObject) -> int:
        today = date.today()
        if obj.next_review_date:
            if obj.next_review_date < today:
                return 100
            days = (obj.next_review_date - today).days
            return 60 if days <= 30 else 20 if days <= 90 else 0
        if obj.last_reviewed_date:
            days = (today - obj.last_reviewed_date).days
            return 20 if days <= 180 else 60 if days <= 365 else 100
        return 75

    @staticmethod
    def _support_horizon_risk(end: date | None) -> int:
        if end is None:
            return 30
        months = (end - date.today()).days / 30.44
        if months < 0:
            return 100
        if months < 6:
            return 85
        if months < 12:
            return 60
        if months < 24:
            return 30
        if months < 36:
            return 10
        return 0

    @staticmethod
    def _date_value(value: object) -> date | None:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def _present(value: object) -> bool:
        return value not in (None, "", [], {})
