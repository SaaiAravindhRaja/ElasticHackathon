import uuid
import logging
import fitz  # PyMuPDF
from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services.elasticsearch import bulk_index
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX
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


async def ingest_document(
    title: str,
    text: str,
    doc_type: str = "general",
    source_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[str, int]:
    """Chunk → embed → index to company-knowledge-index. Returns (document_id, chunks_indexed)."""
    settings = get_settings()
    document_id = str(uuid.uuid4())
    now = _now_iso()

    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        return document_id, 0

    embeddings = await embed_texts([c.text for c in chunks])

    docs = [
        {
            "title": title,
            "text": chunk.text,
            "text_embedding": embedding,
            "doc_type": doc_type,
            "source_url": source_url,
            "metadata": metadata or {},
            "timestamp": now,
            "chunk_id": chunk.chunk_id,
            "total_chunks": chunk.total_chunks,
            "document_id": document_id,
        }
        for chunk, embedding in zip(chunks, embeddings)
    ]

    success, failed = await bulk_index(COMPANY_INDEX, docs)
    logger.info(f"Ingested document '{title}': {success} chunks indexed, {failed} failed")
    return document_id, success


async def ingest_reviews(reviews: list[ReviewObject]) -> tuple[int, int]:
    """Embed → index to market-intelligence-index. Reviews are not chunked."""
    if not reviews:
        return 0, 0

    embeddings = await embed_texts([r.review_text for r in reviews])

    docs = [
        {
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
        for review, embedding in zip(reviews, embeddings)
    ]

    return await bulk_index(MARKET_INDEX, docs)


async def ingest_emails(emails: list[EmailObject]) -> tuple[int, int]:
    """Chunk → embed → index to customer-history-index."""
    settings = get_settings()
    all_docs: list[dict] = []

    for email in emails:
        chunks = chunk_text(email.raw_text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            continue
        embeddings = await embed_texts([c.text for c in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            all_docs.append(
                {
                    "source_type": "email",
                    "raw_text": chunk.text,
                    "text_embedding": embedding,
                    "extracted_features": email.extracted_features or {},
                    "sentiment": None,
                    "customer_id": email.customer_id,
                    "timestamp": email.timestamp,
                    "subject": email.subject,
                    "chunk_id": chunk.chunk_id,
                    "conversation_id": email.conversation_id,
                }
            )

    return await bulk_index(HISTORY_INDEX, all_docs)


async def ingest_transcripts(transcripts: list[TranscriptObject]) -> tuple[int, int]:
    """Chunk → embed → index to customer-history-index."""
    settings = get_settings()
    all_docs: list[dict] = []

    for transcript in transcripts:
        chunks = chunk_text(transcript.raw_text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            continue
        embeddings = await embed_texts([c.text for c in chunks])
        for chunk, embedding in zip(chunks, embeddings):
            all_docs.append(
                {
                    "source_type": transcript.source_type,
                    "raw_text": chunk.text,
                    "text_embedding": embedding,
                    "extracted_features": transcript.extracted_features or {},
                    "sentiment": None,
                    "customer_id": transcript.customer_id,
                    "timestamp": transcript.timestamp,
                    "subject": transcript.subject,
                    "chunk_id": chunk.chunk_id,
                    "conversation_id": transcript.conversation_id,
                }
            )

    return await bulk_index(HISTORY_INDEX, all_docs)
