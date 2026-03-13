from fastapi import APIRouter, Query
from app.services.search import hybrid_search
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/knowledge")
async def search_knowledge(
    q: str = Query(..., description="Natural language search query"),
    doc_type: str | None = Query(None, description="Filter by doc_type (e.g. 'faq', 'pdf')"),
    top_k: int = Query(10, ge=1, le=50),
):
    """
    Hybrid BM25 + kNN search across company-knowledge-index.
    Returns ranked chunks with highlighted snippets.
    """
    filters: dict = {}
    if doc_type:
        filters["doc_type"] = doc_type
    return await hybrid_search(COMPANY_INDEX, q, filters=filters or None, top_k=top_k)


@router.get("/reviews")
async def search_reviews(
    q: str = Query(..., description="Natural language search query"),
    company: str | None = Query(None, description="Filter by company name"),
    sentiment: str | None = Query(None, description="positive | neutral | negative"),
    source_site: str | None = Query(None, description="trustpilot | g2 | capterra"),
    min_rating: float | None = Query(None, ge=0.0, le=5.0, description="Minimum star rating"),
    top_k: int = Query(10, ge=1, le=50),
    boost_recency: bool = Query(False, description="Boost recent reviews in ranking"),
):
    """
    Hybrid search across market-intelligence-index (Trustpilot/G2/Capterra reviews).
    Filter by company, sentiment, source site, or minimum rating.
    Set boost_recency=true to rank recent reviews higher (gaussian decay, 30-day half-life).
    """
    filters: dict = {}
    if company:
        filters["company_name"] = company
    if sentiment:
        filters["sentiment"] = sentiment
    if source_site:
        filters["source_site"] = source_site
    if min_rating is not None:
        filters["min_rating"] = min_rating
    return await hybrid_search(
        MARKET_INDEX, q, filters=filters or None, top_k=top_k, boost_recency=boost_recency
    )


@router.get("/customers")
async def search_customers(
    q: str = Query(..., description="Natural language search query"),
    customer_id: str | None = Query(None),
    source_type: str | None = Query(None, description="email | call | chat"),
    intent: str | None = Query(None, description="billing | technical_issue | refund_request | etc."),
    top_k: int = Query(10, ge=1, le=50),
):
    """
    Hybrid search across customer-history-index (emails, calls, chats).
    Filter by customer, source type, or detected intent.
    """
    filters: dict = {}
    if customer_id:
        filters["customer_id"] = customer_id
    if source_type:
        filters["source_type"] = source_type
    if intent:
        filters["intent"] = intent
    return await hybrid_search(HISTORY_INDEX, q, filters=filters or None, top_k=top_k)
