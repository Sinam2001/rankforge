CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    brand TEXT NOT NULL,
    category TEXT NOT NULL,
    price_inr INTEGER NOT NULL CHECK (price_inr >= 0),
    rating NUMERIC(2,1) NOT NULL DEFAULT 4.0 CHECK (rating >= 0 AND rating <= 5),
    stock_qty INTEGER NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    click_count INTEGER NOT NULL DEFAULT 0,
    search_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(brand, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(category, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(description, '')), 'C')
    ) STORED,
    embedding VECTOR(384),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_search_vector
    ON products USING GIN (search_vector);

CREATE INDEX IF NOT EXISTS idx_products_title_trgm
    ON products USING GIN (title gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_products_embedding_hnsw
    ON products USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_products_facets
    ON products (category, price_inr, stock_qty);

CREATE TABLE IF NOT EXISTS synonyms (
    term TEXT PRIMARY KEY,
    expansions TEXT[] NOT NULL
);

CREATE TABLE IF NOT EXISTS search_events (
    id BIGSERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('impression', 'click')),
    rank_position INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'client')),
    rate_limit_rpm INTEGER NOT NULL DEFAULT 120,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO synonyms (term, expansions) VALUES
    ('atta', ARRAY['whole wheat flour', 'chakki atta']),
    ('chappal', ARRAY['slippers', 'flip flops', 'sandals']),
    ('ifone', ARRAY['iphone', 'apple smartphone']),
    ('earbuds', ARRAY['tws', 'wireless earphones', 'anc earbuds']),
    ('mixie', ARRAY['mixer grinder', 'juicer'])
ON CONFLICT (term) DO NOTHING;

INSERT INTO api_keys (key_hash, role, rate_limit_rpm)
VALUES (encode(digest('rf_admin_dev_key', 'sha256'), 'hex'), 'admin', 600)
ON CONFLICT (key_hash) DO NOTHING;
