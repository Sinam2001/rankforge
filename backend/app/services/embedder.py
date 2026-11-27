import asyncio
from functools import lru_cache
from fastembed import TextEmbedding
from app.core.config import settings
from app.services.cache_service import get_cached_json, make_cache_key, set_cached_json


@lru_cache(maxsize=1)
def _load_model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model)


def _embed_sync(texts: list[str]) -> list[list[float]]:
    model = _load_model()
    return [vec.tolist() for vec in model.embed(texts)]


async def embed_query(text: str) -> list[float]:
    normalized = " ".join(text.lower().split())
    cache_key = make_cache_key("search:emb", normalized)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return cached
    vectors = await asyncio.to_thread(_embed_sync, [normalized])
    await set_cached_json(cache_key, vectors[0], ttl_seconds=3600)
    return vectors[0]


async def embed_documents(texts: list[str]) -> list[list[float]]:
    return await asyncio.to_thread(_embed_sync, texts)
