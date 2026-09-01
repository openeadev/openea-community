from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token
from app.auth.permissions import require_authenticated
from app.core.config import get_settings
from app.db.session import get_db
from app.models.analytics import ObjectMetric
from app.models.metamodel import ArchitectureObject
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/analytics", response_class=HTMLResponse)
def analytics_dashboard(
    request: Request,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = AnalyticsService(db)
    health = service.repository_health()
    top_risks = list(
        db.scalars(
            select(ObjectMetric)
            .where(ObjectMetric.metric_type.in_(["application_risk", "technology_risk", "capability_risk"]))
            .order_by(ObjectMetric.score.desc())
            .limit(12)
        ).unique().all()
    )
    return templates.TemplateResponse(
        request=request,
        name="analytics/index.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "health": health,
            "top_risks": top_risks,
        },
    )


@router.get("/analytics/health/{dimension}", response_class=HTMLResponse)
def repository_health_dimension(
    dimension: str,
    request: Request,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    try:
        detail = AnalyticsService(db).repository_health_dimension(dimension)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="analytics/health_dimension.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "detail": detail,
        },
    )


@router.get("/analytics/objects/{object_id}", response_class=HTMLResponse)
def object_metrics(
    object_id: str,
    request: Request,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    obj = db.get(ArchitectureObject, object_id)
    if obj is None or obj.archived_at is not None:
        raise HTTPException(status_code=404, detail="Object not found")
    service = AnalyticsService(db)
    metrics = service.metrics_for_object(object_id)
    return templates.TemplateResponse(
        request=request,
        name="analytics/object.html",
        context={
            "settings": get_settings(),
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "object": obj,
            "metric_views": [service.metric_view(metric) for metric in metrics],
        },
    )
