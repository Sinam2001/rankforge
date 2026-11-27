from app.db.redis_client import get_redis

AUTOCOMPLETE_KEY = "autocomplete:titles"


async def index_autocomplete_term(title: str) -> None:
    client = get_redis()
    if client is None:
        return
    normalized = title.strip().lower()
    if not normalized:
        return
    try:
        await client.zadd(AUTOCOMPLETE_KEY, {f"{normalized}::{title.strip()}": 0})
    except Exception:
        pass


async def suggest_prefixes(prefix: str, limit: int = 6) -> list[str]:
    client = get_redis()
    clean = prefix.strip().lower()
    if client is None or not clean:
        return []
    try:
        raw_matches = await client.zrangebylex(
            AUTOCOMPLETE_KEY,
            min=f"[{clean}",
            max=f"[{clean}\xff",
            start=0,
            num=limit,
        )
        return [m.split("::", 1)[1] for m in raw_matches if "::" in m]
    except Exception:
        return []
