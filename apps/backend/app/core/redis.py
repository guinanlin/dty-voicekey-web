import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None
_memory_store: dict[str, tuple[str, float]] = {}


def use_memory_store() -> bool:
    return settings.REDIS_URL in ("memory://", "memory")


async def get_redis() -> aioredis.Redis | None:
    global _redis_client
    if use_memory_store():
        return None
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client


async def redis_get(key: str) -> str | None:
    client = await get_redis()
    if client is None:
        entry = _memory_store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        import time

        if time.time() > expires_at:
            _memory_store.pop(key, None)
            return None
        return value
    return await client.get(key)


async def redis_setex(key: str, ttl: int, value: str) -> None:
    client = await get_redis()
    if client is None:
        import time

        _memory_store[key] = (value, time.time() + ttl)
        return
    await client.setex(key, ttl, value)


async def redis_incr(key: str) -> int:
    client = await get_redis()
    if client is None:
        current = _memory_store.get(key)
        count = int(current[0]) + 1 if current else 1
        import time

        _memory_store[key] = (str(count), time.time() + 86400)
        return count
    return await client.incr(key)


async def redis_expire(key: str, ttl: int) -> None:
    client = await get_redis()
    if client is None:
        return
    await client.expire(key, ttl)


async def redis_ttl(key: str) -> int:
    client = await get_redis()
    if client is None:
        entry = _memory_store.get(key)
        if entry is None:
            return -2
        import time

        remaining = int(entry[1] - time.time())
        return max(remaining, 0)
    return await client.ttl(key)


def clear_memory_store() -> None:
    _memory_store.clear()
