export type SearchMode = "hybrid" | "lexical" | "vector";

export interface ExplainBreakdown {
  lexical_rank: number | null;
  semantic_rank: number | null;
  fts_score: number;
  trigram_similarity: number;
  cosine_similarity: number | null;
  rrf_lexical: number;
  rrf_semantic: number;
  popularity_boost: number;
}

export interface ProductResult {
  id: string;
  sku: string;
  title: string;
  description: string;
  brand: string;
  category: string;
  price_inr: number;
  rating: number;
  stock_qty: number;
  score: number;
  explain?: ExplainBreakdown;
}

export interface SearchResponse {
  query: string;
  expanded_query: string;
  mode: SearchMode;
  total_candidates: number;
  results: ProductResult[];
  facets: {
    categories: Record<string, number>;
    brands: Record<string, number>;
  };
  client_latency_ms?: number;
  cache_status?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function searchProducts(params: {
  q: string;
  mode: SearchMode;
  category?: string;
  brand?: string;
  max_price?: number;
  in_stock?: boolean;
  explain?: boolean;
}): Promise<SearchResponse> {
  const qs = new URLSearchParams({
    q: params.q,
    mode: params.mode,
    explain: String(params.explain ?? true),
  });
  if (params.category) qs.set("category", params.category);
  if (params.brand) qs.set("brand", params.brand);
  if (params.max_price) qs.set("max_price", String(params.max_price));
  if (params.in_stock) qs.set("in_stock", "true");

  const t0 = performance.now();
  const res = await fetch(`${API_BASE}/v1/search?${qs.toString()}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  const data: SearchResponse = await res.json();
  data.client_latency_ms = Math.round(performance.now() - t0);
  data.cache_status = res.headers.get("X-Cache") || undefined;
  return data;
}

export async function fetchAutocomplete(prefix: string): Promise<string[]> {
  if (!prefix.trim()) return [];
  const res = await fetch(`${API_BASE}/v1/autocomplete?q=${encodeURIComponent(prefix)}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.suggestions ?? [];
}

export async function trackProductClick(
  query: string,
  productId: string,
  rankPosition: number
): Promise<void> {
  await fetch(`${API_BASE}/v1/events/click`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, product_id: productId, rank_position: rankPosition }),
  });
}
