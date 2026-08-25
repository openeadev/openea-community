from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import ARCHITECT, ARCHITECTURE_ADMIN, CONTRIBUTOR, require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.metamodel import RelationshipType
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.repositories.relationship_repository import RelationshipRepository
from app.services.metamodel_service import MetamodelService
from app.services.relationship_service import RelationshipService, RelationshipServiceError

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
require_relationship_editor = require_roles(ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR)
require_relationship_archiver = require_roles(ARCHITECTURE_ADMIN, ARCHITECT)


def _enum_values(db: Session, key: str) -> list[str]:
    return MetamodelService(db)._enumeration_values(key)


def _schema_fields(rel_type: RelationshipType) -> list[tuple[str, dict[str, Any]]]:
    return [(name, spec) for name, spec in rel_type.properties_schema.items() if isinstance(spec, dict)]


def _property_values(form: Any, rel_type: RelationshipType) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, spec in _schema_fields(rel_type):
        key = f"prop__{name}"
        kind = spec.get("type")
        if kind == "boolean":
            result[name] = form.get(key) == "true"
        elif kind == "multi_select":
            values = [v for v in form.getlist(key) if v]
            if values or spec.get("required"):
                result[name] = values
        else:
            raw = form.get(key)
            if raw not in (None, ""):
                if kind == "integer":
                    try:
                        result[name] = int(raw)
                    except (TypeError, ValueError):
                        result[name] = raw
                else:
                    result[name] = raw
    return result


def _form_context(request: Request, user: User, db: Session, *, source_obj=None, rel=None, error=None):
    repo = RelationshipRepository(db)
    obj_repo = ObjectRepository(db)
    if rel is not None:
        rel_type = rel.relationship_type
        return {
            "settings": get_settings(), "current_user": user, "csrf_token": get_csrf_token(request),
            "source_object": rel.source_object, "relationship": rel, "relationship_type": rel_type,
            "schema_fields": _schema_fields(rel_type), "criticalities": _enum_values(db, "criticality"),
            "confidences": _enum_values(db, "confidence"), "sources": _enum_values(db, "source"),
            "error": error,
        }
    valid_types = repo.list_valid_types_for_source_type(source_obj.object_type_id)
    choices = []
    target_types: set[str] = set()
    for rel_type in valid_types:
        for rule in rel_type.rules:
            if rule.source_object_type_id != source_obj.object_type_id:
                continue
            target_type = next((t for t in obj_repo.list_object_types() if t.id == rule.target_object_type_id), None)
            if target_type:
                choices.append((rel_type, target_type))
                target_types.add(target_type.key)
    targets = []
    for target_type in sorted(target_types):
        targets.extend(obj_repo.list_reference_objects(target_type))
    property_groups = {rel_type.key: _schema_fields(rel_type) for rel_type in valid_types if _schema_fields(rel_type)}
    return {
        "settings": get_settings(), "current_user": user, "csrf_token": get_csrf_token(request),
        "source_object": source_obj, "relationship": None, "relationship_choices": choices,
        "property_groups": property_groups,
        "targets": targets, "criticalities": _enum_values(db, "criticality"),
        "confidences": _enum_values(db, "confidence"), "sources": _enum_values(db, "source"), "error": error,
    }


@router.get("/explore/{source_id}/relationships/new", response_class=HTMLResponse)
def new_relationship_page(source_id: str, request: Request, current_user: User = Depends(require_relationship_editor), db: Session = Depends(get_db)) -> HTMLResponse:
    source_obj = ObjectRepository(db).get_by_id(source_id)
    if source_obj is None:
        raise HTTPException(status_code=404, detail="Source object not found")
    return templates.TemplateResponse(request=request, name="relationships/form.html", context=_form_context(request, current_user, db, source_obj=source_obj))


@router.post("/explore/{source_id}/relationships/new", response_class=HTMLResponse)
async def create_relationship(source_id: str, request: Request, current_user: User = Depends(require_relationship_editor), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    source_obj = ObjectRepository(db).get_by_id(source_id)
    if source_obj is None:
        raise HTTPException(status_code=404, detail="Source object not found")
    choice = str(form.get("relationship_choice", ""))
    relationship_key = choice.split("|", 1)[0] if "|" in choice else choice
    try:
        rel_type = db.query(RelationshipType).filter(RelationshipType.key == relationship_key).one_or_none()
        properties = _property_values(form, rel_type) if rel_type is not None else {}
        rel = RelationshipService(db).create_relationship(
            relationship_key=relationship_key, source_object_id=source_id,
            target_object_id=str(form.get("target_object_id", "")),
            description=str(form.get("description", "")), criticality=str(form.get("criticality", "")) or None,
            confidence=str(form.get("confidence", "")) or None, valid_from=str(form.get("valid_from", "")) or None,
            valid_until=str(form.get("valid_until", "")) or None, source=str(form.get("source", "")) or None,
            properties=properties, actor=current_user,
        )
    except RelationshipServiceError as exc:
        return templates.TemplateResponse(request=request, name="relationships/form.html", context=_form_context(request, current_user, db, source_obj=source_obj, error=str(exc)), status_code=400)
    return RedirectResponse(f"/explore/{rel.source_object_id}?tab=relationships", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/relationships/{relationship_id}/edit", response_class=HTMLResponse)
def edit_relationship_page(relationship_id: str, request: Request, current_user: User = Depends(require_relationship_editor), db: Session = Depends(get_db)) -> HTMLResponse:
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return templates.TemplateResponse(request=request, name="relationships/form.html", context=_form_context(request, current_user, db, rel=rel))


@router.post("/relationships/{relationship_id}/edit", response_class=HTMLResponse)
async def edit_relationship(relationship_id: str, request: Request, current_user: User = Depends(require_relationship_editor), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    try:
        RelationshipService(db).update_relationship(
            rel, description=str(form.get("description", "")), criticality=str(form.get("criticality", "")) or None,
            confidence=str(form.get("confidence", "")) or None, valid_from=str(form.get("valid_from", "")) or None,
            valid_until=str(form.get("valid_until", "")) or None, source=str(form.get("source", "")) or None,
            properties=_property_values(form, rel.relationship_type), actor=current_user,
        )
    except RelationshipServiceError as exc:
        return templates.TemplateResponse(request=request, name="relationships/form.html", context=_form_context(request, current_user, db, rel=rel, error=str(exc)), status_code=400)
    return RedirectResponse(f"/explore/{rel.source_object_id}?tab=relationships", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/relationships/{relationship_id}/archive")
async def archive_relationship(relationship_id: str, request: Request, current_user: User = Depends(require_relationship_archiver), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    source_id = rel.source_object_id
    RelationshipService(db).archive_relationship(rel, actor=current_user)
    return RedirectResponse(f"/explore/{source_id}?tab=relationships", status_code=status.HTTP_303_SEE_OTHER)
