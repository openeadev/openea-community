from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
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
from app.models.findings import Finding, RuleDefinition
from app.models.metamodel import ObjectType, RelationshipType
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.custom_rule_service import (
    DATE_MODES,
    DIRECTIONS,
    METRIC_TYPES,
    SEVERITIES,
    SUPPORTED_RULE_TYPES,
    CustomRuleService,
    CustomRuleValidationError,
)
from app.services.findings_service import FINDING_STATUSES, FindingsService
from app.services.job_service import JobService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _rule_context(db: Session, rule: RuleDefinition | None = None, *, error: str | None = None, form_values: dict[str, object] | None = None) -> dict[str, object]:
    object_types = list(db.scalars(select(ObjectType).where(ObjectType.is_active.is_(True)).order_by(ObjectType.domain, ObjectType.name)).all())
    relationship_types = list(db.scalars(select(RelationshipType).where(RelationshipType.is_active.is_(True)).order_by(RelationshipType.name)).all())
    return {
        "settings": get_settings(),
        "rule": rule,
        "object_types": object_types,
        "relationship_types": relationship_types,
        "rule_types": SUPPORTED_RULE_TYPES,
        "severities": SEVERITIES,
        "directions": DIRECTIONS,
        "date_modes": DATE_MODES,
        "metric_types": METRIC_TYPES,
        "error": error,
        "form_values": form_values or {},
    }


def _form_payload(form: object) -> dict[str, object]:
    # Starlette FormData exposes getlist; keep this adapter small so validation remains in the service.
    getlist = form.getlist
    get = form.get
    return {
        "name": get("name", ""),
        "description": get("description", ""),
        "rule_type": get("rule_type", ""),
        "severity": get("severity", "Medium"),
        "enabled": get("enabled") == "on",
        "object_types": getlist("object_types"),
        "field_name": get("field_name", ""),
        "date_mode": get("date_mode", "within"),
        "days": get("days", ""),
        "relationship": get("relationship", ""),
        "direction": get("direction", "outbound"),
        "source_type": get("source_type", ""),
        "target_type": get("target_type", ""),
        "min_count": get("min_count", ""),
        "max_count": get("max_count", ""),
        "related_type": get("related_type", ""),
        "object_lifecycle": get("object_lifecycle", ""),
        "related_property": get("related_property", ""),
        "related_values": get("related_values", ""),
        "lifecycle_values": get("lifecycle_values", ""),
        "metric_type": get("metric_type", ""),
        "threshold": get("threshold", ""),
        "criticality": get("criticality", ""),
    }


@router.get("/findings", response_class=HTMLResponse)
def findings_dashboard(request: Request, status_filter: str = "current", severity: str = "", current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    stmt = select(Finding).order_by(Finding.detected_at.desc())
    if status_filter == "current":
        stmt = stmt.where(Finding.status != "Resolved")
    elif status_filter and status_filter != "all":
        stmt = stmt.where(Finding.status == status_filter)
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    findings = list(db.scalars(stmt).unique().all())
    return templates.TemplateResponse(
        request=request,
        name="findings/index.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "findings": findings,
            "statuses": FINDING_STATUSES,
            "status_filter": status_filter,
            "severity_filter": severity,
        },
    )


@router.get("/findings/{finding_id}", response_class=HTMLResponse)
def finding_detail(finding_id: str, request: Request, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    users = UserRepository(db).list_users()
    return templates.TemplateResponse(request=request, name="findings/detail.html", context={"settings": get_settings(), "current_user": current_user, "csrf_token": get_csrf_token(request), "finding": finding, "statuses": FINDING_STATUSES, "users": users})


@router.post("/findings/{finding_id}/status")
def update_finding_status(finding_id: str, request: Request, status: str = Form(...), notes: str = Form(""), dismissal_reason: str = Form(""), assigned_user_id: str = Form(""), assigned_role: str = Form(""), csrf_token: str = Form(...), current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN, ARCHITECT, CONTRIBUTOR)), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    try:
        FindingsService(db).update_status(finding, status=status, actor=current_user, notes=notes, dismissal_reason=dismissal_reason, assigned_user_id=assigned_user_id or None, assigned_role=assigned_role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(f"/findings/{finding_id}", status_code=303)


@router.post("/findings/evaluate")
def evaluate_findings(request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN, ARCHITECT)), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    JobService(db).enqueue_findings_evaluation(correlation_id=f"user:{current_user.id}")
    db.commit()
    return RedirectResponse("/findings", status_code=303)


@router.get("/admin/finding-rules", response_class=HTMLResponse)
def finding_rules(request: Request, current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> HTMLResponse:
    rules = list(db.scalars(select(RuleDefinition).where(RuleDefinition.archived_at.is_(None)).order_by(RuleDefinition.is_system.desc(), RuleDefinition.rule_id)).all())
    return templates.TemplateResponse(request=request, name="findings/rules.html", context={"settings": get_settings(), "current_user": current_user, "csrf_token": get_csrf_token(request), "rules": rules})


@router.get("/admin/finding-rules/new", response_class=HTMLResponse)
def new_finding_rule(request: Request, current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> HTMLResponse:
    context = _rule_context(db)
    context.update({"current_user": current_user, "csrf_token": get_csrf_token(request)})
    return templates.TemplateResponse(request=request, name="findings/rule_form.html", context=context)


@router.post("/admin/finding-rules/new", response_class=HTMLResponse)
async def create_finding_rule(request: Request, current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> Response:
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    payload = _form_payload(form)
    try:
        CustomRuleService(db).create_rule(payload=payload, actor=current_user)
    except CustomRuleValidationError as exc:
        context = _rule_context(db, error=str(exc), form_values=payload)
        context.update({"current_user": current_user, "csrf_token": get_csrf_token(request)})
        return templates.TemplateResponse(request=request, name="findings/rule_form.html", context=context, status_code=422)
    JobService(db).enqueue_findings_evaluation(correlation_id=f"rule-create:{current_user.id}")
    db.commit()
    return RedirectResponse("/admin/finding-rules", status_code=303)


@router.get("/admin/finding-rules/{rule_id}/edit", response_class=HTMLResponse)
def edit_finding_rule(rule_id: str, request: Request, current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> HTMLResponse:
    rule = db.get(RuleDefinition, rule_id)
    if rule is None or rule.archived_at is not None:
        raise HTTPException(status_code=404, detail="Rule not found")
    context = _rule_context(db, rule=rule)
    context.update({"current_user": current_user, "csrf_token": get_csrf_token(request)})
    return templates.TemplateResponse(request=request, name="findings/rule_form.html", context=context)


@router.post("/admin/finding-rules/{rule_id}/edit", response_class=HTMLResponse)
async def update_finding_rule(rule_id: str, request: Request, current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> Response:
    rule = db.get(RuleDefinition, rule_id)
    if rule is None or rule.archived_at is not None:
        raise HTTPException(status_code=404, detail="Rule not found")
    form = await request.form()
    validate_csrf(request, str(form.get("csrf_token", "")))
    payload = _form_payload(form)
    try:
        CustomRuleService(db).update_rule(rule, payload=payload, actor=current_user)
    except CustomRuleValidationError as exc:
        context = _rule_context(db, rule=rule, error=str(exc), form_values=payload)
        context.update({"current_user": current_user, "csrf_token": get_csrf_token(request)})
        return templates.TemplateResponse(request=request, name="findings/rule_form.html", context=context, status_code=422)
    JobService(db).enqueue_findings_evaluation(correlation_id=f"rule-update:{current_user.id}")
    db.commit()
    return RedirectResponse("/admin/finding-rules", status_code=303)


@router.post("/admin/finding-rules/{rule_id}/toggle")
def toggle_rule(rule_id: str, request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    rule = db.get(RuleDefinition, rule_id)
    if rule is None or rule.archived_at is not None:
        raise HTTPException(status_code=404, detail="Rule not found")
    FindingsService(db).set_rule_enabled(rule, not rule.enabled, current_user)
    JobService(db).enqueue_findings_evaluation(correlation_id=f"rule-toggle:{current_user.id}")
    db.commit()
    return RedirectResponse("/admin/finding-rules", status_code=303)


@router.post("/admin/finding-rules/{rule_id}/delete")
def delete_custom_rule(rule_id: str, request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_roles(ARCHITECTURE_ADMIN)), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    rule = db.get(RuleDefinition, rule_id)
    if rule is None or rule.archived_at is not None:
        raise HTTPException(status_code=404, detail="Rule not found")
    try:
        CustomRuleService(db).archive_custom_rule(rule, actor=current_user)
    except CustomRuleValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    JobService(db).enqueue_findings_evaluation(correlation_id=f"rule-delete:{current_user.id}")
    db.commit()
    return RedirectResponse("/admin/finding-rules", status_code=303)
