from typing import Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag import rag_query, MODE_CONFIG

router = APIRouter(prefix="/ai", tags=["ai"])


class QueryRequest(BaseModel):
    question: str
    mode: str = "support_bot"
    conversation_id: str | None = None
    output_format: Literal["text", "json"] = "text"


class SourceResult(BaseModel):
    index: str
    score: float
    snippet: str


class QueryResponse(BaseModel):
    answer: str | dict[str, Any]
    sources: list[SourceResult]
    mode: str
    conversation_id: str
    total_context_chunks: int
    latency_ms: int


@router.get("/modes")
async def list_modes():
    """List available RAG modes and their descriptions."""
    return {
        "modes": {
            mode: cfg["description"]
            for mode, cfg in MODE_CONFIG.items()
        }
    }


@router.post("/query", response_model=QueryResponse)
async def ai_query(payload: QueryRequest):
    """
    The core AI endpoint — powers all four ElasticCX products.

    Modes:
    - **support_bot**: answers customer questions from company knowledge base + ticket history
    - **sales_copilot**: generates competitive pitch using competitor reviews + product docs
    - **support_agent**: co-pilots live agent with customer history summary + recommended steps
    - **recommendations**: surfaces product improvements from reviews + support patterns

    Multi-turn: pass `conversation_id` from a prior response to continue a conversation.
    Conversations expire after 30 minutes of inactivity.

    Structured output: set `output_format="json"` to receive a mode-specific JSON object
    instead of a plain text answer. Each mode has its own schema:
    - support_bot / support_agent: {summary, issue_type, severity, suggested_resolution, next_steps, escalation_required, confidence}
    - sales_copilot: {competitor_weaknesses, our_strengths, objection_handlers, recommended_pitch_angle}
    - recommendations: {top_improvements, emerging_patterns, strengths_to_preserve}

    Pipeline: embed question → hybrid RRF search → LLM answer with citations
    """
    if payload.mode not in MODE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{payload.mode}'. Valid modes: {list(MODE_CONFIG.keys())}",
        )

    result = await rag_query(
        question=payload.question,
        mode=payload.mode,
        conversation_id=payload.conversation_id,
        output_format=payload.output_format,
    )

    return QueryResponse(
        answer=result.answer,
        sources=[
            SourceResult(index=s.index, score=round(s.score, 4), snippet=s.snippet)
            for s in result.sources
        ],
        mode=result.mode,
        conversation_id=result.conversation_id,
        total_context_chunks=result.total_context_chunks,
        latency_ms=result.latency_ms,
    )
