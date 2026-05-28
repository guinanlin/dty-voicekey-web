import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import settings

logger = logging.getLogger("app.middleware")


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.trace_id = trace_id
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = trace_id
        logger.info(
            "request_completed method=%s path=%s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            extra={"trace_id": trace_id},
        )
        return response


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    """Validate service-to-service token for /api/v1/* except health."""

    PUBLIC_PREFIXES = (
        "/api/v1/health",
        "/api/v1/upload/local/",
        "/api/v1/files/local/",
    )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if path in {"/docs", "/redoc", "/openapi.json"}:
            return await call_next(request)
        if any(path.startswith(p) for p in self.PUBLIC_PREFIXES):
            request.state.tenant_id = request.headers.get("X-Tenant-Id", "default")
            return await call_next(request)
        if not path.startswith("/api/v1"):
            return await call_next(request)

        token = request.headers.get("X-Service-Token")
        if not token or token not in settings.service_token_set:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing X-Service-Token"},
            )

        tenant_id = request.headers.get("X-Tenant-Id", "default")
        request.state.tenant_id = tenant_id
        return await call_next(request)
