import hashlib
import json
from typing import Literal
from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.db.pool import get_db_pool
from app.services.autocomplete import suggest_prefixes
from app.services.cache_service import get_cached_json, make_cache_key, set_cached_json
from app.services.search_service import hybrid_search

router = APIRouter(prefix="/v1")


class ProductIn(BaseModel):
    sku: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=2000)
    brand: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=2, max_length=100)
    price_inr: int = Field(..., ge=0)
    rating: float = Field(default=4.0, ge=0.0, le=5.0)
    stock_qty: int = Field(default=10, ge=0)


class ClickEventIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    product_id: str
    rank_position: int = Field(..., ge=1)


async def require_admin_key(x_api_key: str = Header(default="")) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    pool = get_db_pool()
    row = await pool.fetchrow(
        "SELECT role FROM api_keys WHERE key_hash = $1 AND is_active = TRUE", key_hash
    )
    if not row or row["role"] != "admin":
        raise HTTPException(status_code=403, detail="Invalid or unauthorized API key")


@router.get("/health")
async def health_check():
    pool = get_db_pool()
    await pool.fetchval("SELECT 1")
    return {"status": "ok", "database": "connected"}


@router.get("/autocomplete", dependencies=[Depends(rate_limit_dependency)])
async def autocomplete(q: str = Query(..., min_length=1, max_length=100)):
    suggestions = await suggest_prefixes(q, limit=6)
    return {"prefix": q, "suggestions": suggestions}


@router.get("/search", dependencies=[Depends(rate_limit_dependency)])
async def search_products(
    response: Response,
    q: str = Query(..., min_length=1, max_length=200),
    mode: Literal["hybrid", "lexical", "vector"] = "hybrid",
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    in_stock: bool = False,
    limit: int = Query(default=12, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    explain: bool = False,
):
    cache_payload = {
        "q": " ".join(q.lower().split()),
        "mode": mode,
        "category": category,
        "brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "in_stock": in_stock,
        "limit": limit,
        "offset": offset,
        "explain": explain,
    }
    cache_key = make_cache_key("search:res", cache_payload)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    pool = get_db_pool()
    result = await hybrid_search(
        pool=pool,
        query=q,
        mode=mode,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        limit=limit,
        offset=offset,
        explain=explain,
    )
    await set_cached_json(cache_key, result, ttl_seconds=60)
    response.headers["X-Cache"] = "MISS"
    return result


@router.post("/events/click", status_code=202)
async def track_click(payload: ClickEventIn):
    pool = get_db_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO search_events (query, product_id, event_type, rank_position)
                VALUES ($1, $2::uuid, 'click', $3)
                """,
                payload.query,
                payload.product_id,
                payload.rank_position,
            )
            await conn.execute(
                "UPDATE products SET click_count = click_count + 1 WHERE id = $1::uuid",
                payload.product_id,
            )
    return {"status": "recorded"}


@router.post("/products/bulk", status_code=202, dependencies=[Depends(require_admin_key)])
async def bulk_ingest_products(products: list[ProductIn]):
    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)
    await producer.start()
    try:
        for product in products:
            await producer.send_and_wait(
                settings.kafka_catalog_topic,
                key=product.sku.encode("utf-8"),
                value=json.dumps(product.model_dump()).encode("utf-8"),
            )
    finally:
        await producer.stop()
    return {"status": "queued", "count": len(products)}
