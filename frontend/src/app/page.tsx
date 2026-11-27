"use client";

import { useEffect, useState } from "react";
import {
  fetchAutocomplete,
  searchProducts,
  trackProductClick,
  SearchMode,
  SearchResponse,
} from "@/lib/api";

const DEMO_QUERIES = [
  "quiet keyboard for office",
  "samung",
  "atta",
  "chappal",
  "noise cancelling",
];

export default function SearchWorkbench() {
  const [query, setQuery] = useState("quiet keyboard for office");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [category, setCategory] = useState<string>("");
  const [brand, setBrand] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");
  const [inStock, setInStock] = useState(false);
  const [showExplain, setShowExplain] = useState(true);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clickedId, setClickedId] = useState<string | null>(null);

  const runSearch = async (overrideQuery?: string) => {
    const q = (overrideQuery ?? query).trim();
    if (!q) return;
    setSuggestions([]);
    setLoading(true);
    setError(null);
    try {
      const res = await searchProducts({
        q,
        mode,
        category: category || undefined,
        brand: brand || undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
        in_stock: inStock,
        explain: showExplain,
      });
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch results");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSearch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, category, brand, inStock, showExplain]);

  const handleQueryChange = async (value: string) => {
    setQuery(value);
    if (value.trim().length >= 2) {
      try {
        setSuggestions(await fetchAutocomplete(value));
      } catch {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  };

  const handleProductClick = async (productId: string, rank: number) => {
    setClickedId(productId);
    try {
      await trackProductClick(query, productId, rank);
    } catch {
      // Non-blocking analytics failure
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight">RankForge</h1>
              <p className="text-sm text-slate-500">
                Hybrid E-Commerce Search Engine (BM25 + Trigram + pgvector HNSW + RRF)
              </p>
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-slate-100 p-1">
              {(["hybrid", "lexical", "vector"] as SearchMode[]).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium capitalize transition ${
                    mode === m
                      ? "bg-slate-900 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="relative mt-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                runSearch();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                placeholder="Try typos ('samung'), Hinglish ('atta'), or intent ('quiet keyboard for office')..."
                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm focus:border-slate-900 focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading}
                className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {loading ? "Searching..." : "Search"}
              </button>
            </form>

            {suggestions.length > 0 && (
              <ul className="absolute z-10 mt-1 w-full rounded-lg border bg-white shadow-md">
                {suggestions.map((s) => (
                  <li key={s}>
                    <button
                      type="button"
                      onClick={() => {
                        setQuery(s);
                        runSearch(s);
                      }}
                      className="w-full px-4 py-2 text-left text-sm hover:bg-slate-100"
                    >
                      {s}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-500">Try:</span>
            {DEMO_QUERIES.map((dq) => (
              <button
                key={dq}
                onClick={() => {
                  setQuery(dq);
                  runSearch(dq);
                }}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-700 hover:bg-slate-100"
              >
                {dq}
              </button>
            ))}
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-6 py-6 md:grid-cols-4">
        <aside className="space-y-5 rounded-xl border bg-white p-4 h-fit">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Filters</h2>
            <button
              onClick={() => {
                setCategory("");
                setBrand("");
                setMaxPrice("");
                setInStock(false);
              }}
              className="text-xs text-blue-600 hover:underline"
            >
              Reset
            </button>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={inStock}
              onChange={(e) => setInStock(e.target.checked)}
              className="rounded"
            />
            In Stock Only
          </label>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showExplain}
              onChange={(e) => setShowExplain(e.target.checked)}
              className="rounded"
            />
            Show Score Breakdown
          </label>

          <div>
            <label className="block text-xs font-medium text-slate-600">Max Price (INR)</label>
            <div className="mt-1 flex gap-2">
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="e.g. 15000"
                className="w-full rounded-md border px-2.5 py-1.5 text-sm"
              />
              <button
                onClick={() => runSearch()}
                className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium hover:bg-slate-200"
              >
                Go
              </button>
            </div>
          </div>

          {data && Object.keys(data.facets.categories).length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-slate-600">Categories</h3>
              <div className="mt-2 space-y-1">
                {Object.entries(data.facets.categories).map(([cat, count]) => (
                  <button
                    key={cat}
                    onClick={() => setCategory(category === cat ? "" : cat)}
                    className={`flex w-full justify-between rounded px-2 py-1 text-left text-xs ${
                      category === cat ? "bg-slate-900 text-white" : "hover:bg-slate-100"
                    }`}
                  >
                    <span>{cat}</span>
                    <span className="opacity-70">{count}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {data && Object.keys(data.facets.brands).length > 0 && (
            <div>
              <h3 className="text-xs font-medium text-slate-600">Brands</h3>
              <div className="mt-2 space-y-1">
                {Object.entries(data.facets.brands).map(([b, count]) => (
                  <button
                    key={b}
                    onClick={() => setBrand(brand === b ? "" : b)}
                    className={`flex w-full justify-between rounded px-2 py-1 text-left text-xs ${
                      brand === b ? "bg-slate-900 text-white" : "hover:bg-slate-100"
                    }`}
                  >
                    <span>{b}</span>
                    <span className="opacity-70">{count}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>

        <section className="md:col-span-3 space-y-4">
          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {data && (
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-white px-4 py-2.5 text-xs text-slate-600">
              <div>
                Found <strong>{data.total_candidates}</strong> candidates in{" "}
                <strong>{data.client_latency_ms} ms</strong> ({data.mode} mode
                {data.cache_status ? ` · Cache: ${data.cache_status}` : ""})
              </div>
              {data.expanded_query !== data.query && (
                <div className="rounded bg-blue-50 px-2 py-0.5 text-blue-700">
                  Synonym expansion: <span className="font-mono">{data.expanded_query}</span>
                </div>
              )}
            </div>
          )}

          <div className="space-y-3">
            {data?.results.map((item, idx) => (
              <article
                key={item.id}
                className="rounded-xl border bg-white p-4 transition hover:border-slate-300"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span className="font-mono">#{idx + 1}</span>
                      <span>{item.brand}</span>
                      <span>•</span>
                      <span>{item.category}</span>
                    </div>
                    <h3 className="mt-1 text-base font-semibold">{item.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold">
                      ₹{item.price_inr.toLocaleString("en-IN")}
                    </div>
                    <div className="text-xs text-slate-500">
                      ★ {item.rating} ·{" "}
                      {item.stock_qty > 0 ? `${item.stock_qty} in stock` : "Out of stock"}
                    </div>
                    <button
                      onClick={() => handleProductClick(item.id, idx + 1)}
                      className="mt-2 rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium hover:bg-slate-100"
                    >
                      {clickedId === item.id ? "Click Logged ✓" : "Simulate Click"}
                    </button>
                  </div>
                </div>

                {showExplain && item.explain && (
                  <div className="mt-3 rounded-lg bg-slate-50 p-3 font-mono text-xs text-slate-700">
                    <div className="flex flex-wrap gap-x-5 gap-y-1">
                      <span>Final RRF: <strong>{item.score}</strong></span>
                      <span>Lex Rank: <strong>{item.explain.lexical_rank ?? "—"}</strong></span>
                      <span>Vec Rank: <strong>{item.explain.semantic_rank ?? "—"}</strong></span>
                      <span>Cosine: <strong>{item.explain.cosine_similarity ?? "—"}</strong></span>
                      <span>Trigram: <strong>{item.explain.trigram_similarity}</strong></span>
                      <span>Pop Boost: <strong>{item.explain.popularity_boost}</strong></span>
                    </div>
                  </div>
                )}
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
