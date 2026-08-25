from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.imports import ImportBatch
from app.models.metamodel import (
    ArchitectureObject,
    ArchitectureRelationship,
    ObjectType,
    RelationshipType,
)
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.audit_service import AuditService
from app.services.object_service import ObjectService, ObjectValidationError

COMMON_IMPORT_FIELDS = (
    "id",
    "name",
    "description",
    "record_status",
    "lifecycle_stage",
    "criticality",
    "source",
    "confidence",
    "valid_from",
    "valid_until",
    "review_frequency",
    "aliases",
    "tags",
)


@dataclass(frozen=True)
class ImportPreviewRow:
    row_number: int
    action: str
    name: str
    errors: list[str]
    warnings: list[str]
    values: dict[str, object]
    existing_id: str | None = None


class ImportService:
    MAX_BYTES = 5 * 1024 * 1024
    MAX_ROWS = 5000

    def __init__(self, db: Session) -> None:
        self.db = db
        self.objects = ObjectRepository(db)

    def create_batch(self, *, object_type_key: str, filename: str, content: bytes, actor: User) -> ImportBatch:
        object_type = self.objects.get_type_by_key(object_type_key)
        if object_type is None:
            raise ValueError("Unknown object type")
        if len(content) > self.MAX_BYTES:
            raise ValueError("CSV file exceeds 5 MB limit")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV must be UTF-8 encoded") from exc
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV must contain a header row")
        headers = [str(v).strip() for v in reader.fieldnames if v]
        rows: list[dict[str, object]] = []
        for index, row in enumerate(reader, start=1):
            if index > self.MAX_ROWS:
                raise ValueError(f"CSV exceeds {self.MAX_ROWS} row limit")
            rows.append({str(k): (v or "").strip() for k, v in row.items() if k is not None})
        mapping = self.suggest_mapping(object_type, headers)
        batch = ImportBatch(
            object_type_key=object_type_key,
            original_filename=filename or "import.csv",
            headers=headers,
            rows=rows,
            mapping=mapping,
            created_by=actor.id,
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def suggest_mapping(self, object_type: ObjectType, headers: list[str]) -> dict[str, str]:
        allowed = set(COMMON_IMPORT_FIELDS)
        allowed.update(f"properties.{name}" for name in (object_type.schema_definition or {}))
        lookup = {value.lower().replace(" ", "_"): value for value in allowed}
        mapping: dict[str, str] = {}
        for header in headers:
            normalized = header.strip().lower().replace(" ", "_")
            if normalized in lookup:
                mapping[header] = lookup[normalized]
            elif f"properties.{normalized}" in allowed:
                mapping[header] = f"properties.{normalized}"
        return mapping

    def allowed_fields(self, object_type_key: str) -> list[tuple[str, str]]:
        object_type = self.objects.get_type_by_key(object_type_key)
        if object_type is None:
            return []
        fields = [(field, field.replace("_", " ").title()) for field in COMMON_IMPORT_FIELDS]
        for name, spec in (object_type.schema_definition or {}).items():
            label = spec.get("label", name.replace("_", " ").title()) if isinstance(spec, dict) else name
            fields.append((f"properties.{name}", str(label)))
        return fields

    def validate(self, batch: ImportBatch, mapping: dict[str, str]) -> dict[str, object]:
        if "name" not in mapping.values():
            raise ValueError("At least one CSV column must be mapped to Name")
        allowed = {value for value, _ in self.allowed_fields(batch.object_type_key)}
        mapping = {k: v for k, v in mapping.items() if v and k in batch.headers}
        if any(value not in allowed for value in mapping.values()):
            raise ValueError("Mapping contains an unsupported destination field")
        if len(set(mapping.values())) != len(mapping.values()):
            raise ValueError("Each destination field may be mapped only once")

        results: list[ImportPreviewRow] = []
        for row_number, raw in enumerate(batch.rows, start=2):
            results.append(self._preview_row(batch.object_type_key, row_number, raw, mapping))
        counts = {key: sum(1 for row in results if row.action == key) for key in ("New", "Update", "Unchanged", "Error")}
        preview = {
            "counts": counts,
            "rows": [
                {
                    "row_number": row.row_number,
                    "action": row.action,
                    "name": row.name,
                    "errors": row.errors,
                    "warnings": row.warnings,
                    "values": row.values,
                    "existing_id": row.existing_id,
                }
                for row in results
            ],
        }
        batch.mapping = mapping
        batch.preview = preview
        batch.status = "Validated" if counts["Error"] == 0 else "Validation Failed"
        self.db.commit()
        return preview

    def commit(self, batch: ImportBatch, *, actor: User) -> dict[str, int]:
        if batch.status != "Validated":
            raise ValueError("Import must validate without errors before commit")
        preview_rows = list(batch.preview.get("rows", []))
        if any(row.get("action") == "Error" for row in preview_rows):
            raise ValueError("Import contains invalid rows")
        service = ObjectService(self.db)
        counts = {"created": 0, "updated": 0, "unchanged": 0}
        correlation_id = f"csv-import:{batch.id}"
        for row in preview_rows:
            action = str(row["action"])
            if action == "Unchanged":
                counts["unchanged"] += 1
                continue
            values = dict(row["values"])
            existing_id = row.get("existing_id")
            if action == "New":
                service.create_object(actor=actor, correlation_id=correlation_id, audit_source="CSV Import", **self._service_values(batch.object_type_key, values))
                counts["created"] += 1
            elif action == "Update" and existing_id:
                obj = self.objects.get_by_id(str(existing_id))
                if obj is None:
                    raise ValueError(f"Object disappeared before commit: {existing_id}")
                service.update_object(obj, actor=actor, correlation_id=correlation_id, audit_source="CSV Import", **self._update_values(obj, values))
                counts["updated"] += 1
        AuditService(self.db).record(
            action="CsvImportCommitted",
            entity_type="import_batch",
            entity_id=batch.id,
            actor=actor,
            after=counts,
            source="CSV Import",
            correlation_id=correlation_id,
        )
        batch.status = "Committed"
        batch.committed_at = datetime.now(timezone.utc)
        self.db.commit()
        return counts

    def get_batch(self, batch_id: str) -> ImportBatch | None:
        return self.db.get(ImportBatch, batch_id)

    def _preview_row(self, object_type_key: str, row_number: int, raw: dict[str, object], mapping: dict[str, str]) -> ImportPreviewRow:
        values = self._mapped_values(raw, mapping)
        values["properties"] = self._coerce_properties(object_type_key, dict(values.get("properties", {})))
        name = str(values.get("name", "")).strip()
        errors: list[str] = []
        warnings: list[str] = []
        if not name:
            errors.append("Name is required")
            return ImportPreviewRow(row_number, "Error", name, errors, warnings, values)
        existing = self._match_existing(object_type_key, values)
        try:
            if existing is None:
                self._validate_service_values(object_type_key, values)
                action = "New"
            else:
                self._validate_update(existing, values)
                action = "Unchanged" if self._is_unchanged(existing, values) else "Update"
        except (ObjectValidationError, ValueError) as exc:
            errors.append(str(exc))
            action = "Error"
        if existing is None and values.get("id"):
            warnings.append("ID did not match an existing object; a new UUID will be assigned")
        return ImportPreviewRow(row_number, action, name, errors, warnings, values, existing.id if existing else None)

    def _match_existing(self, object_type_key: str, values: dict[str, object]) -> ArchitectureObject | None:
        supplied_id = str(values.get("id") or "").strip()
        if supplied_id:
            obj = self.objects.get_by_id(supplied_id)
            if obj is not None and obj.object_type.key == object_type_key:
                return obj
        name = str(values.get("name") or "").strip()
        if not name:
            return None
        return self.db.scalar(
            select(ArchitectureObject)
            .join(ObjectType)
            .where(
                ObjectType.key == object_type_key,
                ArchitectureObject.archived_at.is_(None),
                func.lower(ArchitectureObject.name) == name.lower(),
            )
        )

    def _coerce_properties(self, object_type_key: str, properties: dict[str, object]) -> dict[str, object]:
        object_type = self.objects.get_type_by_key(object_type_key)
        if object_type is None:
            return properties
        coerced: dict[str, object] = {}
        for name, value in properties.items():
            spec = (object_type.schema_definition or {}).get(name, {})
            kind = spec.get("type") if isinstance(spec, dict) else None
            text = str(value).strip()
            if kind == "boolean":
                lowered = text.lower()
                if lowered in {"true", "yes", "1", "y"}:
                    coerced[name] = True
                elif lowered in {"false", "no", "0", "n"}:
                    coerced[name] = False
                else:
                    coerced[name] = value
            elif kind == "integer":
                try:
                    coerced[name] = int(text)
                except ValueError:
                    coerced[name] = value
            elif kind == "multi_select":
                coerced[name] = [item.strip() for item in text.split("|") if item.strip()]
            else:
                coerced[name] = value
        return coerced

    @staticmethod
    def _mapped_values(raw: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
        values: dict[str, object] = {"properties": {}}
        for source, destination in mapping.items():
            value = raw.get(source, "")
            if destination.startswith("properties."):
                prop = destination.split(".", 1)[1]
                if value != "":
                    values["properties"][prop] = value
            elif value != "":
                values[destination] = value
        return values

    def _validate_service_values(self, object_type_key: str, values: dict[str, object]) -> None:
        object_type = self.objects.get_type_by_key(object_type_key)
        if object_type is None:
            raise ValueError("Unknown object type")
        # Validate common values and property schema without persisting.
        service = ObjectService(self.db)
        service._validate_common(
            object_type_key=object_type_key,
            name=str(values.get("name", "")),
            record_status=str(values.get("record_status", "Draft")),
            governance_status=None,
            lifecycle_stage=self._none(values.get("lifecycle_stage")),
            criticality=self._none(values.get("criticality")),
            owner_organization_id=None,
            owner_role_id=None,
            source=self._none(values.get("source")),
            confidence=self._none(values.get("confidence")),
            valid_from=self._none(values.get("valid_from")),
            valid_until=self._none(values.get("valid_until")),
        )
        service.metamodel.validate_object_properties(object_type_key, dict(values.get("properties", {})))

    def _validate_update(self, obj: ArchitectureObject, values: dict[str, object]) -> None:
        merged = self._update_values(obj, values)
        service = ObjectService(self.db)
        service._validate_common(
            object_type_key=obj.object_type.key,
            name=str(merged["name"]),
            record_status=str(merged["record_status"]),
            governance_status=obj.governance_status,
            lifecycle_stage=self._none(merged.get("lifecycle_stage")),
            criticality=self._none(merged.get("criticality")),
            owner_organization_id=merged.get("owner_organization_id"),
            owner_role_id=merged.get("owner_role_id"),
            source=self._none(merged.get("source")),
            confidence=self._none(merged.get("confidence")),
            valid_from=self._none(merged.get("valid_from")),
            valid_until=self._none(merged.get("valid_until")),
        )
        service.metamodel.validate_object_properties(obj.object_type.key, dict(merged.get("properties", {})))

    def _service_values(self, object_type_key: str, values: dict[str, object]) -> dict[str, Any]:
        return {
            "object_type_key": object_type_key,
            "name": str(values.get("name", "")),
            "description": str(values.get("description", "")),
            "record_status": str(values.get("record_status", "Draft")),
            "governance_status": None,
            "lifecycle_stage": self._none(values.get("lifecycle_stage")),
            "criticality": self._none(values.get("criticality")),
            "owner_organization_id": None,
            "owner_role_id": None,
            "source": self._none(values.get("source")) or "Imported",
            "confidence": self._none(values.get("confidence")),
            "valid_from": self._none(values.get("valid_from")),
            "valid_until": self._none(values.get("valid_until")),
            "aliases": str(values.get("aliases", "")),
            "tags": str(values.get("tags", "")),
            "properties": dict(values.get("properties", {})),
            "review_frequency": self._none(values.get("review_frequency")),
        }

    def _update_values(self, obj: ArchitectureObject, values: dict[str, object]) -> dict[str, Any]:
        merged_properties = dict(obj.properties or {})
        merged_properties.update(dict(values.get("properties", {})))
        return {
            "name": str(values.get("name", obj.name)),
            "description": str(values.get("description", obj.description)),
            "record_status": str(values.get("record_status", obj.record_status)),
            "governance_status": obj.governance_status,
            "lifecycle_stage": self._none(values.get("lifecycle_stage")) or obj.lifecycle_stage,
            "criticality": self._none(values.get("criticality")) or obj.criticality,
            "owner_organization_id": obj.owner_organization_id,
            "owner_role_id": obj.owner_role_id,
            "source": self._none(values.get("source")) or obj.source,
            "confidence": self._none(values.get("confidence")) or obj.confidence,
            "valid_from": self._none(values.get("valid_from")) or (obj.valid_from.isoformat() if obj.valid_from else None),
            "valid_until": self._none(values.get("valid_until")) or (obj.valid_until.isoformat() if obj.valid_until else None),
            "aliases": str(values.get("aliases", ", ".join(alias.alias for alias in obj.aliases))),
            "tags": str(values.get("tags", ", ".join(tag.name for tag in obj.tags))),
            "properties": merged_properties,
            "review_frequency": self._none(values.get("review_frequency")) or obj.review_frequency,
        }

    def _is_unchanged(self, obj: ArchitectureObject, values: dict[str, object]) -> bool:
        merged = self._update_values(obj, values)
        comparable = {
            "name": obj.name,
            "description": obj.description,
            "record_status": obj.record_status,
            "lifecycle_stage": obj.lifecycle_stage,
            "criticality": obj.criticality,
            "source": obj.source,
            "confidence": obj.confidence,
            "review_frequency": obj.review_frequency,
            "properties": obj.properties or {},
        }
        candidate = {key: merged[key] for key in comparable}
        return comparable == candidate

    @staticmethod
    def _none(value: object) -> str | None:
        text = str(value or "").strip()
        return text or None

RELATIONSHIP_IMPORT_FIELDS = (
    "source_type",
    "source_id",
    "source_external_id",
    "source_name",
    "relationship_type",
    "target_type",
    "target_id",
    "target_external_id",
    "target_name",
    "description",
    "criticality",
    "confidence",
    "valid_from",
    "valid_until",
    "source",
)


class RelationshipImportService:
    """Validated CSV import for first-class architecture relationships."""

    MAX_BYTES = ImportService.MAX_BYTES
    MAX_ROWS = ImportService.MAX_ROWS

    def __init__(self, db: Session) -> None:
        self.db = db
        self.objects = ObjectRepository(db)

    def create_batch(self, *, filename: str, content: bytes, actor: User) -> ImportBatch:
        if len(content) > self.MAX_BYTES:
            raise ValueError("CSV file exceeds 5 MB limit")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("CSV must be UTF-8 encoded") from exc
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("CSV must contain a header row")
        headers = [str(v).strip() for v in reader.fieldnames if v]
        rows: list[dict[str, object]] = []
        for index, row in enumerate(reader, start=1):
            if index > self.MAX_ROWS:
                raise ValueError(f"CSV exceeds {self.MAX_ROWS} row limit")
            rows.append({str(k): (v or "").strip() for k, v in row.items() if k is not None})
        batch = ImportBatch(
            import_kind="relationship",
            object_type_key=None,
            original_filename=filename or "relationships.csv",
            headers=headers,
            rows=rows,
            mapping=self.suggest_mapping(headers),
            created_by=actor.id,
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def get_batch(self, batch_id: str) -> ImportBatch | None:
        return self.db.get(ImportBatch, batch_id)

    def allowed_fields(self) -> list[tuple[str, str]]:
        fields = [(field, field.replace("_", " ").title()) for field in RELATIONSHIP_IMPORT_FIELDS]
        prop_names: set[str] = set()
        for rel_type in self.db.scalars(select(RelationshipType).where(RelationshipType.is_active.is_(True))):
            prop_names.update((rel_type.properties_schema or {}).keys())
        fields.extend((f"properties.{name}", f"{name.replace('_', ' ').title()} (relationship property)") for name in sorted(prop_names))
        return fields

    def suggest_mapping(self, headers: list[str]) -> dict[str, str]:
        allowed = {field for field, _ in self.allowed_fields()}
        lookup = {value.lower().replace(" ", "_"): value for value in allowed}
        mapping: dict[str, str] = {}
        for header in headers:
            normalized = header.strip().lower().replace(" ", "_")
            if normalized in lookup:
                mapping[header] = lookup[normalized]
            elif f"properties.{normalized}" in allowed:
                mapping[header] = f"properties.{normalized}"
        return mapping

    def validate(self, batch: ImportBatch, mapping: dict[str, str]) -> dict[str, object]:
        if batch.import_kind != "relationship":
            raise ValueError("This is not a relationship import batch")
        required = {"source_type", "relationship_type", "target_type"}
        mapped = set(mapping.values())
        missing = sorted(required - mapped)
        if missing:
            raise ValueError(f"Required relationship mappings are missing: {', '.join(missing)}")
        allowed = {value for value, _ in self.allowed_fields()}
        mapping = {k: v for k, v in mapping.items() if v and k in batch.headers}
        if any(value not in allowed for value in mapping.values()):
            raise ValueError("Mapping contains an unsupported destination field")
        if len(set(mapping.values())) != len(mapping.values()):
            raise ValueError("Each destination field may be mapped only once")

        rows: list[dict[str, object]] = []
        for row_number, raw in enumerate(batch.rows, start=2):
            rows.append(self._preview_row(row_number, raw, mapping))
        counts = {key: sum(1 for row in rows if row["action"] == key) for key in ("New", "Update", "Unchanged", "Error")}
        preview = {"counts": counts, "rows": rows}
        batch.mapping = mapping
        batch.preview = preview
        batch.status = "Validated" if counts["Error"] == 0 else "Validation Failed"
        self.db.commit()
        return preview

    def commit(self, batch: ImportBatch, *, actor: User) -> dict[str, int]:
        if batch.import_kind != "relationship":
            raise ValueError("This is not a relationship import batch")
        if batch.status != "Validated":
            raise ValueError("Import must validate without errors before commit")
        rows = list((batch.preview or {}).get("rows", []))
        if any(row.get("action") == "Error" for row in rows):
            raise ValueError("Import contains invalid rows")
        from app.services.relationship_service import RelationshipService

        service = RelationshipService(self.db)
        counts = {"created": 0, "updated": 0, "unchanged": 0}
        correlation_id = f"relationship-csv-import:{batch.id}"
        for row in rows:
            action = str(row["action"])
            if action == "Unchanged":
                counts["unchanged"] += 1
                continue
            values = dict(row["values"])
            if action == "New":
                service.create_relationship(
                    relationship_key=str(values["relationship_type"]),
                    source_object_id=str(values["source_object_id"]),
                    target_object_id=str(values["target_object_id"]),
                    description=str(values.get("description") or ""),
                    criticality=self._optional(values.get("criticality")),
                    confidence=self._optional(values.get("confidence")),
                    valid_from=self._optional(values.get("valid_from")),
                    valid_until=self._optional(values.get("valid_until")),
                    source=self._optional(values.get("source")),
                    properties=dict(values.get("properties") or {}),
                    actor=actor,
                    audit_source="CSV Import",
                    correlation_id=correlation_id,
                )
                counts["created"] += 1
            elif action == "Update":
                rel = self.db.get(ArchitectureRelationship, str(row.get("existing_id")))
                if rel is None or rel.archived_at is not None:
                    raise ValueError("Relationship disappeared before commit")
                service.update_relationship(
                    rel,
                    description=str(values.get("description") or ""),
                    criticality=self._optional(values.get("criticality")),
                    confidence=self._optional(values.get("confidence")),
                    valid_from=self._optional(values.get("valid_from")),
                    valid_until=self._optional(values.get("valid_until")),
                    source=self._optional(values.get("source")),
                    properties=dict(values.get("properties") or {}),
                    actor=actor,
                    audit_source="CSV Import",
                    correlation_id=correlation_id,
                )
                counts["updated"] += 1
        AuditService(self.db).record(
            action="RelationshipImportCommitted",
            entity_type="import_batch",
            entity_id=batch.id,
            actor=actor,
            source="CSV Import",
            correlation_id=correlation_id,
            after=counts,
        )
        batch.status = "Committed"
        batch.committed_at = datetime.now(timezone.utc)
        self.db.commit()
        return counts

    def _preview_row(self, row_number: int, raw: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
        errors: list[str] = []
        warnings: list[str] = []
        mapped = self._mapped_values(raw, mapping)
        source_type = str(mapped.get("source_type") or "").strip()
        target_type = str(mapped.get("target_type") or "").strip()
        rel_key_input = str(mapped.get("relationship_type") or "").strip()
        if not source_type or not target_type or not rel_key_input:
            errors.append("Source type, relationship type, and target type are required")
        rel_type = self._resolve_relationship_type(rel_key_input)
        if rel_type is None and rel_key_input:
            errors.append(f"Unknown relationship type: {rel_key_input}")

        source_obj, source_error, source_warning = self._resolve_object(
            object_type_key=source_type,
            object_id=str(mapped.get("source_id") or ""),
            external_id=str(mapped.get("source_external_id") or ""),
            name=str(mapped.get("source_name") or ""),
        )
        target_obj, target_error, target_warning = self._resolve_object(
            object_type_key=target_type,
            object_id=str(mapped.get("target_id") or ""),
            external_id=str(mapped.get("target_external_id") or ""),
            name=str(mapped.get("target_name") or ""),
        )
        if source_error:
            errors.append(f"Source: {source_error}")
        if target_error:
            errors.append(f"Target: {target_error}")
        if source_warning:
            warnings.append(f"Source: {source_warning}")
        if target_warning:
            warnings.append(f"Target: {target_warning}")

        properties = dict(mapped.get("properties") or {})
        if rel_type is not None:
            properties = self._coerce_properties(rel_type, properties)
        values: dict[str, object] = {
            "source_object_id": source_obj.id if source_obj else "",
            "target_object_id": target_obj.id if target_obj else "",
            "relationship_type": rel_type.key if rel_type else rel_key_input,
            "description": str(mapped.get("description") or ""),
            "criticality": str(mapped.get("criticality") or ""),
            "confidence": str(mapped.get("confidence") or ""),
            "valid_from": str(mapped.get("valid_from") or ""),
            "valid_until": str(mapped.get("valid_until") or ""),
            "source": str(mapped.get("source") or ""),
            "properties": properties,
        }
        if not errors and rel_type and source_obj and target_obj:
            try:
                from app.services.relationship_service import RelationshipService

                validator = RelationshipService(self.db)
                validator.metamodel.validate_relationship_rule(rel_type.key, source_obj.object_type.key, target_obj.object_type.key)
                validator.metamodel.validate_relationship_properties(rel_type.key, properties)
                start = validator._parse_date(self._optional(values.get("valid_from")), "Valid from")
                end = validator._parse_date(self._optional(values.get("valid_until")), "Valid until")
                if start and end and end < start:
                    raise ValueError("Valid until cannot be before valid from")
                validator._validate_enum("criticality", self._optional(values.get("criticality")))
                validator._validate_enum("confidence", self._optional(values.get("confidence")))
                validator._validate_enum("source", self._optional(values.get("source")))
            except ValueError as exc:
                errors.append(str(exc))

        existing = None
        if not errors and rel_type and source_obj and target_obj:
            existing = self.db.scalar(
                select(ArchitectureRelationship).where(
                    ArchitectureRelationship.relationship_type_id == rel_type.id,
                    ArchitectureRelationship.source_object_id == source_obj.id,
                    ArchitectureRelationship.target_object_id == target_obj.id,
                    ArchitectureRelationship.archived_at.is_(None),
                )
            )
        action = "Error" if errors else "New"
        if existing is not None and not errors:
            action = "Unchanged" if self._same(existing, values) else "Update"
        label = f"{source_obj.name if source_obj else source_type} → {rel_type.name if rel_type else rel_key_input} → {target_obj.name if target_obj else target_type}"
        return {
            "row_number": row_number,
            "action": action,
            "name": label,
            "errors": errors,
            "warnings": warnings,
            "values": values,
            "existing_id": existing.id if existing else None,
        }

    def _resolve_object(self, *, object_type_key: str, object_id: str, external_id: str, name: str) -> tuple[ArchitectureObject | None, str | None, str | None]:
        object_type = self._resolve_object_type(object_type_key)
        if object_type is None:
            return None, f"Unknown object type: {object_type_key or '(blank)'}", None
        candidates = list(
            self.db.scalars(
                select(ArchitectureObject).where(
                    ArchitectureObject.object_type_id == object_type.id,
                    ArchitectureObject.archived_at.is_(None),
                )
            ).unique().all()
        )
        if object_id:
            matches = [obj for obj in candidates if obj.id == object_id]
            return self._one(matches, f"UUID {object_id}", "UUID")
        if external_id:
            matches = []
            for obj in candidates:
                props = obj.properties or {}
                ext = props.get("external_id")
                ext_many = props.get("external_ids")
                if str(ext or "") == external_id or (isinstance(ext_many, list) and external_id in [str(v) for v in ext_many]):
                    matches.append(obj)
            if matches:
                obj, error, _ = self._one(matches, f"external ID {external_id}", "external ID")
                return obj, error, "matched by external ID" if obj else None
        if name:
            exact = [obj for obj in candidates if obj.name.casefold() == name.casefold()]
            if exact:
                obj, error, _ = self._one(exact, f"name {name}", "name")
                return obj, error, "matched by exact name" if obj else None
            alias_matches = [obj for obj in candidates if any(alias.alias.casefold() == name.casefold() for alias in obj.aliases)]
            if alias_matches:
                obj, error, _ = self._one(alias_matches, f"alias {name}", "alias")
                return obj, error, "matched by alias" if obj else None
        return None, "No matching active object found", None

    @staticmethod
    def _one(matches: list[ArchitectureObject], label: str, method: str) -> tuple[ArchitectureObject | None, str | None, str | None]:
        if len(matches) == 1:
            return matches[0], None, f"matched by {method}"
        if len(matches) > 1:
            return None, f"Ambiguous {label}: {len(matches)} objects match", None
        return None, f"No object matches {label}", None

    def _resolve_object_type(self, value: str) -> ObjectType | None:
        if not value:
            return None
        object_type = self.objects.get_type_by_key(value)
        if object_type:
            return object_type
        matches = list(
            self.db.scalars(
                select(ObjectType).where(
                    func.lower(ObjectType.name) == value.lower(),
                    ObjectType.is_active.is_(True),
                )
            ).all()
        )
        return matches[0] if len(matches) == 1 else None

    def _resolve_relationship_type(self, value: str) -> RelationshipType | None:
        if not value:
            return None
        rel = self.db.scalar(select(RelationshipType).where(RelationshipType.key == value, RelationshipType.is_active.is_(True)))
        if rel:
            return rel
        matches = list(self.db.scalars(select(RelationshipType).where(func.lower(RelationshipType.name) == value.lower(), RelationshipType.is_active.is_(True))).all())
        return matches[0] if len(matches) == 1 else None

    @staticmethod
    def _coerce_properties(rel_type: RelationshipType, properties: dict[str, object]) -> dict[str, object]:
        coerced: dict[str, object] = {}
        for name, value in properties.items():
            spec = (rel_type.properties_schema or {}).get(name, {})
            kind = spec.get("type") if isinstance(spec, dict) else None
            text = str(value).strip()
            if kind == "boolean":
                if text.lower() in {"true", "yes", "1", "y"}:
                    coerced[name] = True
                elif text.lower() in {"false", "no", "0", "n"}:
                    coerced[name] = False
                else:
                    coerced[name] = value
            elif kind == "integer":
                try:
                    coerced[name] = int(text)
                except ValueError:
                    coerced[name] = value
            elif kind == "multi_select":
                coerced[name] = [item.strip() for item in text.split("|") if item.strip()]
            else:
                coerced[name] = value
        return coerced

    @staticmethod
    def _mapped_values(raw: dict[str, object], mapping: dict[str, str]) -> dict[str, object]:
        values: dict[str, object] = {"properties": {}}
        for source, destination in mapping.items():
            value = raw.get(source, "")
            if destination.startswith("properties."):
                if value != "":
                    values["properties"][destination.split(".", 1)[1]] = value
            elif value != "":
                values[destination] = value
        return values

    @staticmethod
    def _same(rel: ArchitectureRelationship, values: dict[str, object]) -> bool:
        return (
            rel.description == str(values.get("description") or "")
            and (rel.criticality or "") == str(values.get("criticality") or "")
            and (rel.confidence or "") == str(values.get("confidence") or "")
            and (rel.valid_from.isoformat() if rel.valid_from else "") == str(values.get("valid_from") or "")
            and (rel.valid_until.isoformat() if rel.valid_until else "") == str(values.get("valid_until") or "")
            and (rel.source or "") == str(values.get("source") or "")
            and (rel.properties or {}) == dict(values.get("properties") or {})
        )

    @staticmethod
    def _optional(value: object) -> str | None:
        text = str(value or "").strip()
        return text or None
