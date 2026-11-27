import time
from fastapi import HTTPException, Request, Response
from app.db.redis_client import get_redis

SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]

redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local current = redis.call('ZCARD', key)
if current >= limit then
    return {0, 0}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window)
return {1, limit - current - 1}
"""


async def rate_limit_dependency(
    request: Request, response: Response, limit_rpm: int = 120
) -> None:
    client = get_redis()
    if client is None:
        return

    client_id = request.headers.get("X-API-Key") or (
        request.client.host if request.client else "unknown"
    )
    key = f"ratelimit:{client_id}"
    now_ms = int(time.time() * 1000)
    window_ms = 60_000
    member = f"{now_ms}-{id(request)}"

    try:
        allowed, remaining = await client.eval(
            SLIDING_WINDOW_LUA, 1, key, now_ms, window_ms, limit_rpm, member
        )
        response.headers["X-RateLimit-Limit"] = str(limit_rpm)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Try again in a minute.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception:
        return
