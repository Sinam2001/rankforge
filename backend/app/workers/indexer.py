import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from app.core.config import settings
from app.db.pool import init_db_pool, vector_to_pg_literal
from app.db.redis_client import init_redis
from app.services.autocomplete import index_autocomplete_term
from app.services.embedder import embed_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rankforge.indexer")


async def upsert_product(pool, item: dict, embedding: list[float]) -> None:
    pg_vec = vector_to_pg_literal(embedding)
    await pool.execute(
        """
        INSERT INTO products (sku, title, description, brand, category, price_inr, rating, stock_qty, embedding, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::vector, NOW())
        ON CONFLICT (sku) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            brand = EXCLUDED.brand,
            category = EXCLUDED.category,
            price_inr = EXCLUDED.price_inr,
            rating = EXCLUDED.rating,
            stock_qty = EXCLUDED.stock_qty,
            embedding = EXCLUDED.embedding,
            updated_at = NOW()
        """,
        item["sku"],
        item["title"],
        item["description"],
        item["brand"],
        item["category"],
        item["price_inr"],
        item["rating"],
        item["stock_qty"],
        pg_vec,
    )


async def run_worker() -> None:
    pool = await init_db_pool()
    await init_redis()
    consumer = AIOKafkaConsumer(
        settings.kafka_catalog_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="rankforge-indexer-v1",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    dlq_producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_bootstrap_servers)

    await consumer.start()
    await dlq_producer.start()
    logger.info("Indexer worker listening on topic=%s", settings.kafka_catalog_topic)

    try:
        async for msg in consumer:
            for attempt in range(1, 4):
                try:
                    item = json.loads(msg.value.decode("utf-8"))
                    text_to_embed = f"{item['title']} | {item['brand']} | {item['category']} | {item['description']}"
                    embedding = (await embed_documents([text_to_embed]))[0]
                    await upsert_product(pool, item, embedding)
                    await index_autocomplete_term(item["title"])
                    await consumer.commit()
                    logger.info("Indexed SKU=%s", item["sku"])
                    break
                except Exception as exc:
                    logger.warning("Attempt %d failed for offset=%d: %s", attempt, msg.offset, exc)
                    if attempt == 3:
                        dlq_payload = json.dumps({
                            "error": str(exc),
                            "raw_value": msg.value.decode("utf-8", errors="replace"),
                        }).encode("utf-8")
                        await dlq_producer.send_and_wait(settings.kafka_dlq_topic, value=dlq_payload)
                        await consumer.commit()
                        logger.error("Routed offset=%d to DLQ", msg.offset)
                    else:
                        await asyncio.sleep(0.5 * attempt)
    finally:
        await consumer.stop()
        await dlq_producer.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
