import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_bulk_ingest_requires_valid_api_key():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp_missing = await client.post("/v1/products/bulk", json=[])
        assert resp_missing.status_code == 401

        resp_invalid = await client.post(
            "/v1/products/bulk", headers={"X-API-Key": "wrong_key"}, json=[]
        )
        assert resp_invalid.status_code == 403


@pytest.mark.asyncio
async def test_hybrid_search_cache_hit_and_explain():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        params = {"q": "quiet keyboard for office", "mode": "hybrid", "explain": "true"}
        r1 = await client.get("/v1/search", params=params)
        assert r1.status_code == 200
        body = r1.json()
        assert body["total_candidates"] >= 1
        assert "explain" in body["results"][0]
        assert "X-RateLimit-Remaining" in r1.headers

        r2 = await client.get("/v1/search", params=params)
        assert r2.status_code == 200
        assert r2.headers.get("X-Cache") == "HIT"


@pytest.mark.asyncio
async def test_autocomplete_returns_suggestions():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        resp = await client.get("/v1/autocomplete", params={"q": "key"})
        assert resp.status_code == 200
        assert isinstance(resp.json()["suggestions"], list)
