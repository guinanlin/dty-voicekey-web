import hashlib
import time
from datetime import datetime, timezone
from uuid import UUID

from fastapi import Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.model.base_model import User
from app.model.sms_model import SmsMessage, utcnow
from app.schemas import SmsForwardInboundRequest

PROTOCOL_VERSION = "1.0.0"
MAX_BODY_CHARS = 4000


class SmsForwardSuccessResponse(BaseModel):
    ok: bool = True
    code: str
    message: str | None = None
    serverTime: int
    duplicate: bool = False


class SmsForwardErrorResponse(BaseModel):
    ok: bool = False
    code: str
    message: str | None = None
    retryAfterMs: int | None = None


def _server_time_ms() -> int:
    return int(time.time() * 1000)


def _timestamp_ms_to_datetime(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def _success_response(
    *, duplicate: bool, request_id: str | None = None
) -> JSONResponse:
    body = SmsForwardSuccessResponse(
        ok=True,
        code="DUPLICATE" if duplicate else "ACCEPTED",
        message="Message already processed" if duplicate else "SMS received",
        serverTime=_server_time_ms(),
        duplicate=duplicate,
    )
    headers = {}
    if request_id:
        headers["X-Request-Id"] = request_id
    return JSONResponse(status_code=200, content=body.model_dump(), headers=headers)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    retry_after_ms: int | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    body = SmsForwardErrorResponse(
        ok=False, code=code, message=message, retryAfterMs=retry_after_ms
    )
    headers = {}
    if request_id:
        headers["X-Request-Id"] = request_id
    if retry_after_ms and status_code == 429:
        headers["Retry-After"] = str(max(retry_after_ms // 1000, 1))
    return JSONResponse(
        status_code=status_code, content=body.model_dump(), headers=headers
    )


async def resolve_webhook_user(
    db: AsyncSession, x_api_key: str | None
) -> User | JSONResponse:
    if not x_api_key:
        if settings.SMS_FORWARD_REQUIRE_API_KEY:
            return _error_response(
                status_code=401,
                code="UNAUTHORIZED",
                message="Missing x-api-key header",
            )
        result = await db.execute(
            select(User).where(User.email == settings.SMS_FORWARD_DEFAULT_USER_EMAIL)
        )
        user = result.scalar_one_or_none()
        if user is None:
            return _error_response(
                status_code=401,
                code="UNAUTHORIZED",
                message="Default webhook user not configured",
            )
        return user

    result = await db.execute(
        select(User).where(User.webhook_api_key == x_api_key, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        return _error_response(
            status_code=401,
            code="UNAUTHORIZED",
            message="Invalid x-api-key",
        )
    return user


def validate_headers(
    payload: SmsForwardInboundRequest,
    x_sms_forward_message_id: str | None,
    x_sms_forward_device_id: str | None,
    x_sms_forward_rule_id: str | None,
    x_sms_forward_version: str | None,
) -> JSONResponse | None:
    if x_sms_forward_version and x_sms_forward_version != PROTOCOL_VERSION:
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message=f"Unsupported protocol version: {x_sms_forward_version}",
        )
    if x_sms_forward_message_id and x_sms_forward_message_id != str(payload.id):
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message="X-Sms-Forward-Message-Id mismatch with body.id",
        )
    if x_sms_forward_device_id and x_sms_forward_device_id != payload.device.id:
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message="X-Sms-Forward-Device-Id mismatch with device.id",
        )
    if x_sms_forward_rule_id and x_sms_forward_rule_id != str(payload.rule.id):
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message="X-Sms-Forward-Rule-Id mismatch with rule.id",
        )
    return None


def validate_payload(payload: SmsForwardInboundRequest) -> JSONResponse | None:
    if payload.event != "sms.received":
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message=f"Unsupported event: {payload.event}",
        )
    if payload.version != PROTOCOL_VERSION:
        return _error_response(
            status_code=400,
            code="BAD_REQUEST",
            message=f"Unsupported version: {payload.version}",
        )
    if not payload.message.body or not payload.message.body.strip():
        return _error_response(
            status_code=422,
            code="UNPROCESSABLE",
            message="message.body must not be empty",
        )
    if len(payload.message.body) > MAX_BODY_CHARS:
        return _error_response(
            status_code=413,
            code="PAYLOAD_TOO_LARGE",
            message=f"message.body exceeds {MAX_BODY_CHARS} characters",
        )
    actual_sha = hashlib.sha256(payload.message.body.encode("utf-8")).hexdigest()
    if payload.meta.contentSha256.lower() != actual_sha:
        return _error_response(
            status_code=422,
            code="UNPROCESSABLE",
            message="contentSha256 mismatch",
        )
    if payload.meta.contentLength != len(payload.message.body.encode("utf-8")):
        return _error_response(
            status_code=422,
            code="UNPROCESSABLE",
            message="contentLength mismatch",
        )
    return None


async def process_inbound_sms(
    db: AsyncSession,
    user: User,
    payload: SmsForwardInboundRequest,
    request_id: str | None = None,
) -> JSONResponse:
    existing = await db.execute(
        select(SmsMessage).where(
            SmsMessage.forward_id == payload.id,
            SmsMessage.deleted.is_(False),
        )
    )
    if existing.scalar_one_or_none() is not None:
        return _success_response(duplicate=True, request_id=request_id)

    sms = SmsMessage(
        forward_id=payload.id,
        user_id=user.id,
        phone=payload.message.from_.strip(),
        content=payload.message.body,
        received_at=_timestamp_ms_to_datetime(payload.message.timestamp),
        source="webhook",
        device_id=payload.device.id,
        rule_id=payload.rule.id,
        content_sha256=payload.meta.contentSha256.lower(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(sms)
    await db.commit()
    return _success_response(duplicate=False, request_id=request_id)
