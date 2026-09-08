import json
import logging
from typing import Any

import redis.asyncio as aioredis

from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def get_cached_json(key: str) -> Any | None:
    try:
        client = get_redis_client()
        cached = await client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as exc:
        logger.warning("Redis cache read failure for key %s: %s", key, exc)
    return None


async def set_cached_json(key: str, data: Any, ttl_seconds: int = 180) -> None:
    try:
        client = get_redis_client()
        serialized = json.dumps(data, default=str)
        await client.set(key, serialized, ex=ttl_seconds)
    except Exception as exc:
        logger.warning("Redis cache write failure for key %s: %s", key, exc)


async def invalidate_cache_pattern(pattern: str) -> None:
    try:
        client = get_redis_client()
        keys = await client.keys(pattern)
        if keys:
            await client.delete(*keys)
    except Exception as exc:
        logger.warning("Redis cache invalidation failure for pattern %s: %s", pattern, exc)
