import hashlib
import json
import logging
from app.db.redis_client import get_redis

logger = logging.getLogger("rankforge.cache")


def make_cache_key(prefix: str, payload: dict | str) -> str:
    raw = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"{prefix}:{digest}"


async def get_cached_json(key: str) -> dict | list | None:
    client = get_redis()
    if client is None:
        return None
    try:
        val = await client.get(key)
        return json.loads(val) if val else None
    except Exception as exc:
        logger.warning("Redis GET failed (failing open): %s", exc)
        return None


async def set_cached_json(key: str, data: dict | list, ttl_seconds: int) -> None:
    client = get_redis()
    if client is None:
        return
    try:
        await client.set(key, json.dumps(data), ex=ttl_seconds)
    except Exception as exc:
        logger.warning("Redis SET failed (failing open): %s", exc)
