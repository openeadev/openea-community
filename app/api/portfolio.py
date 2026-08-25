from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token
from app.auth.permissions import require_authenticated
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.portfolio_service import PortfolioService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _context(request: Request, current_user: User) -> dict[str, object]:
    return {"settings": get_settings(), "current_user": current_user, "csrf_token": get_csrf_token(request)}


@router.get("/portfolio", response_class=HTMLResponse)
def portfolio_home(request: Request, current_user: User = Depends(require_authenticated)) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="portfolio/index.html", context=_context(request, current_user))


@router.get("/portfolio/applications", response_class=HTMLResponse)
def application_portfolio(request: Request, lifecycle: str | None = None, risk_band: str | None = None, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    context = _context(request, current_user)
    context.update({"lifecycle": lifecycle or "", "risk_band": risk_band or ""})
    context["rows"] = PortfolioService(db).application_portfolio(lifecycle=lifecycle, risk_band=risk_band)
    return templates.TemplateResponse(request=request, name="portfolio/applications.html", context=context)


@router.get("/portfolio/technologies", response_class=HTMLResponse)
def technology_portfolio(request: Request, lifecycle: str | None = None, strategic_status: str | None = None, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    context = _context(request, current_user)
    context.update({"lifecycle": lifecycle or "", "strategic_status": strategic_status or ""})
    context["rows"] = PortfolioService(db).technology_portfolio(lifecycle=lifecycle, strategic_status=strategic_status)
    return templates.TemplateResponse(request=request, name="portfolio/technologies.html", context=context)


@router.get("/portfolio/capabilities", response_class=HTMLResponse)
def capability_map(request: Request, overlay: str = "capability_risk", current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    allowed = {"capability_risk", "application_risk", "technology_risk", "maturity", "strategic_importance", "application_count"}
    if overlay not in allowed:
        overlay = "capability_risk"
    context = _context(request, current_user)
    context["overlay"] = overlay
    context["roots"] = PortfolioService(db).capability_map()
    return templates.TemplateResponse(request=request, name="portfolio/capabilities.html", context=context)


@router.get("/roadmaps", response_class=HTMLResponse)
def roadmaps(request: Request, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    context = _context(request, current_user)
    context["items"] = PortfolioService(db).roadmaps()
    return templates.TemplateResponse(request=request, name="portfolio/roadmaps.html", context=context)
