import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.pool import vector_to_pg_literal  # noqa: E402
from app.services.cache_service import make_cache_key  # noqa: E402
from eval.evaluate_ndcg import mrr, ndcg_at_k  # noqa: E402


def test_vector_literal_formatting():
    assert vector_to_pg_literal([0.1, -0.25, 0.5]) == "[0.100000,-0.250000,0.500000]"


def test_cache_key_is_deterministic_across_key_order():
    k1 = make_cache_key("search:res", {"q": "atta", "mode": "hybrid", "limit": 12})
    k2 = make_cache_key("search:res", {"limit": 12, "q": "atta", "mode": "hybrid"})
    assert k1 == k2
    assert k1.startswith("search:res:")


def test_ndcg_and_mrr_calculations():
    relevant = {"SKU-1": 3, "SKU-2": 2}
    assert round(ndcg_at_k(["SKU-1", "SKU-2", "SKU-9"], relevant, k=5), 4) == 1.0
    assert mrr(["SKU-1", "SKU-2"], relevant) == 1.0
    assert round(mrr(["SKU-9", "SKU-8", "SKU-2"], relevant), 4) == round(1 / 3, 4)
