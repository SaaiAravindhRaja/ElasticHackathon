import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.elasticsearch import get_es_client, close_es_client, ensure_index
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX, MAPPING as COMPANY_MAPPING
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX, MAPPING as MARKET_MAPPING
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX, MAPPING as HISTORY_MAPPING
from app.indices.alerts import INDEX_NAME as ALERTS_INDEX, MAPPING as ALERTS_MAPPING
from app.routers import ingest as ingest_router
from app.routers import search as search_router
from app.routers import ai as ai_router
from app.routers import analytics as analytics_router
from app.routers import alerts as alerts_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

_INDICES = [
    (COMPANY_INDEX, COMPANY_MAPPING),
    (MARKET_INDEX, MARKET_MAPPING),
    (HISTORY_INDEX, HISTORY_MAPPING),
    (ALERTS_INDEX, ALERTS_MAPPING),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to Elasticsearch Cloud…")
    client = get_es_client()
    info = await client.info()
    logger.info(
        f"Connected — cluster: {info['cluster_name']}, "
        f"version: {info['version']['number']}"
    )

    for name, mapping in _INDICES:
        await ensure_index(name, mapping)

    yield

    await close_es_client()
    logger.info("Elasticsearch client closed")


app = FastAPI(
    title="ElasticCX API",
    description=(
        "AI-powered customer experience suite backend. "
        "Ingest documents, emails, transcripts, and reviews. "
        "Query with hybrid RRF search (BM25 + kNN). "
        "Generate AI answers grounded in your data via POST /ai/query. "
        "Multi-turn conversations supported via conversation_id. "
        "Register real-time percolator alerts via POST /alerts. "
        "Analyze trends and competitive intelligence via GET /analytics/*."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(ingest_router.router)
app.include_router(search_router.router)
app.include_router(ai_router.router)
app.include_router(analytics_router.router)
app.include_router(alerts_router.router)


@app.get("/health", tags=["meta"])
async def health():
    client = get_es_client()
    cluster_info = await client.info()
    return {
        "status": "ok",
        "cluster": cluster_info["cluster_name"],
        "es_version": cluster_info["version"]["number"],
    }
