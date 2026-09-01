from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import ARCHITECT, ARCHITECTURE_ADMIN, CONTRIBUTOR, require_roles
from app.core.config import get_settings
from app.db.session import get_db
from app.models.metamodel import ArchitectureObject, ObjectType, RelationshipType
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


def _relationship_choice_groups(
    db: Session, source_obj: ArchitectureObject
) -> list[tuple[RelationshipType, list[ObjectType]]]:
    rel_repo = RelationshipRepository(db)
    obj_repo = ObjectRepository(db)
    object_types_by_id = {object_type.id: object_type for object_type in obj_repo.list_object_types()}

    groups: list[tuple[RelationshipType, list[ObjectType]]] = []
    for rel_type in rel_repo.list_valid_types_for_source_type(source_obj.object_type_id):
        target_types: dict[str, ObjectType] = {}
        for rule in rel_type.rules:
            if rule.source_object_type_id != source_obj.object_type_id:
                continue
            target_type = object_types_by_id.get(rule.target_object_type_id)
            if target_type is not None:
                target_types[target_type.id] = target_type
        if target_types:
            groups.append(
                (
                    rel_type,
                    sorted(
                        target_types.values(),
                        key=lambda item: (item.name.casefold(), item.name),
                    ),
                )
            )

    return sorted(groups, key=lambda item: (item[0].name.casefold(), item[0].name))


def _choice_is_valid(
    groups: list[tuple[RelationshipType, list[ObjectType]]], relationship_choice: str
) -> bool:
    return any(
        relationship_choice == f"{rel_type.key}|{target_type.key}"
        for rel_type, target_types in groups
        for target_type in target_types
    )


def _targets_for_choice(
    db: Session,
    groups: list[tuple[RelationshipType, list[ObjectType]]],
    relationship_choice: str,
) -> list[ArchitectureObject]:
    if not relationship_choice or not _choice_is_valid(groups, relationship_choice):
        return []
    _, target_type_key = relationship_choice.split("|", 1)
    return ObjectRepository(db).list_reference_objects(target_type_key)


def _form_context(
    request: Request,
    user: User,
    db: Session,
    *,
    source_obj: ArchitectureObject | None = None,
    rel=None,
    error: str | None = None,
    selected_choice: str | None = None,
    selected_target_id: str | None = None,
):
    source = rel.source_object if rel is not None else source_obj
    if source is None:
        raise ValueError("A source object is required")

    groups = _relationship_choice_groups(db, source)
    current_choice = ""
    current_target_id = ""
    if rel is not None:
        current_choice = f"{rel.relationship_type.key}|{rel.target_object.object_type.key}"
        current_target_id = rel.target_object_id

    selected_choice = selected_choice if selected_choice is not None else current_choice
    selected_target_id = selected_target_id if selected_target_id is not None else current_target_id
    targets = _targets_for_choice(db, groups, selected_choice)

    valid_types = [rel_type for rel_type, _ in groups]
    property_groups = {
        rel_type.key: _schema_fields(rel_type)
        for rel_type in valid_types
        if _schema_fields(rel_type)
    }

    return {
        "settings": get_settings(),
        "current_user": user,
        "csrf_token": get_csrf_token(request),
        "source_object": source,
        "relationship": rel,
        "relationship_choice_groups": groups,
        "selected_relationship_choice": selected_choice,
        "selected_target_id": selected_target_id,
        "property_groups": property_groups,
        "targets": targets,
        "criticalities": _enum_values(db, "criticality"),
        "confidences": _enum_values(db, "confidence"),
        "sources": _enum_values(db, "source"),
        "error": error,
    }


@router.get("/explore/{source_id}/relationships/new", response_class=HTMLResponse)
def new_relationship_page(
    source_id: str,
    request: Request,
    current_user: User = Depends(require_relationship_editor),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    source_obj = ObjectRepository(db).get_by_id(source_id)
    if source_obj is None:
        raise HTTPException(status_code=404, detail="Source object not found")
    return templates.TemplateResponse(
        request=request,
        name="relationships/form.html",
        context=_form_context(request, current_user, db, source_obj=source_obj),
    )


@router.get("/explore/{source_id}/relationships/targets")
def relationship_targets(
    source_id: str,
    relationship_choice: str = Query(...),
    _: User = Depends(require_relationship_editor),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, str]]]:
    source_obj = ObjectRepository(db).get_by_id(source_id)
    if source_obj is None:
        raise HTTPException(status_code=404, detail="Source object not found")

    groups = _relationship_choice_groups(db, source_obj)
    if not _choice_is_valid(groups, relationship_choice):
        raise HTTPException(status_code=422, detail="Invalid relationship choice for source object")

    targets = _targets_for_choice(db, groups, relationship_choice)
    return {
        "items": [
            {
                "id": target.id,
                "name": target.name,
                "object_type": target.object_type.name,
            }
            for target in targets
        ]
    }


@router.post("/explore/{source_id}/relationships/new", response_class=HTMLResponse)
async def create_relationship(
    source_id: str,
    request: Request,
    current_user: User = Depends(require_relationship_editor),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    source_obj = ObjectRepository(db).get_by_id(source_id)
    if source_obj is None:
        raise HTTPException(status_code=404, detail="Source object not found")

    choice = str(form.get("relationship_choice", ""))
    target_object_id = str(form.get("target_object_id", ""))
    relationship_key = choice.split("|", 1)[0] if "|" in choice else choice
    try:
        rel_type = db.query(RelationshipType).filter(RelationshipType.key == relationship_key).one_or_none()
        properties = _property_values(form, rel_type) if rel_type is not None else {}
        rel = RelationshipService(db).create_relationship(
            relationship_key=relationship_key,
            source_object_id=source_id,
            target_object_id=target_object_id,
            description=str(form.get("description", "")),
            criticality=str(form.get("criticality", "")) or None,
            confidence=str(form.get("confidence", "")) or None,
            valid_from=str(form.get("valid_from", "")) or None,
            valid_until=str(form.get("valid_until", "")) or None,
            source=str(form.get("source", "")) or None,
            properties=properties,
            actor=current_user,
        )
    except RelationshipServiceError as exc:
        return templates.TemplateResponse(
            request=request,
            name="relationships/form.html",
            context=_form_context(
                request,
                current_user,
                db,
                source_obj=source_obj,
                error=str(exc),
                selected_choice=choice,
                selected_target_id=target_object_id,
            ),
            status_code=400,
        )
    return RedirectResponse(
        f"/explore/{rel.source_object_id}?tab=relationships",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/relationships/{relationship_id}/edit", response_class=HTMLResponse)
def edit_relationship_page(
    relationship_id: str,
    request: Request,
    current_user: User = Depends(require_relationship_editor),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return templates.TemplateResponse(
        request=request,
        name="relationships/form.html",
        context=_form_context(request, current_user, db, rel=rel),
    )


@router.post("/relationships/{relationship_id}/edit", response_class=HTMLResponse)
async def edit_relationship(
    relationship_id: str,
    request: Request,
    current_user: User = Depends(require_relationship_editor),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")

    choice = str(form.get("relationship_choice", ""))
    target_object_id = str(form.get("target_object_id", ""))
    relationship_key = choice.split("|", 1)[0] if "|" in choice else choice
    try:
        rel_type = db.query(RelationshipType).filter(RelationshipType.key == relationship_key).one_or_none()
        properties = _property_values(form, rel_type) if rel_type is not None else {}
        RelationshipService(db).update_relationship(
            rel,
            relationship_key=relationship_key,
            target_object_id=target_object_id,
            description=str(form.get("description", "")),
            criticality=str(form.get("criticality", "")) or None,
            confidence=str(form.get("confidence", "")) or None,
            valid_from=str(form.get("valid_from", "")) or None,
            valid_until=str(form.get("valid_until", "")) or None,
            source=str(form.get("source", "")) or None,
            properties=properties,
            actor=current_user,
        )
    except RelationshipServiceError as exc:
        return templates.TemplateResponse(
            request=request,
            name="relationships/form.html",
            context=_form_context(
                request,
                current_user,
                db,
                rel=rel,
                error=str(exc),
                selected_choice=choice,
                selected_target_id=target_object_id,
            ),
            status_code=400,
        )
    return RedirectResponse(
        f"/explore/{rel.source_object_id}?tab=relationships",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/relationships/{relationship_id}/archive")
async def archive_relationship(
    relationship_id: str,
    request: Request,
    current_user: User = Depends(require_relationship_archiver),
    db: Session = Depends(get_db),
) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    rel = RelationshipRepository(db).get_by_id(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    source_id = rel.source_object_id
    RelationshipService(db).archive_relationship(rel, actor=current_user)
    return RedirectResponse(
        f"/explore/{source_id}?tab=relationships",
        status_code=status.HTTP_303_SEE_OTHER,
    )
