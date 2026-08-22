from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.core.auth import optional_principal
from app.core.settings import get_settings
from app.services.operations.metrics import metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics(
    request: Request, authorization: str | None = Header(default=None)
) -> PlainTextResponse:
    settings = get_settings()
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled.")
    token = settings.metrics_internal_token
    if token:
        expected = f"Bearer {token}"
        if authorization != expected:
            raise HTTPException(status_code=403, detail="Metrics token required.")
    else:
        principal = await optional_principal(request)
        local = request.client and request.client.host in {"127.0.0.1", "testclient"}
        if not local and not (principal and principal.is_admin):
            # Local development default; set METRICS_INTERNAL_TOKEN before exposing this service.
            raise HTTPException(status_code=403, detail="Metrics are local-only without a token.")
    return PlainTextResponse(metrics.render_prometheus())
