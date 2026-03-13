import time
import logging
from app.services.elasticsearch import get_es_client
from app.services.embedder import embed_single

logger = logging.getLogger(__name__)


def _build_filter_clauses(filters: dict) -> list[dict]:
    clauses = []
    if "sentiment" in filters:
        clauses.append({"term": {"sentiment": filters["sentiment"]}})
    if "source_site" in filters:
        clauses.append({"term": {"source_site": filters["source_site"]}})
    if "company_name" in filters:
        clauses.append({"term": {"company_name": filters["company_name"]}})
    if "customer_id" in filters:
        clauses.append({"term": {"customer_id": filters["customer_id"]}})
    if "source_type" in filters:
        clauses.append({"term": {"source_type": filters["source_type"]}})
    if "doc_type" in filters:
        clauses.append({"term": {"doc_type": filters["doc_type"]}})
    if "intent" in filters:
        clauses.append({"term": {"intent": filters["intent"]}})
    if "min_rating" in filters:
        clauses.append({"range": {"rating": {"gte": filters["min_rating"]}}})
    return clauses


def _make_recency_function_score(base_query: dict) -> dict:
    """
    Wrap a query in function_score with gaussian date decay.
    Documents < 7 days old keep full score; half-life at 37 days.
    ES silently ignores gauss functions for docs missing the date/timestamp field,
    so this is safe to apply across all indices.
    """
    return {
        "function_score": {
            "query": base_query,
            "functions": [
                {
                    "gauss": {
                        "date": {
                            "origin": "now",
                            "scale": "30d",
                            "offset": "7d",
                            "decay": 0.5,
                        }
                    },
                    "weight": 1.5,
                },
                {
                    "gauss": {
                        "timestamp": {
                            "origin": "now",
                            "scale": "30d",
                            "offset": "7d",
                            "decay": 0.5,
                        }
                    },
                    "weight": 1.5,
                },
            ],
            "score_mode": "max",
            "boost_mode": "multiply",
        }
    }


async def hybrid_search(
    index: str,
    query_text: str,
    filters: dict | None = None,
    top_k: int = 10,
    boost_recency: bool = False,
) -> dict:
    """
    Hybrid search via Elasticsearch RRF retriever API (ES 8.9+).
    Fuses BM25 (multi_match across all text fields) + kNN (dense vector)
    using Reciprocal Rank Fusion. Filters are applied inside both retrievers
    so ranking is performed only on matched documents.

    boost_recency=True applies gaussian date decay — recent docs score higher.

    Returns: {hits: [...], total: int, took_ms: int}
    Each hit: {id, score, index, highlights, ...source_fields (no vector)}
    """
    start = time.monotonic()
    query_vector = await embed_single(query_text)
    client = get_es_client()

    filter_clauses = _build_filter_clauses(filters or {})

    # BM25 retriever — boosted field weights for best_fields fusion
    base_bm25: dict = {
        "multi_match": {
            "query": query_text,
            "fields": [
                "title^3",
                "text^2",
                "review_text^2",
                "subject^2",
                "pros",
                "cons",
                "raw_text",
            ],
            "type": "best_fields",
        }
    }

    if filter_clauses:
        bm25_query: dict = {
            "bool": {
                "must": [base_bm25],
                "filter": filter_clauses,
            }
        }
    else:
        bm25_query = base_bm25

    if boost_recency:
        bm25_query = _make_recency_function_score(bm25_query)

    # kNN retriever — optionally filtered
    knn_block: dict = {
        "field": "text_embedding",
        "query_vector": query_vector,
        "num_candidates": max(top_k * 10, 100),
        "k": top_k * 2,
    }
    if filter_clauses:
        knn_block["filter"] = {"bool": {"filter": filter_clauses}}

    body = {
        "retriever": {
            "rrf": {
                "retrievers": [
                    {"standard": {"query": bm25_query}},
                    {"knn": knn_block},
                ],
                "rank_window_size": max(top_k * 5, 100),
                "rank_constant": 20,
            }
        },
        "_source": {"excludes": ["text_embedding"]},
        "highlight": {
            "pre_tags": ["<mark>"],
            "post_tags": ["</mark>"],
            "fields": {
                "text": {"number_of_fragments": 2, "fragment_size": 200},
                "review_text": {"number_of_fragments": 2, "fragment_size": 200},
                "raw_text": {"number_of_fragments": 2, "fragment_size": 200},
                "title": {"number_of_fragments": 1, "fragment_size": 150},
            },
        },
        "size": top_k,
    }

    response = await client.search(index=index, body=body)
    took_ms = int((time.monotonic() - start) * 1000)

    hits = []
    for hit in response["hits"]["hits"]:
        hit_data: dict = {
            "id": hit["_id"],
            "score": round(hit["_score"], 4),
            "index": hit["_index"],
            **hit["_source"],
        }
        if "highlight" in hit:
            hit_data["highlights"] = hit["highlight"]
        hits.append(hit_data)

    return {
        "hits": hits,
        "total": response["hits"]["total"]["value"],
        "took_ms": took_ms,
    }
