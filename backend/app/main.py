from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.logging_mw import structured_logging_middleware
from app.db.pool import close_db_pool, init_db_pool
from app.db.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    await init_redis()
    yield
    await close_redis()
    await close_db_pool()


app = FastAPI(title="RankForge Hybrid Search Engine", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(structured_logging_middleware)
app.include_router(router)
