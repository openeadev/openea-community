from app.services.scheduled_job_service import ScheduledJobService
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.csrf import get_csrf_token, validate_csrf
from app.auth.permissions import require_platform_admin
from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthenticationService

router = APIRouter(prefix="/admin", include_in_schema=False)
templates = Jinja2Templates(directory="app/templates")


def _context(
    request: Request, current_user: User, db: Session, **extra: object
) -> dict[str, object]:
    repo = UserRepository(db)
    return {
        "settings": get_settings(),
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "roles": repo.list_roles(),
        **extra,
    }


@router.get("/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context=_context(request, current_user, db, users=UserRepository(db).list_users()),
    )


@router.get("/users/new", response_class=HTMLResponse)
def new_user_page(
    request: Request,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="admin/user_form.html",
        context=_context(request, current_user, db, user=None, selected_roles=set()),
    )


@router.post("/users/new", response_class=HTMLResponse)
def create_user_submit(
    request: Request,
    username: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    roles: list[str] = Form(default=[]),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        AuthenticationService(db).create_user(username, display_name, password, set(roles), actor=current_user)
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="admin/user_form.html",
            context=_context(
                request,
                current_user,
                db,
                user=None,
                error=str(exc),
                username=username,
                display_name=display_name,
                selected_roles=set(roles),
            ),
            status_code=400,
        )
    return RedirectResponse("/admin/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/users/{user_id}", response_class=HTMLResponse)
def edit_user_page(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(
        request=request,
        name="admin/user_form.html",
        context=_context(
            request,
            current_user,
            db,
            user=user,
            selected_roles={role.name for role in user.roles},
        ),
    )


@router.post("/users/{user_id}", response_class=HTMLResponse)
def edit_user_submit(
    user_id: str,
    request: Request,
    display_name: str = Form(...),
    is_active: str | None = Form(None),
    new_password: str = Form(""),
    roles: list[str] = Form(default=[]),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and (
        is_active is None or "Platform Administrator" not in set(roles)
    ):
        return templates.TemplateResponse(
            request=request,
            name="admin/user_form.html",
            context=_context(
                request,
                current_user,
                db,
                user=user,
                error=(
                    "You cannot deactivate your own account or remove your "
                    "Platform Administrator role"
                ),
                selected_roles=set(roles),
            ),
            status_code=400,
        )
    try:
        AuthenticationService(db).update_user(
            user,
            display_name,
            is_active=is_active is not None,
            role_names=set(roles),
            new_password=new_password or None,
            actor=current_user,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="admin/user_form.html",
            context=_context(
                request,
                current_user,
                db,
                user=user,
                error=str(exc),
                selected_roles=set(roles),
            ),
            status_code=400,
        )
    return RedirectResponse("/admin/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/background-processing", response_class=HTMLResponse)
def background_processing_page(
    request: Request,
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    service = ScheduledJobService(db)
    processes = [service.view(setting) for setting in service.list_settings()]
    return templates.TemplateResponse(
        request=request,
        name="admin/background_processing.html",
        context=_context(
            request,
            current_user,
            db,
            processes=processes,
            interval_options=service.interval_options(),
        ),
    )


@router.post("/background-processing/{job_key}", response_class=HTMLResponse)
def update_background_processing(
    job_key: str,
    request: Request,
    interval_minutes: int = Form(...),
    enabled: str | None = Form(None),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    service = ScheduledJobService(db)
    try:
        service.update(
            job_key,
            enabled=enabled is not None,
            interval_minutes=interval_minutes,
            actor=current_user,
        )
    except ValueError as exc:
        processes = [service.view(setting) for setting in service.list_settings()]
        return templates.TemplateResponse(
            request=request,
            name="admin/background_processing.html",
            context=_context(
                request,
                current_user,
                db,
                processes=processes,
                interval_options=service.interval_options(),
                error=str(exc),
            ),
            status_code=400,
        )
    return RedirectResponse(
        "/admin/background-processing?updated=1", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/background-processing/{job_key}/run", response_class=HTMLResponse)
def run_background_processing_now(
    job_key: str,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(require_platform_admin),
    db: Session = Depends(get_db),
) -> Response:
    validate_csrf(request, csrf_token)
    try:
        ScheduledJobService(db).run_now(job_key, actor=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RedirectResponse(
        "/admin/background-processing?queued=1", status_code=status.HTTP_303_SEE_OTHER
    )
