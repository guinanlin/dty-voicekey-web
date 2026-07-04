import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.schemas import SmsForwardInboundRequest
from app.service.sms_forward_service import (
    _error_response,
    process_inbound_sms,
    resolve_webhook_user,
    validate_headers,
    validate_payload,
)
from app.service.verification_service import check_rate_limit

router = APIRouter(tags=["sms-forward"])


@router.get("/health")
async def inbound_health():
    return JSONResponse(
        status_code=200,
        content={"ok": True, "service": "sms-forward-inbound"},
    )


@router.post("/inbound")
async def sms_inbound(
    payload: SmsForwardInboundRequest,
    db: AsyncSession = Depends(get_async_session),
    x_api_key: str | None = Header(default=None, alias="x-api-key"),
    x_sms_forward_version: str | None = Header(
        default=None, alias="X-Sms-Forward-Version"
    ),
    x_sms_forward_message_id: str | None = Header(
        default=None, alias="X-Sms-Forward-Message-Id"
    ),
    x_sms_forward_device_id: str | None = Header(
        default=None, alias="X-Sms-Forward-Device-Id"
    ),
    x_sms_forward_rule_id: str | None = Header(
        default=None, alias="X-Sms-Forward-Rule-Id"
    ),
):
    request_id = str(uuid.uuid4())

    user = await resolve_webhook_user(db, x_api_key)
    if isinstance(user, JSONResponse):
        return user

    try:
        await check_rate_limit(str(user.id), "sms_inbound", 100)
    except HTTPException:
        return _error_response(
            status_code=429,
            code="RATE_LIMITED",
            message="Too many requests, retry later",
            retry_after_ms=60000,
            request_id=request_id,
        )

    header_error = validate_headers(
        payload,
        x_sms_forward_message_id,
        x_sms_forward_device_id,
        x_sms_forward_rule_id,
        x_sms_forward_version,
    )
    if header_error:
        return header_error

    payload_error = validate_payload(payload)
    if payload_error:
        return payload_error

    try:
        return await process_inbound_sms(db, user, payload, request_id=request_id)
    except Exception:
        return _error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Internal server error",
            request_id=request_id,
        )
