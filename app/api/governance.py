from __future__ import annotations

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
from app.models.user import User
from app.repositories.object_repository import ObjectRepository
from app.services.governance_service import GovernanceError, GovernanceService
from app.services.relationship_service import RelationshipService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")
require_governance_editor = require_roles(ARCHITECTURE_ADMIN, ARCHITECT)
require_reviewer = require_roles(ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR)


def _obj(db: Session, object_id: str):
    obj = ObjectRepository(db).get_by_id(object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


@router.post("/explore/{object_id}/governance")
async def transition(object_id: str, request: Request, current_user: User = Depends(require_governance_editor), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    try:
        GovernanceService(db).transition(_obj(db, object_id), str(form.get("status", "")), current_user)
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/explore/{object_id}?tab=lifecycle", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/explore/{object_id}/review")
async def review(object_id: str, request: Request, current_user: User = Depends(require_reviewer), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    try:
        GovernanceService(db).mark_reviewed(_obj(db, object_id), actor=current_user,
            notes=str(form.get("notes", "")), next_review_date=str(form.get("next_review_date", "")) or None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/explore/{object_id}?tab=lifecycle", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/explore/{object_id}/comments")
async def comment(object_id: str, request: Request, current_user: User = Depends(require_reviewer), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    try:
        GovernanceService(db).add_comment(_obj(db, object_id), actor=current_user, body=str(form.get("body", "")))
    except GovernanceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(f"/explore/{object_id}?tab=comments", status_code=status.HTTP_303_SEE_OTHER)



@router.get("/decisions", response_class=HTMLResponse)
def decisions_workspace(request: Request, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="decisions/index.html", context={
        "settings": get_settings(), "current_user": current_user, "csrf_token": get_csrf_token(request),
        "decisions": ObjectRepository(db).list_reference_objects("architecture_decision"),
    })

@router.get("/reviews", response_class=HTMLResponse)
def reviews_workspace(request: Request, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    service = GovernanceService(db)
    return templates.TemplateResponse(request=request, name="reviews/index.html", context={
        "settings": get_settings(), "current_user": current_user, "csrf_token": get_csrf_token(request),
        "attention_items": service.review_attention_items(),
    })


@router.post("/explore/{object_id}/supersede")
async def supersede(object_id: str, request: Request, current_user: User = Depends(require_governance_editor), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    old = _obj(db, object_id)
    new = _obj(db, str(form.get("replacement_id", "")))
    if old.object_type.key != "architecture_decision" or new.object_type.key != "architecture_decision" or old.id == new.id:
        raise HTTPException(status_code=400, detail="Superseding requires two different Architecture Decisions")
    if new.properties.get("decision_status") != "Accepted":
        raise HTTPException(status_code=400, detail="Replacement decision must be Accepted")
    RelationshipService(db).create_relationship(relationship_key="supersedes", source_object_id=new.id, target_object_id=old.id, actor=current_user)
    GovernanceService(db).transition(old, "Superseded", current_user)
    return RedirectResponse(f"/explore/{old.id}?tab=lifecycle", status_code=status.HTTP_303_SEE_OTHER)
