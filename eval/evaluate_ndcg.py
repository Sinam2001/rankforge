import json
import math
import httpx

API_URL = "http://localhost:8000/v1/search"


def dcg_at_k(relevances: list[int], k: int) -> float:
    return sum((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(relevances[:k]))


def ndcg_at_k(ranked_skus: list[str], relevant_map: dict[str, int], k: int = 5) -> float:
    actual = [relevant_map.get(sku, 0) for sku in ranked_skus[:k]]
    ideal = sorted(relevant_map.values(), reverse=True)[:k]
    idcg = dcg_at_k(ideal, k)
    return dcg_at_k(actual, k) / idcg if idcg > 0 else 0.0


def mrr(ranked_skus: list[str], relevant_map: dict[str, int]) -> float:
    for idx, sku in enumerate(ranked_skus, start=1):
        if relevant_map.get(sku, 0) > 0:
            return 1.0 / idx
    return 0.0


def evaluate():
    with open("eval/golden_queries.json") as f:
        golden = json.load(f)

    for mode in ("lexical", "vector", "hybrid"):
        ndcg_scores, mrr_scores = [], []
        for case in golden:
            resp = httpx.get(API_URL, params={"q": case["query"], "mode": mode, "limit": 10}, timeout=10.0)
            resp.raise_for_status()
            skus = [item["sku"] for item in resp.json()["results"]]
            ndcg_scores.append(ndcg_at_k(skus, case["relevant_skus"], k=5))
            mrr_scores.append(mrr(skus, case["relevant_skus"]))

        avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
        avg_mrr = sum(mrr_scores) / len(mrr_scores)
        print(f"Mode={mode:8s} | NDCG@5={avg_ndcg:.4f} | MRR={avg_mrr:.4f}")


if __name__ == "__main__":
    evaluate()
