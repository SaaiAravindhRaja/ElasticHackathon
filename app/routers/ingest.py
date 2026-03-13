import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from app.models.documents import DocumentIngestRequest, DocumentIngestResponse
from app.models.emails import EmailIngestRequest, EmailIngestResponse
from app.models.transcripts import TranscriptIngestRequest, TranscriptIngestResponse
from app.models.reviews import ReviewIngestRequest, ReviewIngestResponse
from app.services import ingest as ingest_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/documents", response_model=DocumentIngestResponse)
async def ingest_documents_json(payload: DocumentIngestRequest):
    """Ingest a document from JSON. Chunks, embeds, and indexes into company-knowledge-index."""
    document_id, chunks = await ingest_service.ingest_document(
        title=payload.title,
        text=payload.text,
        doc_type=payload.doc_type,
        source_url=payload.source_url,
        metadata=payload.metadata,
    )
    return DocumentIngestResponse(
        document_id=document_id,
        chunks_indexed=chunks,
        index="company-knowledge-index",
    )


@router.post("/documents/pdf", response_model=DocumentIngestResponse)
async def ingest_documents_pdf(
    file: UploadFile = File(...),
    title: str = Form("Uploaded PDF"),
    doc_type: str = Form("pdf"),
    source_url: str | None = Form(None),
):
    """Upload a PDF file. Extracts text with PyMuPDF, chunks, embeds, and indexes."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    try:
        text = ingest_service.extract_pdf_text(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF extraction failed: {e}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="PDF appears to contain no extractable text")

    document_id, chunks = await ingest_service.ingest_document(
        title=title,
        text=text,
        doc_type=doc_type,
        source_url=source_url,
    )
    return DocumentIngestResponse(
        document_id=document_id,
        chunks_indexed=chunks,
        index="company-knowledge-index",
    )


@router.post("/emails", response_model=EmailIngestResponse)
async def ingest_emails(payload: EmailIngestRequest):
    """Ingest an array of email objects into customer-history-index."""
    success, failed = await ingest_service.ingest_emails(payload.emails)
    return EmailIngestResponse(indexed=success, failed=failed, index="customer-history-index")


@router.post("/transcripts", response_model=TranscriptIngestResponse)
async def ingest_transcripts(payload: TranscriptIngestRequest):
    """Ingest call or chat transcripts into customer-history-index."""
    success, failed = await ingest_service.ingest_transcripts(payload.transcripts)
    return TranscriptIngestResponse(indexed=success, failed=failed, index="customer-history-index")


@router.post("/reviews", response_model=ReviewIngestResponse)
async def ingest_reviews(payload: ReviewIngestRequest):
    """Ingest structured reviews (from scraper) into market-intelligence-index."""
    success, failed = await ingest_service.ingest_reviews(payload.reviews)
    return ReviewIngestResponse(indexed=success, failed=failed, index="market-intelligence-index")
