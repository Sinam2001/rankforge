import math
from typing import Literal
import asyncpg
from app.db.pool import vector_to_pg_literal
from app.services.embedder import embed_query

RRF_K = 60
SearchMode = Literal["hybrid", "lexical", "vector"]


async def expand_query_with_synonyms(pool: asyncpg.Pool, query: str) -> str:
    tokens = [t.strip().lower() for t in query.split() if t.strip()]
    if not tokens:
        return query
    rows = await pool.fetch(
        "SELECT term, expansions FROM synonyms WHERE term = ANY($1::text[])", tokens
    )
    if not rows:
        return query
    expanded_parts = list(tokens)
    for row in rows:
        expanded_parts.extend(row["expansions"])
    return " ".join(dict.fromkeys(expanded_parts))


async def hybrid_search(
    pool: asyncpg.Pool,
    query: str,
    mode: SearchMode = "hybrid",
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    in_stock: bool = False,
    limit: int = 12,
    offset: int = 0,
    explain: bool = False,
) -> dict:
    expanded_query = await expand_query_with_synonyms(pool, query)
    query_vec = await embed_query(expanded_query) if mode in ("hybrid", "vector") else None
    pg_vec = vector_to_pg_literal(query_vec) if query_vec else None

    filters = ["1=1"]
    params: list = [expanded_query, query]
    idx = 3

    if category:
        filters.append(f"category = ${idx}")
        params.append(category)
        idx += 1
    if brand:
        filters.append(f"brand = ${idx}")
        params.append(brand)
        idx += 1
    if min_price is not None:
        filters.append(f"price_inr >= ${idx}")
        params.append(min_price)
        idx += 1
    if max_price is not None:
        filters.append(f"price_inr <= ${idx}")
        params.append(max_price)
        idx += 1
    if in_stock:
        filters.append("stock_qty > 0")

    where_sql = " AND ".join(filters)
    lexical_rows = []
    vector_rows = []

    if mode in ("hybrid", "lexical"):
        lex_sql = f"""
            SELECT id, sku, title, description, brand, category, price_inr, rating, stock_qty, click_count,
                   ts_rank_cd(search_vector, websearch_to_tsquery('english', $1)) AS fts_score,
                   similarity(title, $2) AS trgm_score
            FROM products
            WHERE {where_sql}
              AND (
                  search_vector @@ websearch_to_tsquery('english', $1)
                  OR similarity(title, $2) > 0.22
              )
            ORDER BY (ts_rank_cd(search_vector, websearch_to_tsquery('english', $1)) * 2.0 + similarity(title, $2)) DESC
            LIMIT 50
        """
        lexical_rows = await pool.fetch(lex_sql, *params)

    if mode in ("hybrid", "vector") and pg_vec is not None:
        vec_params = params + [pg_vec]
        vec_param_idx = idx
        vec_sql = f"""
            SELECT id, sku, title, description, brand, category, price_inr, rating, stock_qty, click_count,
                   1 - (embedding <=> ${vec_param_idx}::vector) AS cosine_sim
            FROM products
            WHERE {where_sql} AND embedding IS NOT NULL
            ORDER BY embedding <=> ${vec_param_idx}::vector ASC
            LIMIT 50
        """
        vector_rows = await pool.fetch(vec_sql, *vec_params)

    candidates: dict[str, dict] = {}

    for rank, row in enumerate(lexical_rows, start=1):
        pid = str(row["id"])
        candidates[pid] = {
            "row": dict(row),
            "lex_rank": rank,
            "vec_rank": None,
            "fts_score": float(row["fts_score"]),
            "trgm_score": float(row["trgm_score"]),
            "cosine_sim": None,
        }

    for rank, row in enumerate(vector_rows, start=1):
        pid = str(row["id"])
        if pid not in candidates:
            candidates[pid] = {
                "row": dict(row),
                "lex_rank": None,
                "vec_rank": rank,
                "fts_score": 0.0,
                "trgm_score": 0.0,
                "cosine_sim": float(row["cosine_sim"]),
            }
        else:
            candidates[pid]["vec_rank"] = rank
            candidates[pid]["cosine_sim"] = float(row["cosine_sim"])

    w_lex = 1.0 if mode in ("hybrid", "lexical") else 0.0
    w_vec = 1.0 if mode in ("hybrid", "vector") else 0.0
    w_pop = 0.002

    scored = []
    for pid, data in candidates.items():
        row = data["row"]
        lex_contrib = (w_lex / (RRF_K + data["lex_rank"])) if data["lex_rank"] else 0.0
        vec_contrib = (w_vec / (RRF_K + data["vec_rank"])) if data["vec_rank"] else 0.0
        pop_boost = w_pop * math.log1p(row["click_count"]) if row["stock_qty"] > 0 else -0.005
        final_score = lex_contrib + vec_contrib + pop_boost

        item = {
            "id": pid,
            "sku": row["sku"],
            "title": row["title"],
            "description": row["description"],
            "brand": row["brand"],
            "category": row["category"],
            "price_inr": row["price_inr"],
            "rating": float(row["rating"]),
            "stock_qty": row["stock_qty"],
            "score": round(final_score, 6),
        }
        if explain:
            item["explain"] = {
                "lexical_rank": data["lex_rank"],
                "semantic_rank": data["vec_rank"],
                "fts_score": round(data["fts_score"], 4),
                "trigram_similarity": round(data["trgm_score"], 4),
                "cosine_similarity": round(data["cosine_sim"], 4) if data["cosine_sim"] is not None else None,
                "rrf_lexical": round(lex_contrib, 6),
                "rrf_semantic": round(vec_contrib, 6),
                "popularity_boost": round(pop_boost, 6),
            }
        scored.append(item)

    scored.sort(key=lambda x: x["score"], reverse=True)
    paginated = scored[offset : offset + limit]

    cat_counts: dict[str, int] = {}
    brand_counts: dict[str, int] = {}
    for item in scored:
        cat_counts[item["category"]] = cat_counts.get(item["category"], 0) + 1
        brand_counts[item["brand"]] = brand_counts.get(item["brand"], 0) + 1

    return {
        "query": query,
        "expanded_query": expanded_query,
        "mode": mode,
        "total_candidates": len(scored),
        "results": paginated,
        "facets": {"categories": cat_counts, "brands": brand_counts},
    }
