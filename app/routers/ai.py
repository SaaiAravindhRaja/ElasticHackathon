from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.rag import rag_query, MODE_CONFIG

router = APIRouter(prefix="/ai", tags=["ai"])


class QueryRequest(BaseModel):
    question: str
    mode: str = "support_bot"


class SourceResult(BaseModel):
    index: str
    score: float
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceResult]
    mode: str
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

    Pipeline: embed question → hybrid RRF search → LLM answer with citations
    """
    if payload.mode not in MODE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{payload.mode}'. Valid modes: {list(MODE_CONFIG.keys())}",
        )

    result = await rag_query(question=payload.question, mode=payload.mode)

    return QueryResponse(
        answer=result.answer,
        sources=[
            SourceResult(index=s.index, score=round(s.score, 4), snippet=s.snippet)
            for s in result.sources
        ],
        mode=result.mode,
        total_context_chunks=result.total_context_chunks,
        latency_ms=result.latency_ms,
    )
