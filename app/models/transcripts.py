from pydantic import BaseModel
from typing import Any, Literal


class TranscriptObject(BaseModel):
    raw_text: str
    source_type: Literal["call", "chat"] = "call"
    subject: str | None = None
    customer_id: str | None = None
    timestamp: str | None = None
    conversation_id: str | None = None
    extracted_features: dict[str, Any] | None = None


class TranscriptIngestRequest(BaseModel):
    transcripts: list[TranscriptObject]


class TranscriptIngestResponse(BaseModel):
    indexed: int
    failed: int
    index: str
