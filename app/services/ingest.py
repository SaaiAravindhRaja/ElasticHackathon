import uuid
import logging
import fitz  # PyMuPDF
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.elasticsearch import bulk_index_with_dedup, get_es_client
from app.services.dedup import content_fingerprint
from app.services import nlp
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX
from app.indices.alerts import INDEX_NAME as ALERTS_INDEX
from app.models.reviews import ReviewObject
from app.models.emails import EmailObject
from app.models.transcripts import TranscriptObject

logger = logging.getLogger(__name__)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    return "\n\n".join(pages)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sentiment_from_rating(rating: float | None) -> str:
    if rating is None:
        return "neutral"
    if rating >= 4.0:
        return "positive"
    if rating >= 3.0:
        return "neutral"
    return "negative"


async def _percolate_check(target_index: str, doc: dict) -> list[str]:
    """
    Match a document against all registered percolator alerts for this index.
    Returns the names of triggered alerts. Never raises — errors are logged only.
    """
    try:
        client = get_es_client()
        response = await client.search(
            index=ALERTS_INDEX,
            body={
                "query": {
                    "bool": {
                        "must": [
                            {"percolate": {"field": "query", "document": doc}}
                        ],
                        "filter": [
                            {"term": {"target_index": target_index}}
                        ],
                    }
                },
                "_source": ["name"],
                "size": 50,
            },
        )
        triggered = [hit["_source"]["name"] for hit in response["hits"]["hits"]]
        if triggered:
            logger.info(f"Alerts triggered for {target_index}: {triggered}")
        return triggered
    except Exception as e:
        logger.warning(f"Percolate check failed (non-blocking): {e}")
        return []


async def ingest_document(
    title: str,
    text: str,
    doc_type: str = "general",
    source_url: str | None = None,
    company_name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, int, int]:
    """
    Chunk → embed → deduplicated bulk index to company-knowledge-index.
    Returns (document_id, chunks_indexed, chunks_deduplicated).
    """
    settings = get_settings()
    document_id = str(uuid.uuid4())
    now = _now_iso()

    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return document_id, 0, 0

    embeddings = await embed_texts([c.text for c in chunks])

    docs = []
    for chunk, embedding in zip(chunks, embeddings):
        fp = content_fingerprint(COMPANY_INDEX, chunk.text)
        docs.append(
            {
                "_id": fp,
                "title": title,
                "text": chunk.text,
                "text_embedding": embedding,
                "doc_type": doc_type,
                "source_url": source_url,
                "company_name": company_name,
                "metadata": metadata or {},
                "timestamp": now,
                "chunk_id": chunk.chunk_id,
                "total_chunks": chunk.total_chunks,
                "document_id": document_id,
            }
        )

    indexed, deduped, failed = await bulk_index_with_dedup(COMPANY_INDEX, docs)

    # Percolate the first chunk (non-blocking — alerts fire on any new doc content)
    if docs and indexed > 0:
        await _percolate_check(COMPANY_INDEX, {k: v for k, v in docs[0].items() if k != "_id"})

    logger.info(
        f"Document '{title}': {indexed} indexed, {deduped} deduplicated, {failed} failed"
    )
    return document_id, indexed, deduped


async def ingest_reviews(reviews: list[ReviewObject]) -> tuple[int, int, int]:
    """
    Embed → deduplicated index to market-intelligence-index.
    Sentiment is derived from star rating (or LLM if rating is absent).
    Returns (indexed, deduplicated, failed).
    """
    if not reviews:
        return 0, 0, 0

    embeddings = await embed_texts([r.review_text for r in reviews])

    docs = []
    for review, embedding in zip(reviews, embeddings):
        fp = content_fingerprint(MARKET_INDEX, review.review_text)
        docs.append(
            {
                "_id": fp,
                "source_site": review.source_site,
                "company_name": review.company_name,
                "review_text": review.review_text,
                "text_embedding": embedding,
                "rating": review.rating,
                "sentiment": _sentiment_from_rating(review.rating),
                "reviewer": review.reviewer,
                "date": review.date,
                "url": review.url,
                "pros": review.pros,
                "cons": review.cons,
            }
        )

    indexed, deduped, failed = await bulk_index_with_dedup(MARKET_INDEX, docs)

    # Percolate first doc to trigger any registered review alerts
    if docs and indexed > 0:
        await _percolate_check(MARKET_INDEX, {k: v for k, v in docs[0].items() if k != "_id"})

    return indexed, deduped, failed


async def ingest_emails(emails: list[EmailObject]) -> tuple[int, int, int]:
    """
    Chunk + NLP enrich → embed → deduplicated index to customer-history-index.
    NLP extraction (sentiment, intent, topics) runs on full email text, not per chunk.
    Returns (indexed, deduplicated, failed).
    """
    settings = get_settings()
    all_docs: list[dict] = []

    for email in emails:
        # NLP enrichment on the full email text (once, not per chunk)
        enrichment = await nlp.enrich(email.raw_text)

        chunks = chunk_text(email.raw_text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            continue
        embeddings = await embed_texts([c.text for c in chunks])

        for chunk, embedding in zip(chunks, embeddings):
            fp = content_fingerprint(HISTORY_INDEX, chunk.text)
            all_docs.append(
                {
                    "_id": fp,
                    "source_type": "email",
                    "raw_text": chunk.text,
                    "text_embedding": embedding,
                    "extracted_features": {
                        **(email.extracted_features or {}),
                        **enrichment,
                    },
                    "sentiment": enrichment["sentiment"],
                    "intent": enrichment["intent"],
                    "topics": enrichment["topics"],
                    "customer_id": email.customer_id,
                    "timestamp": email.timestamp,
                    "subject": email.subject,
                    "chunk_id": chunk.chunk_id,
                    "conversation_id": email.conversation_id,
                }
            )

    indexed, deduped, failed = await bulk_index_with_dedup(HISTORY_INDEX, all_docs)

    if all_docs and indexed > 0:
        await _percolate_check(HISTORY_INDEX, {k: v for k, v in all_docs[0].items() if k != "_id"})

    return indexed, deduped, failed


async def ingest_transcripts(transcripts: list[TranscriptObject]) -> tuple[int, int, int]:
    """
    Chunk + NLP enrich → embed → deduplicated index to customer-history-index.
    Returns (indexed, deduplicated, failed).
    """
    settings = get_settings()
    all_docs: list[dict] = []

    for transcript in transcripts:
        enrichment = await nlp.enrich(transcript.raw_text)

        chunks = chunk_text(transcript.raw_text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            continue
        embeddings = await embed_texts([c.text for c in chunks])

        for chunk, embedding in zip(chunks, embeddings):
            fp = content_fingerprint(HISTORY_INDEX, chunk.text)
            all_docs.append(
                {
                    "_id": fp,
                    "source_type": transcript.source_type,
                    "raw_text": chunk.text,
                    "text_embedding": embedding,
                    "extracted_features": {
                        **(transcript.extracted_features or {}),
                        **enrichment,
                    },
                    "sentiment": enrichment["sentiment"],
                    "intent": enrichment["intent"],
                    "topics": enrichment["topics"],
                    "customer_id": transcript.customer_id,
                    "timestamp": transcript.timestamp,
                    "subject": transcript.subject,
                    "chunk_id": chunk.chunk_id,
                    "conversation_id": transcript.conversation_id,
                }
            )

    indexed, deduped, failed = await bulk_index_with_dedup(HISTORY_INDEX, all_docs)

    if all_docs and indexed > 0:
        await _percolate_check(HISTORY_INDEX, {k: v for k, v in all_docs[0].items() if k != "_id"})

    return indexed, deduped, failed
