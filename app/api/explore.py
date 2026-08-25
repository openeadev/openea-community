from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import (
    ARCHITECT,
    ARCHITECTURE_ADMIN,
    CONTRIBUTOR,
    require_authenticated,
    require_roles,
)
from app.core.config import get_settings
from app.db.session import get_db
from app.models.metamodel import ArchitectureObject, ObjectType
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.services.audit_service import AuditService
from app.services.governance_service import (
    DECISION_TRANSITIONS,
    PRINCIPLE_TRANSITIONS,
    GovernanceService,
)
from app.services.metamodel_service import MetamodelService
from app.services.object_service import ObjectService, ObjectValidationError
from app.services.search_service import SearchService

router = APIRouter(prefix="/explore", include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")

require_object_creator = require_roles(ARCHITECTURE_ADMIN, ARCHITECT)
require_object_editor = require_roles(ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR)
require_object_archiver = require_roles(ARCHITECTURE_ADMIN, ARCHITECT)


def _can(user: User, *roles: str) -> bool:
    return bool({role.name for role in user.roles}.intersection(roles))


def _enum_values(db: Session, key: str) -> list[str]:
    return MetamodelService(db)._enumeration_values(key)


def _lifecycle_enum(object_type_key: str) -> str | None:
    return ObjectService._lifecycle_enum_for_type(object_type_key)


def _schema_fields(object_type: ObjectType) -> list[tuple[str, dict[str, Any]]]:
    fields: list[tuple[str, dict[str, Any]]] = []
    for name, raw_spec in object_type.schema_definition.items():
        if name == "lifecycle_stage" or not isinstance(raw_spec, dict):
            continue
        fields.append((name, raw_spec))
    return fields


def _reference_options(db: Session, fields: list[tuple[str, dict[str, Any]]]) -> dict[str, list[ArchitectureObject]]:
    repo = ObjectRepository(db)
    result: dict[str, list[ArchitectureObject]] = {}
    for name, spec in fields:
        if spec.get("type") == "object_reference" and spec.get("target_object_type"):
            result[name] = repo.list_reference_objects(str(spec["target_object_type"]))
    return result


def _form_context(
    request: Request,
    current_user: User,
    db: Session,
    object_type: ObjectType,
    *,
    obj: ArchitectureObject | None = None,
    error: str | None = None,
    submitted: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fields = _schema_fields(object_type)
    enum_options: dict[str, list[str]] = {}
    for name, spec in fields:
        if spec.get("type") in {"select", "multi_select"} and spec.get("enum"):
            enum_options[name] = _enum_values(db, str(spec["enum"]))
    lifecycle_key = _lifecycle_enum(object_type.key)
    return {
        "settings": get_settings(),
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "object_type": object_type,
        "object": obj,
        "schema_fields": fields,
        "enum_options": enum_options,
        "reference_options": _reference_options(db, fields),
        "owner_organizations": ObjectRepository(db).list_reference_objects("organization"),
        "owner_roles": ObjectRepository(db).list_reference_objects("role"),
        "record_statuses": _enum_values(db, "record_status"),
        "governance_statuses": _enum_values(db, "governance_status"),
        "criticalities": _enum_values(db, "criticality"),
        "sources": _enum_values(db, "source"),
        "confidences": _enum_values(db, "confidence"),
        "lifecycle_stages": _enum_values(db, lifecycle_key) if lifecycle_key else [],
        "error": error,
        "submitted": submitted or {},
        "can_archive": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT),
    }


def _parse_properties(form: Any, object_type: ObjectType) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name, spec in _schema_fields(object_type):
        key = f"prop__{name}"
        kind = spec.get("type")
        if kind == "boolean":
            values[name] = form.get(key) == "true"
            continue
        if kind == "multi_select":
            selected = [value for value in form.getlist(key) if value]
            if selected or spec.get("required"):
                values[name] = selected
            continue
        raw = form.get(key)
        if raw in (None, ""):
            continue
        if kind == "integer":
            try:
                values[name] = int(raw)
            except (TypeError, ValueError):
                values[name] = raw
        else:
            values[name] = raw
    return values


def _service_values(form: Any, object_type: ObjectType) -> dict[str, Any]:
    return {
        "name": str(form.get("name", "")),
        "description": str(form.get("description", "")),
        "record_status": str(form.get("record_status", "Draft")),
        "governance_status": str(form.get("governance_status", "")) or None,
        "lifecycle_stage": str(form.get("lifecycle_stage", "")) or None,
        "criticality": str(form.get("criticality", "")) or None,
        "owner_organization_id": str(form.get("owner_organization_id", "")) or None,
        "owner_role_id": str(form.get("owner_role_id", "")) or None,
        "source": str(form.get("source", "")) or None,
        "confidence": str(form.get("confidence", "")) or None,
        "valid_from": str(form.get("valid_from", "")) or None,
        "valid_until": str(form.get("valid_until", "")) or None,
        "review_frequency": str(form.get("review_frequency", "")) or None,
        "aliases": str(form.get("aliases", "")),
        "tags": str(form.get("tags", "")),
        "properties": _parse_properties(form, object_type),
    }


@router.get("", response_class=HTMLResponse)
def explore_page(
    request: Request,
    q: str | None = None,
    object_type: str | None = None,
    record_status: str | None = None,
    lifecycle: str | None = None,
    criticality: str | None = None,
    governance_status: str | None = None,
    owner: str | None = None,
    tag: str | None = None,
    review_status: str | None = None,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    repo = ObjectRepository(db)
    effective_sort = "relevance" if q and sort == "name" else sort
    results = SearchService(db).search(
        query=q,
        object_type_key=object_type,
        record_status=record_status,
        lifecycle_stage=lifecycle,
        criticality=criticality,
        governance_status=governance_status,
        owner_id=owner,
        tag=tag,
        review_status=review_status,
        sort=effective_sort,
        direction=direction,
        page=page,
    )
    owners = repo.list_reference_objects("organization") + repo.list_reference_objects("role")
    return templates.TemplateResponse(
        request=request,
        name="explore/index.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "objects": results.items,
            "results": results,
            "object_types": repo.list_object_types(),
            "owners": owners,
            "tags": repo.list_tags(),
            "record_statuses": _enum_values(db, "record_status"),
            "criticalities": _enum_values(db, "criticality"),
            "governance_statuses": _enum_values(db, "governance_status"),
            "filters": {
                "q": q or "",
                "object_type": object_type or "",
                "record_status": record_status or "",
                "lifecycle": lifecycle or "",
                "criticality": criticality or "",
                "governance_status": governance_status or "",
                "owner": owner or "",
                "tag": tag or "",
                "review_status": review_status or "",
                "sort": effective_sort,
                "direction": direction,
            },
            "can_create": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT),
        },
    )


@router.get("/new", response_class=HTMLResponse)
def choose_type_page(
    request: Request,
    current_user: User = Depends(require_object_creator),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="explore/choose_type.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "object_types": ObjectRepository(db).list_object_types(),
        },
    )


@router.get("/new/{object_type_key}", response_class=HTMLResponse)
def new_object_page(
    object_type_key: str,
    request: Request,
    current_user: User = Depends(require_object_creator),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    object_type = ObjectRepository(db).get_type_by_key(object_type_key)
    if object_type is None:
        raise HTTPException(status_code=404, detail="Object type not found")
    return templates.TemplateResponse(
        request=request,
        name="explore/object_form.html",
        context=_form_context(request, current_user, db, object_type),
    )


@router.post("/new/{object_type_key}", response_class=HTMLResponse)
async def create_object_submit(
    object_type_key: str,
    request: Request,
    current_user: User = Depends(require_object_creator),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    object_type = ObjectRepository(db).get_type_by_key(object_type_key)
    if object_type is None:
        raise HTTPException(status_code=404, detail="Object type not found")
    values = _service_values(form, object_type)
    try:
        obj = ObjectService(db).create_object(object_type_key=object_type_key, actor=current_user, **values)
    except ObjectValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="explore/object_form.html",
            context=_form_context(
                request,
                current_user,
                db,
                object_type,
                error=str(exc),
                submitted={**values, "properties": values["properties"]},
            ),
            status_code=400,
        )
    return RedirectResponse(f"/explore/{obj.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{object_id}", response_class=HTMLResponse)
def object_detail_page(
    object_id: str,
    request: Request,
    tab: str = "overview",
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return templates.TemplateResponse(
        request=request,
        name="explore/object_detail.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "object": obj,
            "schema_fields": _schema_fields(obj.object_type),
            "can_edit": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR),
            "can_archive": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT),
            "can_manage_relationships": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR),
            "can_govern": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT),
            "can_review_comment": _can(current_user, ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR),
            "tab": tab if tab in {"overview", "relationships", "lifecycle", "history", "comments"} else "overview",
            "relationships": RelationshipRepository(db).list_for_object(obj.id),
            "reviews": GovernanceService(db).list_reviews(obj.id),
            "comments": GovernanceService(db).list_comments(obj.id),
            "audit_events": AuditService(db).list_for_object(obj.id),
            "decision_candidates": ObjectRepository(db).list_reference_objects("architecture_decision") if obj.object_type.key == "architecture_decision" else [],
            "principle_transitions": PRINCIPLE_TRANSITIONS,
            "decision_transitions": DECISION_TRANSITIONS,
        },
    )


@router.get("/{object_id}/edit", response_class=HTMLResponse)
def edit_object_page(
    object_id: str,
    request: Request,
    current_user: User = Depends(require_object_editor),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return templates.TemplateResponse(
        request=request,
        name="explore/object_form.html",
        context=_form_context(request, current_user, db, obj.object_type, obj=obj),
    )


@router.post("/{object_id}/edit", response_class=HTMLResponse)
async def edit_object_submit(
    object_id: str,
    request: Request,
    current_user: User = Depends(require_object_editor),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    values = _service_values(form, obj.object_type)
    try:
        ObjectService(db).update_object(obj, actor=current_user, **values)
    except ObjectValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="explore/object_form.html",
            context=_form_context(
                request,
                current_user,
                db,
                obj.object_type,
                obj=obj,
                error=str(exc),
                submitted={**values, "properties": values["properties"]},
            ),
            status_code=400,
        )
    return RedirectResponse(f"/explore/{obj.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{object_id}/archive")
async def archive_object_submit(
    object_id: str,
    request: Request,
    current_user: User = Depends(require_object_archiver),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    ObjectService(db).archive_object(obj, actor=current_user)
    return RedirectResponse("/explore", status_code=status.HTTP_303_SEE_OTHER)
