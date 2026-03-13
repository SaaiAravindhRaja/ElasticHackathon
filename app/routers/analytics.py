from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
from app.services.elasticsearch import get_es_client
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def overview():
    """
    High-level dashboard stats: document counts per index + overall sentiment distribution.
    """
    client = get_es_client()

    # Parallel doc counts
    counts: dict[str, int] = {}
    for label, index in [
        ("knowledge", COMPANY_INDEX),
        ("reviews", MARKET_INDEX),
        ("customers", HISTORY_INDEX),
    ]:
        resp = await client.count(index=index)
        counts[label] = resp["count"]

    # Sentiment distribution across all reviews
    sentiment_resp = await client.search(
        index=MARKET_INDEX,
        body={
            "size": 0,
            "aggs": {"sentiments": {"terms": {"field": "sentiment", "size": 10}}},
        },
    )
    sentiment_dist = {
        b["key"]: b["doc_count"]
        for b in sentiment_resp["aggregations"]["sentiments"]["buckets"]
    }

    # Intent distribution from customer history
    intent_resp = await client.search(
        index=HISTORY_INDEX,
        body={
            "size": 0,
            "aggs": {"intents": {"terms": {"field": "intent", "size": 10}}},
        },
    )
    intent_dist = {
        b["key"]: b["doc_count"]
        for b in intent_resp["aggregations"]["intents"]["buckets"]
    }

    return {
        "total_docs": counts,
        "review_sentiment_distribution": sentiment_dist,
        "customer_intent_distribution": intent_dist,
    }


@router.get("/sentiment-trend")
async def sentiment_trend(
    index: str = Query("reviews", description="'reviews' or 'customers'"),
    days: int = Query(30, ge=1, le=365),
):
    """
    Sentiment over time — daily bucketed breakdown.
    Useful for tracking whether customer satisfaction is improving or degrading.
    """
    client = get_es_client()
    target_index = MARKET_INDEX if index == "reviews" else HISTORY_INDEX
    time_field = "date" if index == "reviews" else "timestamp"

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    response = await client.search(
        index=target_index,
        body={
            "size": 0,
            "query": {"range": {time_field: {"gte": since}}},
            "aggs": {
                "by_date": {
                    "date_histogram": {
                        "field": time_field,
                        "calendar_interval": "day",
                        "min_doc_count": 1,
                    },
                    "aggs": {
                        "by_sentiment": {"terms": {"field": "sentiment", "size": 5}}
                    },
                }
            },
        },
    )

    buckets = []
    for bucket in response["aggregations"]["by_date"]["buckets"]:
        counts = {b["key"]: b["doc_count"] for b in bucket["by_sentiment"]["buckets"]}
        buckets.append(
            {
                "date": bucket["key_as_string"],
                "positive": counts.get("positive", 0),
                "neutral": counts.get("neutral", 0),
                "negative": counts.get("negative", 0),
                "total": bucket["doc_count"],
            }
        )

    return {"index": index, "days": days, "buckets": buckets}


@router.get("/top-topics")
async def top_topics(
    index: str = Query("customers", description="'customers' or 'reviews'"),
    top_n: int = Query(20, ge=1, le=100),
):
    """
    Most frequently appearing topics in customer messages or reviews.
    For customers: uses LLM-extracted topic tags.
    For reviews: uses significant_text aggregation on review body.
    """
    client = get_es_client()

    if index == "customers":
        response = await client.search(
            index=HISTORY_INDEX,
            body={
                "size": 0,
                "aggs": {"topics": {"terms": {"field": "topics", "size": top_n}}},
            },
        )
        topics = [
            {"term": b["key"], "count": b["doc_count"]}
            for b in response["aggregations"]["topics"]["buckets"]
        ]
    else:
        # significant_text finds statistically unusual terms in this corpus
        response = await client.search(
            index=MARKET_INDEX,
            body={
                "size": 0,
                "aggs": {
                    "keywords": {
                        "significant_text": {
                            "field": "review_text",
                            "size": top_n,
                        }
                    }
                },
            },
        )
        topics = [
            {"term": b["key"], "count": b["doc_count"], "significance_score": round(b["score"], 4)}
            for b in response["aggregations"]["keywords"]["buckets"]
        ]

    return {"index": index, "topics": topics}


@router.get("/competitor-compare")
async def competitor_compare(
    companies: str = Query(..., description="Comma-separated company names, e.g. 'Zendesk,Freshdesk'"),
):
    """
    Compare multiple companies by avg rating, sentiment distribution, and review volume per source.
    Powers the competitive intelligence dashboard.
    """
    client = get_es_client()
    company_list = [c.strip() for c in companies.split(",") if c.strip()]

    response = await client.search(
        index=MARKET_INDEX,
        body={
            "size": 0,
            "query": {"terms": {"company_name": company_list}},
            "aggs": {
                "by_company": {
                    "terms": {"field": "company_name", "size": 20},
                    "aggs": {
                        "avg_rating": {"avg": {"field": "rating"}},
                        "by_sentiment": {"terms": {"field": "sentiment", "size": 5}},
                        "by_source": {"terms": {"field": "source_site", "size": 5}},
                    },
                }
            },
        },
    )

    result = []
    for bucket in response["aggregations"]["by_company"]["buckets"]:
        sentiment = {b["key"]: b["doc_count"] for b in bucket["by_sentiment"]["buckets"]}
        sources = {b["key"]: b["doc_count"] for b in bucket["by_source"]["buckets"]}
        result.append(
            {
                "company": bucket["key"],
                "total_reviews": bucket["doc_count"],
                "avg_rating": round(bucket["avg_rating"]["value"] or 0.0, 2),
                "sentiment_distribution": sentiment,
                "reviews_by_source": sources,
            }
        )

    return {"companies": result}


@router.get("/avg-rating-trend")
async def avg_rating_trend(
    company: str = Query(..., description="Company name"),
    days: int = Query(90, ge=7, le=365),
):
    """
    Average star rating over time for a specific company.
    Useful for detecting review trends after product events or outages.
    """
    client = get_es_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    response = await client.search(
        index=MARKET_INDEX,
        body={
            "size": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"company_name": company}},
                        {"range": {"date": {"gte": since}}},
                    ]
                }
            },
            "aggs": {
                "by_week": {
                    "date_histogram": {
                        "field": "date",
                        "calendar_interval": "week",
                        "min_doc_count": 1,
                    },
                    "aggs": {"avg_rating": {"avg": {"field": "rating"}}},
                }
            },
        },
    )

    buckets = [
        {
            "week": b["key_as_string"],
            "avg_rating": round(b["avg_rating"]["value"] or 0.0, 2),
            "count": b["doc_count"],
        }
        for b in response["aggregations"]["by_week"]["buckets"]
    ]

    return {"company": company, "days": days, "buckets": buckets}
