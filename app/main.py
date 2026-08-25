import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.api_auth_ui import router as api_auth_ui_router
from app.api.auth import router as auth_router
from app.api.explore import router as explore_router
from app.api.findings import router as findings_router
from app.api.governance import router as governance_router
from app.api.health import router as health_router
from app.api.impact import router as impact_router
from app.api.import_export import router as import_export_router
from app.api.portfolio import router as portfolio_router
from app.api.relationships import router as relationships_router
from app.api.ui import router as ui_router
from app.api.v1 import router as api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, SecurityHeadersMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("openea")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_starting", extra={"status": settings.app_version})
    yield
    logger.info("application_stopping")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie="openea_session",
        max_age=settings.session_max_age_seconds,
        same_site="lax",
        https_only=settings.secure_cookies,
    )
    app.mount("/static", StaticFiles(directory=Path("app/static")), name="static")
    app.include_router(health_router)
    app.include_router(api_v1_router)
    app.include_router(analytics_router)
    app.include_router(findings_router)
    app.include_router(impact_router)
    app.include_router(import_export_router)
    app.include_router(portfolio_router)
    app.include_router(auth_router)
    app.include_router(api_auth_ui_router)
    app.include_router(admin_router)
    app.include_router(governance_router)
    app.include_router(explore_router)
    app.include_router(relationships_router)
    app.include_router(ui_router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        if (
            exc.status_code == status.HTTP_401_UNAUTHORIZED
            and not request.url.path.startswith("/api/")
        ):
            return RedirectResponse(
                f"/login?next={request.url.path}", status_code=status.HTTP_303_SEE_OTHER
            )
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        if exc.status_code == status.HTTP_403_FORBIDDEN:
            return HTMLResponse(
                "<main><h1>Access denied</h1>"
                "<p>You do not have permission to access this page.</p></main>",
                status_code=403,
            )
        return HTMLResponse(
            f"<main><h1>Request failed</h1><p>{exc.detail}</p></main>",
            status_code=exc.status_code,
        )

    @app.exception_handler(404)
    async def not_found(request: Request, _: Exception):
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return HTMLResponse(
            "<main><h1>Page not found</h1><p>The requested page does not exist.</p></main>",
            status_code=404,
        )

    return app


app = create_app()
