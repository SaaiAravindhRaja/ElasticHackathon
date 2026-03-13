import json
import time
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query
from app.services.elasticsearch import get_es_client
from app.services.search import hybrid_search
from app.services.embedder import get_openai_client
from app.config import get_settings
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX

logger = logging.getLogger(__name__)
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


@router.get("/emerging-topics")
async def emerging_topics(
    index: str = Query("reviews", description="'reviews' or 'customers'"),
    days: int = Query(7, ge=1, le=90, description="Recent window in days"),
    baseline_days: int = Query(30, ge=7, le=365, description="Baseline window in days"),
    top_n: int = Query(20, ge=1, le=100),
):
    """
    Topics that are suddenly trending upward relative to the baseline period.

    Uses ES significant_text aggregation on two time windows and computes
    the relative lift ratio: recent_frequency / baseline_frequency.
    A lift_ratio > 2.0 means the topic appears twice as often recently.

    This answers "what topics are NEWLY emerging?" not just "what's popular overall?"
    """
    client = get_es_client()
    now = datetime.now(timezone.utc)
    target_index = MARKET_INDEX if index == "reviews" else HISTORY_INDEX
    time_field = "date" if index == "reviews" else "timestamp"
    text_field = "review_text" if index == "reviews" else "raw_text"

    recent_since = (now - timedelta(days=days)).isoformat()
    baseline_since = (now - timedelta(days=days + baseline_days)).isoformat()
    baseline_until = recent_since

    # Run both windows in parallel
    recent_resp, baseline_resp = await asyncio.gather(
        client.search(
            index=target_index,
            body={
                "size": 0,
                "query": {"range": {time_field: {"gte": recent_since}}},
                "aggs": {
                    "keywords": {
                        "significant_text": {"field": text_field, "size": top_n * 2}
                    },
                    "total": {"value_count": {"field": time_field}},
                },
            },
        ),
        client.search(
            index=target_index,
            body={
                "size": 0,
                "query": {"range": {time_field: {"gte": baseline_since, "lt": baseline_until}}},
                "aggs": {
                    "keywords": {
                        "significant_text": {"field": text_field, "size": top_n * 2}
                    },
                    "total": {"value_count": {"field": time_field}},
                },
            },
        ),
    )

    recent_total = max(recent_resp["aggregations"]["total"]["value"], 1)
    baseline_total = max(baseline_resp["aggregations"]["total"]["value"], 1)

    recent_terms = {
        b["key"]: b["doc_count"]
        for b in recent_resp["aggregations"]["keywords"]["buckets"]
    }
    baseline_terms = {
        b["key"]: b["doc_count"]
        for b in baseline_resp["aggregations"]["keywords"]["buckets"]
    }

    results = []
    for term, recent_count in recent_terms.items():
        baseline_count = baseline_terms.get(term, 0)
        recent_freq = recent_count / recent_total
        baseline_freq = baseline_count / baseline_total if baseline_total > 0 else 0
        lift_ratio = recent_freq / (baseline_freq + 1e-9)
        results.append(
            {
                "term": term,
                "recent_count": recent_count,
                "baseline_count": baseline_count,
                "lift_ratio": round(lift_ratio, 2),
            }
        )

    results.sort(key=lambda x: x["lift_ratio"], reverse=True)

    return {
        "index": index,
        "recent_window_days": days,
        "baseline_window_days": baseline_days,
        "topics": results[:top_n],
    }


@router.get("/summary")
async def company_summary(
    company: str = Query(..., description="Company name to summarize"),
    top_k: int = Query(20, ge=5, le=50, description="Number of reviews to analyze"),
):
    """
    AI-generated executive intelligence brief for a company.

    Performs hybrid RRF search across all indexed reviews for the company,
    feeds the top results to the LLM, and returns a structured JSON summary:
    overall_sentiment, avg_rating, key_themes, strengths, weaknesses, one_sentence_summary.

    Perfect for a quick competitive intelligence briefing.
    """
    start = time.monotonic()
    settings = get_settings()

    # Hybrid search for this company's reviews
    search_result = await hybrid_search(
        MARKET_INDEX,
        f"{company} customer experience product review",
        filters={"company_name": company},
        top_k=top_k,
    )

    hits = search_result.get("hits", [])
    if not hits:
        return {
            "company": company,
            "source_count": 0,
            "summary": None,
            "message": "No reviews found for this company.",
            "latency_ms": int((time.monotonic() - start) * 1000),
        }

    # Build context from review snippets
    snippets = []
    total_rating = 0.0
    rating_count = 0
    for hit in hits:
        text = hit.get("review_text", hit.get("text", ""))[:300]
        rating = hit.get("rating")
        source = hit.get("source_site", "unknown")
        if text:
            snippets.append(f"[{source}] {text}")
        if rating is not None:
            try:
                total_rating += float(rating)
                rating_count += 1
            except (TypeError, ValueError):
                pass

    avg_rating = round(total_rating / rating_count, 2) if rating_count > 0 else None
    context = "\n\n".join(snippets)

    prompt = f"""You are a business analyst. Based on {len(hits)} customer reviews of {company},
provide a structured intelligence brief.

Return ONLY a JSON object with this schema:
{{"overall_sentiment": "positive|mixed|negative", "avg_rating": {avg_rating or "null"}, "key_themes": ["theme1", "theme2", "theme3", "theme4", "theme5"], "strengths": ["strength1", "strength2", "strength3"], "weaknesses": ["weakness1", "weakness2", "weakness3"], "one_sentence_summary": "One sentence capturing the overall customer perception."}}

REVIEWS:
{context}"""

    client = get_openai_client()
    completion = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
        response_format={"type": "json_object"},
    )

    raw = completion.choices[0].message.content or "{}"
    try:
        summary = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        logger.warning(f"Company summary JSON parse failed for {company}")
        summary = {"one_sentence_summary": raw}

    latency_ms = int((time.monotonic() - start) * 1000)
    logger.info(f"Company summary for '{company}': {len(hits)} reviews analyzed in {latency_ms}ms")

    return {
        "company": company,
        "source_count": len(hits),
        "summary": summary,
        "latency_ms": latency_ms,
    }
