import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.services.elasticsearch import get_es_client, close_es_client, ensure_index
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX, MAPPING as COMPANY_MAPPING
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX, MAPPING as MARKET_MAPPING
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX, MAPPING as HISTORY_MAPPING
from app.routers import ingest as ingest_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)

_INDICES = [
    (COMPANY_INDEX, COMPANY_MAPPING),
    (MARKET_INDEX, MARKET_MAPPING),
    (HISTORY_INDEX, HISTORY_MAPPING),
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
    title="ElasticCX Ingestion API",
    description=(
        "Data ingestion backend for ElasticCX. "
        "Chunks, embeds, and indexes documents, emails, transcripts, and reviews "
        "into Elasticsearch Cloud for hybrid BM25 + kNN search."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(ingest_router.router)


@app.get("/health", tags=["meta"])
async def health():
    client = get_es_client()
    cluster_info = await client.info()
    return {
        "status": "ok",
        "cluster": cluster_info["cluster_name"],
        "es_version": cluster_info["version"]["number"],
    }
