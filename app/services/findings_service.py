from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.findings_rules import STANDARD_FINDING_RULES
from app.models.analytics import ObjectMetric
from app.models.findings import Finding, RuleDefinition
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship
from app.models.user import User
from app.services.audit_service import AuditService

ACTIVE_FINDING_STATUSES = {"Open", "Acknowledged", "Accepted", "Remediation Planned"}
FINDING_STATUSES = ("Open", "Acknowledged", "Accepted", "Remediation Planned", "Resolved", "Dismissed")


class FindingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def seed_rules(self) -> int:
        count = 0
        for spec in STANDARD_FINDING_RULES:
            rule = self.db.scalar(select(RuleDefinition).where(RuleDefinition.rule_id == spec["rule_id"]))
            if rule is None:
                rule = RuleDefinition(
                    rule_id=str(spec["rule_id"]),
                    name=str(spec["name"]),
                    description=str(spec["description"]),
                    rule_type=str(spec["rule_type"]),
                    severity=str(spec["severity"]),
                    config=dict(spec["config"]),
                    enabled=True,
                    is_system=True,
                )
                self.db.add(rule)
                count += 1
        self.db.commit()
        return count

    def evaluate_all(self) -> int:
        now = datetime.now(timezone.utc)
        active_keys: set[tuple[str, str]] = set()
        rules = list(self.db.scalars(select(RuleDefinition).where(RuleDefinition.enabled.is_(True), RuleDefinition.archived_at.is_(None))).all())
        for rule in rules:
            for obj, evidence in self._matches(rule):
                active_keys.add((rule.id, obj.id))
                finding = self.db.scalar(select(Finding).where(Finding.rule_definition_id == rule.id, Finding.related_object_id == obj.id))
                if finding is None:
                    finding = Finding(
                        finding_type=rule.rule_type,
                        severity=rule.severity,
                        title=f"{rule.name}: {obj.name}",
                        description=rule.description,
                        rule_definition_id=rule.id,
                        related_object_id=obj.id,
                        evidence=evidence,
                    )
                    self.db.add(finding)
                else:
                    finding.last_evaluated_at = now
                    finding.severity = rule.severity
                    finding.title = f"{rule.name}: {obj.name}"
                    finding.description = rule.description
                    finding.evidence = evidence
                    if finding.status == "Resolved":
                        finding.status = "Open"
                        finding.resolved_at = None
                        finding.resolution_notes = None
        self.db.flush()
        for finding in self.db.scalars(select(Finding)).unique().all():
            finding.last_evaluated_at = now
            key = (finding.rule_definition_id, finding.related_object_id)
            if key not in active_keys and finding.status in ACTIVE_FINDING_STATUSES:
                finding.status = "Resolved"
                finding.resolved_at = now
                finding.resolution_notes = "Condition no longer detected by rule evaluation."
        self.db.commit()
        return len(active_keys)

    def update_status(self, finding: Finding, *, status: str, actor: User, notes: str = "", dismissal_reason: str = "", assigned_user_id: str | None = None, assigned_role: str | None = None) -> Finding:
        if status not in FINDING_STATUSES:
            raise ValueError("Invalid finding status")
        if status == "Dismissed" and not dismissal_reason.strip():
            raise ValueError("Dismissal requires a reason")
        before = self._state(finding)
        finding.status = status
        finding.assigned_user_id = assigned_user_id or None
        finding.assigned_role = assigned_role.strip() if assigned_role else None
        if status == "Resolved":
            finding.resolved_at = datetime.now(timezone.utc)
            finding.resolution_notes = notes.strip() or "Resolved by user."
        elif status == "Dismissed":
            finding.resolved_at = datetime.now(timezone.utc)
            finding.dismissal_reason = dismissal_reason.strip()
            finding.resolution_notes = notes.strip() or None
        else:
            finding.resolved_at = None
            finding.resolution_notes = notes.strip() or None
            finding.dismissal_reason = None
        AuditService(self.db).record(action="FindingStatusChanged", entity_type="finding", entity_id=finding.id, actor=actor, before=before, after=self._state(finding))
        self.db.commit()
        return finding

    def set_rule_enabled(self, rule: RuleDefinition, enabled: bool, actor: User) -> None:
        if rule.archived_at is not None:
            raise ValueError("Archived rules cannot be enabled")
        before = {"enabled": rule.enabled}
        rule.enabled = enabled
        rule.updated_by = actor.id
        AuditService(self.db).record(action="FindingRuleUpdated", entity_type="rule_definition", entity_id=rule.id, actor=actor, before=before, after={"enabled": enabled})
        self.db.commit()

    def _matches(self, rule: RuleDefinition) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        handler = getattr(self, f"_rule_{rule.rule_type}", None)
        if handler is None:
            return []
        return handler(rule.config)

    def _objects(self, config: dict[str, object]) -> list[ArchitectureObject]:
        stmt = select(ArchitectureObject).where(ArchitectureObject.archived_at.is_(None))
        keys = config.get("object_types") or ([config["object_type"]] if config.get("object_type") else [])
        if keys:
            stmt = stmt.where(ArchitectureObject.object_type.has(key=str(keys[0]))) if len(keys) == 1 else stmt.where(ArchitectureObject.object_type.has())
        objects = list(self.db.scalars(stmt).unique().all())
        if keys:
            objects = [obj for obj in objects if obj.object_type.key in set(str(k) for k in keys)]
        return objects

    @staticmethod
    def _value(obj: ArchitectureObject, name: str) -> object:
        return getattr(obj, name, None) if hasattr(obj, name) else obj.properties.get(name)

    def _rule_missing_field(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        out = []
        for obj in self._objects(config):
            if "fields_any" in config:
                fields = [str(v) for v in config["fields_any"]]
                missing = all(not self._value(obj, f) for f in fields)
                evidence = {"fields": fields}
            else:
                field = str(config.get("field") or config.get("property"))
                missing = not self._value(obj, field)
                evidence = {"field": field}
            if missing:
                out.append((obj, evidence))
        return out

    def _rule_date_threshold(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        today = date.today()
        out = []
        for obj in self._objects(config):
            raw = self._value(obj, str(config["field"]))
            try:
                value = raw if isinstance(raw, date) else date.fromisoformat(str(raw)) if raw else None
            except ValueError:
                value = None
            if value is None:
                continue
            days = (value - today).days
            mode = config.get("mode")
            matched = days < 0 if mode == "past" else 0 <= days <= int(config.get("days", 0))
            if matched:
                out.append((obj, {"date": value.isoformat(), "days_until": days}))
        return out

    def _count_relationships(self, obj: ArchitectureObject, config: dict[str, object]) -> int:
        stmt = select(ArchitectureRelationship).where(ArchitectureRelationship.archived_at.is_(None))
        direction = config.get("direction", "outbound")
        if direction == "inbound":
            stmt = stmt.where(ArchitectureRelationship.target_object_id == obj.id)
        else:
            stmt = stmt.where(ArchitectureRelationship.source_object_id == obj.id)
        relationships = list(self.db.scalars(stmt).unique().all())
        names = set(str(x) for x in config.get("relationship_names", []))
        rel_name = config.get("relationship")
        if rel_name:
            names.add(str(rel_name))
        if names:
            relationships = [r for r in relationships if r.relationship_type.name in names or r.relationship_type.key in names]
        source_type = config.get("source_type")
        target_type = config.get("target_type")
        if source_type:
            relationships = [r for r in relationships if r.source_object.object_type.key == source_type]
        if target_type:
            relationships = [r for r in relationships if r.target_object.object_type.key == target_type]
        return len(relationships)

    def _rule_missing_relationship(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        return [(obj, {"relationship": config.get("relationship")}) for obj in self._objects(config) if self._count_relationships(obj, config) == 0]

    def _rule_relationship_count(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        out = []
        minimum = int(config.get("min", -1))
        maximum = int(config.get("max", 10**9))
        for obj in self._objects(config):
            count = self._count_relationships(obj, config)
            if minimum <= count <= maximum:
                out.append((obj, {"relationship_count": count, "minimum": minimum, "maximum": maximum}))
        return out

    def _rule_related_object_status(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        out = []
        for obj in self._objects(config):
            if config.get("object_lifecycle") and obj.lifecycle_stage != config["object_lifecycle"]:
                continue
            stmt = select(ArchitectureRelationship).where(ArchitectureRelationship.source_object_id == obj.id, ArchitectureRelationship.archived_at.is_(None))
            for rel in self.db.scalars(stmt).unique().all():
                if rel.relationship_type.name != config.get("relationship") and rel.relationship_type.key != config.get("relationship"):
                    continue
                related = rel.target_object
                if related.object_type.key != config.get("related_type"):
                    continue
                matched = False
                if config.get("property"):
                    matched = related.properties.get(str(config["property"])) in config.get("values", [])
                if config.get("lifecycle_values"):
                    matched = matched or related.lifecycle_stage in config.get("lifecycle_values", [])
                if matched:
                    out.append((obj, {"related_object_id": related.id, "related_object": related.name}))
                    break
        return out

    def _rule_duplicate_name(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        objects = self._objects(config)
        groups: dict[str, list[ArchitectureObject]] = {}
        for obj in objects:
            normalized = " ".join(obj.name.lower().split())
            groups.setdefault(normalized, []).append(obj)
        result: list[tuple[ArchitectureObject, dict[str, object]]] = []
        for normalized, group in groups.items():
            if len(group) > 1:
                for obj in group:
                    result.append(
                        (obj, {"normalized_name": normalized, "matching_object_ids": [item.id for item in group]})
                    )
        return result

    def _rule_risk_threshold(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        out = []
        for obj in self._objects(config):
            if config.get("criticality") and obj.criticality != config["criticality"]:
                continue
            metric = self.db.scalar(select(ObjectMetric).where(ObjectMetric.object_id == obj.id, ObjectMetric.metric_type == config["metric_type"]))
            if metric and metric.score >= int(config["threshold"]):
                out.append((obj, {"score": metric.score, "band": metric.band, "threshold": config["threshold"]}))
        return out

    def _rule_review_overdue(self, config: dict[str, object]) -> list[tuple[ArchitectureObject, dict[str, object]]]:
        today = date.today()
        return [(obj, {"next_review_date": obj.next_review_date.isoformat()}) for obj in self._objects(config) if obj.next_review_date and obj.next_review_date < today]

    @staticmethod
    def _state(finding: Finding) -> dict[str, object]:
        return {"status": finding.status, "assigned_user_id": finding.assigned_user_id, "assigned_role": finding.assigned_role, "resolved_at": finding.resolved_at.isoformat() if finding.resolved_at else None, "resolution_notes": finding.resolution_notes, "dismissal_reason": finding.dismissal_reason}
