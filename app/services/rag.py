import time
import asyncio
import logging
from dataclasses import dataclass, field

from app.services.search import hybrid_search
from app.services.embedder import get_openai_client
from app.config import get_settings
from app.indices.company_knowledge import INDEX_NAME as COMPANY_INDEX
from app.indices.market_intelligence import INDEX_NAME as MARKET_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX

logger = logging.getLogger(__name__)

# ── System prompts ──────────────────────────────────────────────────────────

_SUPPORT_BOT = """You are a knowledgeable customer support agent for a SaaS company.
Answer the customer's question using ONLY the provided knowledge base and ticket history.
Be concise, accurate, and friendly. If the context doesn't contain the answer, say so clearly.
Reference specific sources by their [N] citation number."""

_SALES_COPILOT = """You are an expert B2B sales strategist.
Using the competitor reviews and product documentation provided, craft a targeted, compelling response.
Identify: (1) specific competitor weaknesses revealed in reviews, (2) your product's matching strengths,
(3) objections to preempt. Be data-driven — quote specific review evidence. Avoid generic claims."""

_SUPPORT_AGENT = """You are an AI co-pilot assisting a support agent handling a live customer case.
Based on the customer's history and similar resolved cases:
1. Summarize the customer's situation and current sentiment in 2 sentences
2. Identify the most likely root cause
3. Recommend 2-3 concrete resolution steps in order of priority
Be concise and actionable. An agent is reading this in real-time."""

_RECOMMENDATIONS = """You are a product intelligence analyst generating actionable insights.
Analyze the customer feedback, support tickets, and market reviews provided to:
1. Identify the top 3 most-requested improvements (with evidence)
2. Flag any emerging complaint patterns not yet addressed
3. Surface what customers love and want preserved
Every point must cite specific evidence from the data — no generic observations."""

MODE_CONFIG: dict[str, dict] = {
    "support_bot": {
        "indices": [COMPANY_INDEX, HISTORY_INDEX],
        "prompt": _SUPPORT_BOT,
        "description": "Customer-facing support chatbot",
    },
    "sales_copilot": {
        "indices": [MARKET_INDEX, COMPANY_INDEX],
        "prompt": _SALES_COPILOT,
        "description": "B2B sales pitch and competitive intelligence co-pilot",
    },
    "support_agent": {
        "indices": [HISTORY_INDEX],
        "prompt": _SUPPORT_AGENT,
        "description": "Real-time agent co-pilot with customer history context",
    },
    "recommendations": {
        "indices": [MARKET_INDEX, HISTORY_INDEX],
        "prompt": _RECOMMENDATIONS,
        "description": "Product recommendations from reviews and support patterns",
    },
}


@dataclass
class RagSource:
    index: str
    score: float
    snippet: str
    metadata: dict = field(default_factory=dict)


@dataclass
class RagResponse:
    answer: str
    sources: list[RagSource]
    mode: str
    total_context_chunks: int
    latency_ms: int


def _extract_snippet(hit: dict) -> str:
    """Get best text snippet from a hit, preferring highlighted versions."""
    highlights = hit.get("highlights", {})
    for field in ("text", "review_text", "raw_text"):
        if field in highlights:
            return " … ".join(highlights[field])
    for field in ("text", "review_text", "raw_text"):
        val = hit.get(field, "")
        if val:
            return val[:400]
    return ""


async def rag_query(question: str, mode: str) -> RagResponse:
    """
    Full RAG pipeline:
    1. Parallel hybrid RRF search across all mode-relevant indices
    2. Merge + re-rank by score, take top-K
    3. Build cited context string
    4. LLM generates a grounded answer
    """
    start = time.monotonic()
    settings = get_settings()
    config = MODE_CONFIG.get(mode)
    if not config:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {list(MODE_CONFIG.keys())}")

    # Parallel search across all relevant indices
    tasks = [
        hybrid_search(idx, question, top_k=settings.rag_top_k)
        for idx in config["indices"]
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_hits: list[dict] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"RAG search error: {result}")
            continue
        all_hits.extend(result.get("hits", []))

    # Merge-sort by score, take top-K
    all_hits.sort(key=lambda h: h.get("score", 0.0), reverse=True)
    top_hits = all_hits[: settings.rag_top_k]

    if not top_hits:
        return RagResponse(
            answer="I couldn't find relevant information to answer your question.",
            sources=[],
            mode=mode,
            total_context_chunks=0,
            latency_ms=int((time.monotonic() - start) * 1000),
        )

    # Build numbered context + source list
    context_parts: list[str] = []
    sources: list[RagSource] = []
    _skip_fields = {"text", "review_text", "raw_text", "highlights", "text_embedding"}

    for i, hit in enumerate(top_hits, 1):
        snippet = _extract_snippet(hit)
        index_label = hit["index"].replace("-index", "").replace("-", " ").title()
        context_parts.append(f"[{i}] {index_label}\n{snippet}")
        sources.append(
            RagSource(
                index=hit["index"],
                score=hit.get("score", 0.0),
                snippet=snippet[:300],
                metadata={k: v for k, v in hit.items() if k not in _skip_fields},
            )
        )

    context = "\n\n".join(context_parts)

    # LLM completion
    client = get_openai_client()
    completion = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": config["prompt"]},
            {
                "role": "user",
                "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}",
            },
        ],
        temperature=0.3,
        max_tokens=900,
    )

    answer = completion.choices[0].message.content or ""
    latency_ms = int((time.monotonic() - start) * 1000)
    logger.info(f"RAG [{mode}] answered in {latency_ms}ms using {len(top_hits)} chunks")

    return RagResponse(
        answer=answer,
        sources=sources,
        mode=mode,
        total_context_chunks=len(top_hits),
        latency_ms=latency_ms,
    )
