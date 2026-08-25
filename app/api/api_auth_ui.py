from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import require_authenticated, require_platform_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.token_service import API_SCOPES, TOKEN_EXPIRATIONS, TokenService

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _expiration(value: str) -> int | None:
    if value == "never":
        return None
    try:
        days = int(value)
    except ValueError as exc:
        raise ValueError("Invalid expiration") from exc
    if days not in TOKEN_EXPIRATIONS:
        raise ValueError("Invalid expiration")
    return days


def _base(request: Request, current_user: User, **extra: object) -> dict[str, object]:
    return {
        "request": request,
        "settings": get_settings(),
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "api_scopes": API_SCOPES,
        "expiration_options": [30, 60, 90, 180, 365],
        **extra,
    }


@router.get("/account/tokens", response_class=HTMLResponse)
def token_page(request: Request, current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="auth/tokens.html", context=_base(request, current_user, tokens=TokenService(db).list_for_user(current_user)))


@router.post("/account/tokens", response_class=HTMLResponse)
def create_pat(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    expiration: str = Form(...),
    scopes: list[str] = Form(default=[]),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_authenticated),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        created = TokenService(db).create_token(owner=current_user, name=name, scopes=scopes, expiration_days=_expiration(expiration), creator=current_user, description=description)
    except ValueError as exc:
        return templates.TemplateResponse(request=request, name="auth/tokens.html", context=_base(request, current_user, tokens=TokenService(db).list_for_user(current_user), error=str(exc)), status_code=400)
    return templates.TemplateResponse(request=request, name="auth/tokens.html", context=_base(request, current_user, tokens=TokenService(db).list_for_user(current_user), new_secret=created.secret))


@router.post("/account/tokens/{token_id}/revoke")
def revoke_pat(token_id: str, request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_authenticated), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    try:
        TokenService(db).revoke(token_id, requesting_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse("/account/tokens", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/service-accounts", response_class=HTMLResponse)
def service_accounts_page(request: Request, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="admin/service_accounts.html", context=_base(request, current_user, accounts=TokenService(db).list_service_accounts(), roles=UserRepository(db).list_roles()))


@router.post("/admin/service-accounts", response_class=HTMLResponse)
def create_service_account(
    request: Request,
    name: str = Form(...),
    roles: list[str] = Form(default=[]),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        account = TokenService(db).create_service_account(name=name, role_names=set(roles), creator=current_user)
    except ValueError as exc:
        return templates.TemplateResponse(request=request, name="admin/service_accounts.html", context=_base(request, current_user, accounts=TokenService(db).list_service_accounts(), roles=UserRepository(db).list_roles(), error=str(exc)), status_code=400)
    return RedirectResponse(f"/admin/service-accounts/{account.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/service-accounts/{account_id}", response_class=HTMLResponse)
def service_account_detail(account_id: str, request: Request, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> HTMLResponse:
    account = UserRepository(db).get_by_id(account_id)
    if account is None or not account.is_service_account:
        raise HTTPException(status_code=404, detail="Service account not found")
    return templates.TemplateResponse(request=request, name="admin/service_account_detail.html", context=_base(request, current_user, account=account, tokens=TokenService(db).list_for_user(account), roles=UserRepository(db).list_roles()))


@router.post("/admin/service-accounts/{account_id}")
def update_service_account(
    account_id: str, request: Request, roles: list[str] = Form(default=[]), is_active: str | None = Form(None),
    csrf_token: str = Form(...), current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db),
) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    account = UserRepository(db).get_by_id(account_id)
    if account is None or not account.is_service_account:
        raise HTTPException(status_code=404, detail="Service account not found")
    TokenService(db).update_service_account(account, role_names=set(roles), is_active=is_active is not None, actor=current_user)
    return RedirectResponse(f"/admin/service-accounts/{account_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/service-accounts/{account_id}/tokens", response_class=HTMLResponse)
def create_service_token(
    account_id: str,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    expiration: str = Form(...),
    scopes: list[str] = Form(default=[]),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    account = UserRepository(db).get_by_id(account_id)
    if account is None or not account.is_service_account:
        raise HTTPException(status_code=404, detail="Service account not found")
    try:
        created = TokenService(db).create_token(owner=account, name=name, scopes=scopes, expiration_days=_expiration(expiration), creator=current_user, description=description)
    except ValueError as exc:
        return templates.TemplateResponse(request=request, name="admin/service_account_detail.html", context=_base(request, current_user, account=account, tokens=TokenService(db).list_for_user(account), roles=UserRepository(db).list_roles(), error=str(exc)), status_code=400)
    return templates.TemplateResponse(request=request, name="admin/service_account_detail.html", context=_base(request, current_user, account=account, tokens=TokenService(db).list_for_user(account), roles=UserRepository(db).list_roles(), new_secret=created.secret))


@router.post("/admin/service-accounts/{account_id}/tokens/{token_id}/revoke")
def revoke_service_token(account_id: str, token_id: str, request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    TokenService(db).revoke(token_id, requesting_user=current_user, allow_any=True)
    return RedirectResponse(f"/admin/service-accounts/{account_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/admin/api-tokens", response_class=HTMLResponse)
def admin_tokens_page(request: Request, current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="admin/api_tokens.html", context=_base(request, current_user, tokens=TokenService(db).list_all()))


@router.post("/admin/api-tokens/{token_id}/revoke")
def admin_revoke_token(token_id: str, request: Request, csrf_token: str = Form(...), current_user: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> RedirectResponse:
    validate_csrf(request, csrf_token)
    try:
        TokenService(db).revoke(token_id, requesting_user=current_user, allow_any=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse("/admin/api-tokens", status_code=status.HTTP_303_SEE_OTHER)
