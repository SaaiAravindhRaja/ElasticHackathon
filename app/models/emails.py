from pydantic import BaseModel
from typing import Any


class EmailObject(BaseModel):
    raw_text: str
    subject: str | None = None
    customer_id: str | None = None
    timestamp: str | None = None
    conversation_id: str | None = None
    extracted_features: dict[str, Any] | None = None


class EmailIngestRequest(BaseModel):
    emails: list[EmailObject]


class EmailIngestResponse(BaseModel):
    indexed: int
    failed: int
    index: str
