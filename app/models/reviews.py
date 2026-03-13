from pydantic import BaseModel, field_validator
from typing import Any


class ReviewObject(BaseModel):
    review_text: str
    source_site: str
    company_name: str
    rating: float | None = None
    reviewer: str | None = None
    date: str | None = None
    url: str | None = None
    pros: str | None = None
    cons: str | None = None

    @field_validator("rating", mode="before")
    @classmethod
    def coerce_rating(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


class ReviewIngestRequest(BaseModel):
    reviews: list[ReviewObject]


class ReviewIngestResponse(BaseModel):
    indexed: int
    deduplicated: int = 0
    failed: int
    index: str
