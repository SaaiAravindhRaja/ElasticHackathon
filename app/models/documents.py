from pydantic import BaseModel
from typing import Any


class DocumentIngestRequest(BaseModel):
    title: str
    text: str
    doc_type: str = "general"
    source_url: str | None = None
    metadata: dict[str, Any] | None = None


class DocumentIngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    index: str
