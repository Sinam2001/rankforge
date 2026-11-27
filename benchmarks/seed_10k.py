import asyncio
import random
import asyncpg
import numpy as np
from app.core.config import settings
from app.db.pool import vector_to_pg_literal

BRANDS = ["Samsung", "Apple", "Sony", "OnePlus", "Keychron", "Logitech", "Aashirvaad", "Fortune", "Puma", "Preethi"]
CATEGORIES = ["Smartphones", "Audio", "Computer Accessories", "Groceries", "Footwear", "Home Appliances"]
ADJECTIVES = ["Pro", "Ultra", "Silent", "Wireless", "Fresh", "Cushioned", "Heavy Duty", "Compact", "Smart", "Lite"]
NOUNS = ["Smartphone", "Headphones", "Keyboard", "Whole Wheat Flour", "Running Shoes", "Mixer Grinder", "Earbuds", "Watch"]


async def main(total: int = 10_000):
    conn = await asyncpg.connect(settings.database_url)
    rng = np.random.default_rng(42)
    rows = []
    for i in range(total):
        brand = random.choice(BRANDS)
        cat = random.choice(CATEGORIES)
        title = f"{brand} {random.choice(ADJECTIVES)} {random.choice(NOUNS)} Model-{i}"
        desc = f"High quality {cat.lower()} product from {brand} engineered for daily Indian usage."
        vec = rng.standard_normal(384)
        vec = vec / np.linalg.norm(vec)
        rows.append((
            f"BENCH-{i:05d}", title, desc, brand, cat,
            random.randint(199, 89999), round(random.uniform(3.5, 5.0), 1),
            random.randint(0, 200), vector_to_pg_literal(vec.tolist())
        ))

    await conn.executemany(
        """
        INSERT INTO products (sku, title, description, brand, category, price_inr, rating, stock_qty, embedding)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector)
        ON CONFLICT (sku) DO NOTHING
        """,
        rows,
    )
    await conn.execute("ANALYZE products;")
    await conn.close()
    print(f"Seeded and analyzed {total} benchmark products.")


if __name__ == "__main__":
    asyncio.run(main())
