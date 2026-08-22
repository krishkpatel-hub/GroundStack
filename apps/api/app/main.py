import re
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.services.operations.metrics import metrics
from app.services.operations.tracing import span

UUID_SEGMENT_RE = re.compile(
    r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def _safe_route_label(path: str) -> str:
    return UUID_SEGMENT_RE.sub("/{id}", path)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        route = _safe_route_label(request.url.path)
        status_code = 500
        with span("http.request", route=route, method=request.method):
            with metrics.timer(
                "groundstack_http_request_seconds", method=request.method, route=route
            ):
                try:
                    response = await call_next(request)
                    status_code = response.status_code
                    return response
                finally:
                    metrics.increment(
                        "groundstack_http_requests_total",
                        method=request.method,
                        route=route,
                        status=str(status_code),
                    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-groundstack-request-id") or str(uuid4())
        response = await call_next(request)
        response.headers["X-GroundStack-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; "
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response


class BodyLimitAndCsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_body_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": {"code": "request_too_large", "message": "Request body is too large."}
                },
            )
        if (
            request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and settings.session_cookie_name in request.cookies
            and request.url.path != "/api/v1/auth/logout"
        ):
            cookie = request.cookies.get(settings.csrf_cookie_name)
            header = request.headers.get(settings.csrf_header_name)
            if not cookie or header != cookie:
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": {"code": "csrf_failed", "message": "CSRF validation failed."}
                    },
                )
        return await call_next(request)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="GroundStack developer-support API.",
        docs_url="/docs"
        if settings.docs_enabled and settings.app_env not in {"demo", "production"}
        else None,
        redoc_url="/redoc"
        if settings.docs_enabled and settings.app_env not in {"demo", "production"}
        else None,
        openapi_url="/openapi.json"
        if settings.docs_enabled and settings.app_env not in {"demo", "production"}
        else None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(BodyLimitAndCsrfMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
