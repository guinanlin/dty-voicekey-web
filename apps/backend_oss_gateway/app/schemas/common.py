import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend_oss_gateway"
