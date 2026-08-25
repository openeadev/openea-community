from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthenticationError, AuthenticationService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _safe_next(next_url: str | None) -> str:
    if not next_url:
        return "/dashboard"
    parsed = urlparse(next_url)
    if parsed.scheme or parsed.netloc or not next_url.startswith("/") or next_url.startswith("//"):
        return "/dashboard"
    return next_url


def _context(request: Request, **extra: object) -> dict[str, object]:
    return {
        "settings": get_settings(),
        "csrf_token": get_csrf_token(request),
        **extra,
    }


@router.get("/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)) -> Response:
    service = AuthenticationService(db)
    if not service.initial_setup_required():
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request, name="auth/setup.html", context=_context(request)
    )


@router.post("/setup", response_class=HTMLResponse)
def setup_submit(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    service = AuthenticationService(db)
    if not service.initial_setup_required():
        raise HTTPException(status_code=409, detail="Initial setup has already been completed")
    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="auth/setup.html",
            context=_context(
                request,
                error="Passwords do not match",
                username=username,
                display_name=display_name,
            ),
            status_code=400,
        )
    try:
        user = service.create_initial_admin(username, display_name, password)
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="auth/setup.html",
            context=_context(request, error=str(exc), username=username, display_name=display_name),
            status_code=400,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    next: str | None = None,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if AuthenticationService(db).initial_setup_required():
        return RedirectResponse("/setup", status_code=status.HTTP_303_SEE_OTHER)
    if current_user is not None:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context=_context(request, next=_safe_next(next)),
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next: str | None = Form(None),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        user = AuthenticationService(db).authenticate(username, password)
    except AuthenticationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context=_context(request, error=str(exc), username=username, next=_safe_next(next)),
            status_code=401,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(_safe_next(next), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
