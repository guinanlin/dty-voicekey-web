import logging
import random
import re
from datetime import datetime, timezone

from fastapi import HTTPException, Request, status

from app.core.redis import redis_expire, redis_get, redis_incr, redis_setex, redis_ttl
from app.email import send_verification_code_email

logger = logging.getLogger(__name__)

CODE_TTL_SECONDS = 300
SEND_INTERVAL_SECONDS = 60

EMAIL_DAILY_LIMIT = 5
EMAIL_IP_HOURLY_LIMIT = 10
PHONE_DAILY_LIMIT = 10
PHONE_IP_HOURLY_LIMIT = 20

PHONE_PATTERN = re.compile(r"^1[3-9]\d{9}$")


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _client_ip(request: Request | None) -> str:
    if request is None:
        return "unknown"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def _check_send_interval(cooldown_key: str) -> None:
    ttl = await redis_ttl(cooldown_key)
    if ttl > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请 {ttl} 秒后再试",
        )


async def _check_daily_limit(daily_key: str, limit: int) -> None:
    count = await redis_incr(daily_key)
    if count == 1:
        await redis_expire(daily_key, 86400)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日发送次数已达上限",
        )


async def _check_ip_hourly_limit(ip_key: str, limit: int) -> None:
    count = await redis_incr(ip_key)
    if count == 1:
        await redis_expire(ip_key, 3600)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )


async def send_email_verification_code(
    email: str, scene: str, request: Request | None = None
) -> None:
    if scene not in {"register", "reset_password"}:
        raise HTTPException(status_code=400, detail="无效的场景")

    ip = _client_ip(request)
    await _check_send_interval(f"email_cooldown:{email}")
    await _check_daily_limit(f"email_daily:{email}:{_today_key()}", EMAIL_DAILY_LIMIT)
    await _check_ip_hourly_limit(f"email_ip:{ip}:{_hour_key()}", EMAIL_IP_HOURLY_LIMIT)

    code = _generate_code()
    code_key = f"email_code:{scene}:{email}"
    await redis_setex(code_key, CODE_TTL_SECONDS, code)
    await redis_setex(f"email_cooldown:{email}", SEND_INTERVAL_SECONDS, "1")
    await send_verification_code_email(email, code, scene)


async def send_phone_verification_code(
    phone: str, request: Request | None = None
) -> None:
    if not PHONE_PATTERN.match(phone):
        raise HTTPException(status_code=400, detail="手机号格式不正确")

    ip = _client_ip(request)
    await _check_send_interval(f"phone_cooldown:{phone}")
    await _check_daily_limit(f"phone_daily:{phone}:{_today_key()}", PHONE_DAILY_LIMIT)
    await _check_ip_hourly_limit(f"phone_ip:{ip}:{_hour_key()}", PHONE_IP_HOURLY_LIMIT)

    code = _generate_code()
    code_key = f"phone_code:{phone}"
    await redis_setex(code_key, CODE_TTL_SECONDS, code)
    await redis_setex(f"phone_cooldown:{phone}", SEND_INTERVAL_SECONDS, "1")
    logger.info("[Mock SMS] phone=%s code=%s", phone, code)
    print(f"[Mock SMS] phone={phone} code={code}")


async def verify_email_code(email: str, scene: str, code: str) -> None:
    stored = await redis_get(f"email_code:{scene}:{email}")
    if stored is None or stored != code:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")


async def verify_phone_code(phone: str, code: str) -> None:
    stored = await redis_get(f"phone_code:{phone}")
    if stored is None or stored != code:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")


async def check_rate_limit(user_id: str, endpoint: str, limit: int) -> None:
    minute_key = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"rate_limit:{user_id}:{endpoint}:{minute_key}"
    count = await redis_incr(key)
    if count == 1:
        await redis_expire(key, 60)
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _hour_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H")
