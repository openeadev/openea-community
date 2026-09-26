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
from app.services.application_setting_service import ApplicationSettingService
from app.services.auth_service import AuthenticationError, AuthenticationService
from app.services.recaptcha_service import RecaptchaService, RecaptchaVerificationUnavailable

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


LOGIN_SECURITY_UNAVAILABLE = (
    "Login security is temporarily unavailable. Please try again later or contact an administrator."
)


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


def _login_context(request: Request, db: Session, **extra: object) -> dict[str, object]:
    settings = get_settings()
    recaptcha_enabled = ApplicationSettingService(db).recaptcha_enabled()
    recaptcha_configured = settings.recaptcha_configured
    request.state.recaptcha_enabled = recaptcha_enabled and recaptcha_configured
    return _context(
        request,
        recaptcha_enabled=recaptcha_enabled,
        recaptcha_configured=recaptcha_configured,
        recaptcha_site_key=(
            settings.recaptcha_site_key if recaptcha_enabled and recaptcha_configured else ""
        ),
        **extra,
    )


def _login_response(
    request: Request,
    db: Session,
    *,
    error: str,
    username: str = "",
    next_url: str | None = None,
    status_code: int,
    login_blocked: bool = False,
) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context=_login_context(
            request,
            db,
            error=error,
            username=username,
            next=_safe_next(next_url),
            login_blocked=login_blocked,
        ),
        status_code=status_code,
    )


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

    settings = get_settings()
    recaptcha_enabled = ApplicationSettingService(db).recaptcha_enabled()
    error = LOGIN_SECURITY_UNAVAILABLE if recaptcha_enabled and not settings.recaptcha_configured else None
    return templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context=_login_context(
            request,
            db,
            next=_safe_next(next),
            error=error,
            login_blocked=bool(error),
        ),
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE if error else status.HTTP_200_OK,
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    next: str | None = Form(None),
    recaptcha_response: str | None = Form(None, alias="g-recaptcha-response"),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)

    application_settings = ApplicationSettingService(db)
    if application_settings.recaptcha_enabled():
        settings = get_settings()
        if not settings.recaptcha_configured:
            return _login_response(
                request,
                db,
                error=LOGIN_SECURITY_UNAVAILABLE,
                username=username,
                next_url=next,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                login_blocked=True,
            )
        if not recaptcha_response:
            return _login_response(
                request,
                db,
                error="Please complete the security challenge before signing in.",
                username=username,
                next_url=next,
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        try:
            verification = RecaptchaService().verify(recaptcha_response)
        except RecaptchaVerificationUnavailable:
            return _login_response(
                request,
                db,
                error="We could not verify the security challenge. Please try again.",
                username=username,
                next_url=next,
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not verification.success:
            return _login_response(
                request,
                db,
                error="Security challenge verification failed. Please try again.",
                username=username,
                next_url=next,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    try:
        user = AuthenticationService(db).authenticate(username, password)
    except AuthenticationError as exc:
        return _login_response(
            request,
            db,
            error=str(exc),
            username=username,
            next_url=next,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(_safe_next(next), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
