from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.api_auth import require_api_access
from app.auth.permissions import ARCHITECT, ARCHITECTURE_ADMIN, CONTRIBUTOR, VIEWER
from app.db.session import get_db
from app.models.analytics import ObjectMetric
from app.models.findings import Finding
from app.models.governance import Review
from app.models.metamodel import ArchitectureObject, ArchitectureRelationship
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.services.analytics_service import AnalyticsService
from app.services.findings_service import FindingsService
from app.services.governance_service import GovernanceService
from app.services.impact_service import ImpactAnalysisError, ImpactService
from app.services.object_service import ObjectService, ObjectValidationError
from app.services.relationship_service import RelationshipService, RelationshipServiceError
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/v1", tags=["OpenEA Community API v1"])


class ObjectWrite(BaseModel):
    object_type_key: str
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    record_status: str = "Draft"
    lifecycle_stage: str | None = None
    criticality: str | None = None
    source: str | None = None
    confidence: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    review_frequency: str | None = None
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    owner_organization_id: str | None = None
    owner_role_id: str | None = None


class ObjectPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    record_status: str | None = None
    lifecycle_stage: str | None = None
    criticality: str | None = None
    source: str | None = None
    confidence: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    review_frequency: str | None = None
    aliases: list[str] | None = None
    tags: list[str] | None = None
    properties: dict[str, Any] | None = None
    owner_organization_id: str | None = None
    owner_role_id: str | None = None


class RelationshipWrite(BaseModel):
    relationship_key: str
    source_object_id: str
    target_object_id: str
    description: str = ""
    criticality: str | None = None
    confidence: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    source: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class RelationshipPatch(BaseModel):
    relationship_key: str | None = None
    target_object_id: str | None = None
    description: str = ""
    criticality: str | None = None
    confidence: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    source: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class FindingPatch(BaseModel):
    status: str
    notes: str = ""
    dismissal_reason: str = ""
    assigned_user_id: str | None = None
    assigned_role: str | None = None


class ReviewWrite(BaseModel):
    notes: str = ""
    next_review_date: str | None = None



API_READ_ROLES = (ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR, VIEWER)
API_WRITE_ROLES = (ARCHITECTURE_ADMIN, ARCHITECT)
API_CONTRIBUTOR_ROLES = (ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR)

def api_access(scope: str, *, write: bool = False, contributor: bool = False):
    roles = API_CONTRIBUTOR_ROLES if contributor else API_WRITE_ROLES if write else API_READ_ROLES
    return require_api_access(roles=roles, scope=scope)


def object_payload(obj: ArchitectureObject) -> dict[str, Any]:
    return {
        "id": obj.id,
        "object_type": {"key": obj.object_type.key, "name": obj.object_type.name, "domain": obj.object_type.domain},
        "name": obj.name,
        "description": obj.description,
        "record_status": obj.record_status,
        "governance_status": obj.governance_status,
        "lifecycle_stage": obj.lifecycle_stage,
        "criticality": obj.criticality,
        "owner_organization_id": obj.owner_organization_id,
        "owner_role_id": obj.owner_role_id,
        "source": obj.source,
        "confidence": obj.confidence,
        "valid_from": obj.valid_from.isoformat() if obj.valid_from else None,
        "valid_until": obj.valid_until.isoformat() if obj.valid_until else None,
        "last_reviewed_date": obj.last_reviewed_date.isoformat() if obj.last_reviewed_date else None,
        "next_review_date": obj.next_review_date.isoformat() if obj.next_review_date else None,
        "review_frequency": obj.review_frequency,
        "aliases": [alias.alias for alias in obj.aliases],
        "tags": [tag.name for tag in obj.tags],
        "properties": obj.properties,
        "created_at": obj.created_at.isoformat(),
        "updated_at": obj.updated_at.isoformat(),
        "url": f"/explore/{obj.id}",
    }


def relationship_payload(rel: ArchitectureRelationship) -> dict[str, Any]:
    return {
        "id": rel.id,
        "relationship_type": {"key": rel.relationship_type.key, "name": rel.relationship_type.name, "inverse_label": rel.relationship_type.inverse_label},
        "source_object_id": rel.source_object_id,
        "target_object_id": rel.target_object_id,
        "description": rel.description,
        "criticality": rel.criticality,
        "confidence": rel.confidence,
        "valid_from": rel.valid_from.isoformat() if rel.valid_from else None,
        "valid_until": rel.valid_until.isoformat() if rel.valid_until else None,
        "source": rel.source,
        "properties": rel.properties,
        "created_at": rel.created_at.isoformat(),
        "updated_at": rel.updated_at.isoformat(),
    }


@router.get("/objects")
def list_objects(
    object_type: str | None = None,
    record_status: str | None = None,
    criticality: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    _: User = Depends(api_access("objects:read")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = SearchService(db).search(object_type_key=object_type, record_status=record_status, criticality=criticality, page=page, per_page=per_page)
    return {"items": [object_payload(obj) for obj in result.items], "total": result.total, "page": result.page, "pages": result.pages, "per_page": result.per_page}


@router.post("/objects", status_code=status.HTTP_201_CREATED)
def create_object(payload: ObjectWrite, actor: User = Depends(api_access("objects:write", write=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        obj = ObjectService(db).create_object(
            object_type_key=payload.object_type_key,
            name=payload.name,
            description=payload.description,
            record_status=payload.record_status,
            governance_status=None,
            lifecycle_stage=payload.lifecycle_stage,
            criticality=payload.criticality,
            owner_organization_id=payload.owner_organization_id,
            owner_role_id=payload.owner_role_id,
            source=payload.source,
            confidence=payload.confidence,
            valid_from=payload.valid_from,
            valid_until=payload.valid_until,
            aliases=", ".join(payload.aliases),
            tags=", ".join(payload.tags),
            properties=payload.properties,
            review_frequency=payload.review_frequency,
            actor=actor,
        )
    except ObjectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return object_payload(obj)


@router.get("/objects/{object_id}")
def get_object(object_id: str, _: User = Depends(api_access("objects:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return object_payload(obj)


@router.patch("/objects/{object_id}")
def update_object(object_id: str, payload: ObjectPatch, actor: User = Depends(api_access("objects:write", contributor=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    repo = ObjectRepository(db)
    obj = repo.get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    values = payload.model_dump(exclude_unset=True)
    data = {
        "name": values.get("name", obj.name),
        "description": values.get("description", obj.description),
        "record_status": values.get("record_status", obj.record_status),
        "governance_status": obj.governance_status,
        "lifecycle_stage": values.get("lifecycle_stage", obj.lifecycle_stage),
        "criticality": values.get("criticality", obj.criticality),
        "owner_organization_id": values.get("owner_organization_id", obj.owner_organization_id),
        "owner_role_id": values.get("owner_role_id", obj.owner_role_id),
        "source": values.get("source", obj.source),
        "confidence": values.get("confidence", obj.confidence),
        "valid_from": values.get("valid_from", obj.valid_from.isoformat() if obj.valid_from else None),
        "valid_until": values.get("valid_until", obj.valid_until.isoformat() if obj.valid_until else None),
        "aliases": ", ".join(values.get("aliases", [alias.alias for alias in obj.aliases])),
        "tags": ", ".join(values.get("tags", [tag.name for tag in obj.tags])),
        "properties": values.get("properties", obj.properties),
        "review_frequency": values.get("review_frequency", obj.review_frequency),
    }
    try:
        updated = ObjectService(db).update_object(obj, actor=actor, **data)
    except ObjectValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return object_payload(updated)


@router.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_object(object_id: str, actor: User = Depends(api_access("objects:write", write=True)), db: Session = Depends(get_db)) -> None:
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    ObjectService(db).archive_object(obj, actor=actor)


@router.get("/relationships")
def list_relationships(object_id: str | None = None, _: User = Depends(api_access("relationships:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    if object_id:
        relationships = RelationshipRepository(db).list_for_object(object_id)
    else:
        relationships = list(db.scalars(select(ArchitectureRelationship).where(ArchitectureRelationship.archived_at.is_(None))).unique().all())
    return {"items": [relationship_payload(rel) for rel in relationships], "total": len(relationships)}


@router.post("/relationships", status_code=status.HTTP_201_CREATED)
def create_relationship(payload: RelationshipWrite, actor: User = Depends(api_access("relationships:write", contributor=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        rel = RelationshipService(db).create_relationship(actor=actor, **payload.model_dump())
    except RelationshipServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return relationship_payload(rel)


@router.patch("/relationships/{relationship_id}")
def update_relationship(relationship_id: str, payload: RelationshipPatch, actor: User = Depends(api_access("relationships:write", contributor=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    try:
        updated = RelationshipService(db).update_relationship(rel, actor=actor, **payload.model_dump())
    except RelationshipServiceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return relationship_payload(updated)


@router.get("/relationships/{relationship_id}")
def get_relationship(relationship_id: str, _: User = Depends(api_access("relationships:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship_payload(rel)


@router.delete("/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_relationship(relationship_id: str, actor: User = Depends(api_access("relationships:write", write=True)), db: Session = Depends(get_db)) -> None:
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    RelationshipService(db).archive_relationship(rel, actor=actor)


@router.get("/search")
def search(
    q: str = "",
    object_type: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    _: User = Depends(api_access("search:read")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    result = SearchService(db).search(query=q or None, object_type_key=object_type, page=page, per_page=per_page, sort="relevance" if q else "name")
    return {"items": [object_payload(obj) for obj in result.items], "total": result.total, "page": result.page, "pages": result.pages}


@router.get("/impact/{object_id}")
def impact(object_id: str, depth: int = Query(3, ge=1, le=5), _: User = Depends(api_access("impact:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        analysis = ImpactService(db).analyze(object_id, depth=depth)
    except ImpactAnalysisError as exc:
        raise HTTPException(status_code=404 if "not found" in str(exc).lower() else 422, detail=str(exc)) from exc
    return {
        "root": object_payload(analysis.root),
        "depth": depth,
        "direct": [impact_item(item) for item in analysis.direct_results],
        "indirect": [impact_item(item) for item in analysis.indirect_results],
        "graph": analysis.graph_payload(),
    }


def impact_item(item: Any) -> dict[str, Any]:
    return {
        "object": object_payload(item.object),
        "depth": item.depth,
        "path_object_ids": item.path_object_ids,
        "path": [step.__dict__ for step in item.path_steps],
    }


@router.get("/findings")
def findings(status_filter: str | None = Query(None, alias="status"), _: User = Depends(api_access("findings:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    stmt = select(Finding)
    if status_filter:
        stmt = stmt.where(Finding.status == status_filter)
    items = list(db.scalars(stmt.order_by(Finding.detected_at.desc())).unique().all())
    return {"items": [{"id": f.id, "severity": f.severity, "title": f.title, "status": f.status, "rule_id": f.rule.rule_id, "related_object_id": f.related_object_id, "evidence": f.evidence} for f in items], "total": len(items)}


@router.patch("/findings/{finding_id}")
def update_finding(finding_id: str, payload: FindingPatch, actor: User = Depends(api_access("findings:write", contributor=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    try:
        updated = FindingsService(db).update_status(finding, actor=actor, **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": updated.id, "status": updated.status, "resolution_notes": updated.resolution_notes, "dismissal_reason": updated.dismissal_reason}


@router.post("/reviews/{object_id}", status_code=status.HTTP_201_CREATED)
def complete_review(object_id: str, payload: ReviewWrite, actor: User = Depends(api_access("reviews:write", contributor=True)), db: Session = Depends(get_db)) -> dict[str, Any]:
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    try:
        review = GovernanceService(db).mark_reviewed(obj, actor=actor, notes=payload.notes, next_review_date=payload.next_review_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": review.id, "object_id": review.object_id, "reviewed_at": review.reviewed_at.isoformat(), "next_review_date": review.next_review_date.isoformat() if review.next_review_date else None, "notes": review.notes}


@router.get("/reviews")
def reviews(_: User = Depends(api_access("reviews:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    items = list(db.scalars(select(Review).order_by(Review.reviewed_at.desc())).unique().all())
    return {"items": [{"id": r.id, "object_id": r.object_id, "reviewed_by": r.reviewed_by, "reviewed_at": r.reviewed_at.isoformat(), "next_review_date": r.next_review_date.isoformat() if r.next_review_date else None, "notes": r.notes} for r in items], "total": len(items)}


@router.get("/analytics")
def analytics(_: User = Depends(api_access("analytics:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    return {"repository_health": AnalyticsService(db).repository_health()}


@router.get("/analytics/objects/{object_id}")
def object_metrics(object_id: str, _: User = Depends(api_access("analytics:read")), db: Session = Depends(get_db)) -> dict[str, Any]:
    if ObjectRepository(db).get_by_id(object_id) is None:
        raise HTTPException(status_code=404, detail="Object not found")
    metrics = list(db.scalars(select(ObjectMetric).where(ObjectMetric.object_id == object_id)).all())
    return {"items": [{"metric_type": m.metric_type, "score": m.score, "band": m.band, "calculated_at": m.calculated_at.isoformat(), "explanation": m.explanation} for m in metrics]}


@router.get("/")
def api_root(_: User = Depends(api_access("objects:read"))) -> dict[str, Any]:
    return {"name": "OpenEA Community API", "version": "v1", "openapi": "/openapi.json", "docs": "/docs"}
