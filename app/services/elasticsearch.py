import logging
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from app.config import get_settings

logger = logging.getLogger(__name__)

_es_client: AsyncElasticsearch | None = None


def get_es_client() -> AsyncElasticsearch:
    global _es_client
    if _es_client is None:
        settings = get_settings()
        _es_client = AsyncElasticsearch(
            cloud_id=settings.es_cloud_id,
            api_key=settings.es_api_key,
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True,
        )
    return _es_client


async def close_es_client() -> None:
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None


async def ensure_index(index_name: str, mapping: dict) -> None:
    client = get_es_client()
    exists = await client.indices.exists(index=index_name)
    if not exists:
        await client.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index: {index_name}")
    else:
        logger.info(f"Index already exists: {index_name}")


async def bulk_index_with_dedup(
    index_name: str, documents: list[dict]
) -> tuple[int, int, int]:
    """
    Bulk index using op_type='create'. Documents must have '_id' set.
    Duplicate documents (409 conflict) are counted as deduplicated, not failed.
    Returns (indexed, deduplicated, failed).
    """
    if not documents:
        return 0, 0, 0

    settings = get_settings()
    client = get_es_client()

    actions = [
        {
            "_op_type": "create",
            "_index": index_name,
            "_id": doc.get("_id"),
            **{k: v for k, v in doc.items() if k != "_id"},
        }
        for doc in documents
    ]

    total_indexed = 0
    total_deduped = 0
    total_failed = 0
    batch_size = settings.bulk_batch_size

    for i in range(0, len(actions), batch_size):
        batch = actions[i : i + batch_size]
        ok, errors = await async_bulk(
            client,
            batch,
            raise_on_error=False,
            raise_on_exception=False,
        )
        total_indexed += ok
        for error in errors:
            op_result = error.get("create", {})
            if op_result.get("status") == 409:
                total_deduped += 1
            else:
                total_failed += 1
                logger.warning(f"Bulk index error in {index_name}: {op_result}")

    return total_indexed, total_deduped, total_failed


async def bulk_index(index_name: str, documents: list[dict]) -> tuple[int, int]:
    """
    Bulk index documents. Returns (success_count, failed_count).
    Each dict in documents should be a plain ES document body (no _index/_source wrapping).
    """
    if not documents:
        return 0, 0

    settings = get_settings()
    client = get_es_client()

    actions = [
        {
            "_index": index_name,
            "_id": doc.get("_id"),
            **{k: v for k, v in doc.items() if k != "_id"},
        }
        for doc in documents
    ]

    total_success = 0
    total_failed = 0
    batch_size = settings.bulk_batch_size

    for i in range(0, len(actions), batch_size):
        batch = actions[i : i + batch_size]
        ok, errors = await async_bulk(
            client,
            batch,
            raise_on_error=False,
            raise_on_exception=False,
        )
        total_success += ok
        total_failed += len(errors)
        if errors:
            logger.warning(f"Bulk index errors in {index_name}: {errors[:3]}")

    return total_success, total_failed
