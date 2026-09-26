import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("openea.http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "route": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def apply_security_headers(
    response: Response, path: str, *, recaptcha_enabled: bool = False
) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if path in {"/docs", "/redoc"}:
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    elif path == "/login" and recaptcha_enabled:
        csp = (
            "default-src 'self'; "
            "style-src 'self'; "
            "script-src 'self' https://www.google.com/recaptcha/ "
            "https://www.gstatic.com/recaptcha/; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://www.google.com/recaptcha/; "
            "frame-src https://www.google.com/recaptcha/ "
            "https://recaptcha.google.com/recaptcha/; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    else:
        csp = (
            "default-src 'self'; "
            "style-src 'self'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    response.headers.setdefault("Content-Security-Policy", csp)
    return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        recaptcha_enabled = bool(getattr(request.state, "recaptcha_enabled", False))
        return apply_security_headers(
            response,
            request.url.path,
            recaptcha_enabled=recaptcha_enabled,
        )
