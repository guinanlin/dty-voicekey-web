from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import ServiceAuthMiddleware, TraceIdMiddleware
from app.routes.v1.storage import (
    files_router,
    health,
    router as health_router,
    upload_router,
)

app = FastAPI(
    title="China Cloud Storage Gateway",
    description="Unified object storage gateway template for FastAPI backends",
    openapi_url=settings.OPENAPI_URL,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ServiceAuthMiddleware)
app.add_middleware(TraceIdMiddleware)

app.include_router(health_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")

# Re-export health for tests
__all__ = ["app", "health"]
