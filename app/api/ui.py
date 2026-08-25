from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token
from app.auth.permissions import get_current_user, require_authenticated
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def landing_page(
    request: Request, current_user: User | None = Depends(get_current_user)
) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    settings = get_settings()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "settings": settings,
            "current_user": current_user,
            "csrf_token": get_csrf_token(request),
            "repository_health": AnalyticsService(db).repository_health(),
        },
    )
