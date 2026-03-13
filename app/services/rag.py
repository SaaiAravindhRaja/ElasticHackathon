import json
import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Literal

from app.services.search import hybrid_search
from app.services.embedder import get_openai_client
from app.services import memory as conv_memory
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

_SUPPORT_BOT_JSON = _SUPPORT_BOT + """

Return your answer as a JSON object with this exact schema:
{"summary": "brief summary of the issue", "issue_type": "billing|technical_issue|refund_request|feature_request|compliment|other", "severity": "low|medium|high|critical", "suggested_resolution": "detailed resolution", "next_steps": ["step 1", "step 2"], "escalation_required": false, "confidence": 0.85}"""

_SALES_COPILOT = """You are an expert B2B sales strategist.
Using the competitor reviews and product documentation provided, craft a targeted, compelling response.
Identify: (1) specific competitor weaknesses revealed in reviews, (2) your product's matching strengths,
(3) objections to preempt. Be data-driven — quote specific review evidence. Avoid generic claims."""

_SALES_COPILOT_JSON = _SALES_COPILOT + """

Return your answer as a JSON object with this exact schema:
{"competitor_weaknesses": ["weakness 1", "weakness 2"], "our_strengths": ["strength 1", "strength 2"], "objection_handlers": ["handler 1", "handler 2"], "recommended_pitch_angle": "one sentence describing the winning pitch angle"}"""

_SUPPORT_AGENT = """You are an AI co-pilot assisting a support agent handling a live customer case.
Based on the customer's history and similar resolved cases:
1. Summarize the customer's situation and current sentiment in 2 sentences
2. Identify the most likely root cause
3. Recommend 2-3 concrete resolution steps in order of priority
Be concise and actionable. An agent is reading this in real-time."""

_SUPPORT_AGENT_JSON = _SUPPORT_AGENT + """

Return your answer as a JSON object with this exact schema:
{"summary": "2-sentence situation summary", "issue_type": "billing|technical_issue|refund_request|feature_request|compliment|other", "severity": "low|medium|high|critical", "suggested_resolution": "root cause + resolution", "next_steps": ["step 1", "step 2", "step 3"], "escalation_required": false, "confidence": 0.85}"""

_RECOMMENDATIONS = """You are a product intelligence analyst generating actionable insights.
Analyze the customer feedback, support tickets, and market reviews provided to:
1. Identify the top 3 most-requested improvements (with evidence)
2. Flag any emerging complaint patterns not yet addressed
3. Surface what customers love and want preserved
Every point must cite specific evidence from the data — no generic observations."""

_RECOMMENDATIONS_JSON = _RECOMMENDATIONS + """

Return your answer as a JSON object with this exact schema:
{"top_improvements": [{"feature": "feature name", "evidence_count": 3, "priority": "high|medium|low"}], "emerging_patterns": ["pattern 1", "pattern 2"], "strengths_to_preserve": ["strength 1", "strength 2"]}"""

MODE_CONFIG: dict[str, dict] = {
    "support_bot": {
        "indices": [COMPANY_INDEX, HISTORY_INDEX],
        "prompt": _SUPPORT_BOT,
        "prompt_json": _SUPPORT_BOT_JSON,
        "description": "Customer-facing support chatbot",
    },
    "sales_copilot": {
        "indices": [MARKET_INDEX, COMPANY_INDEX],
        "prompt": _SALES_COPILOT,
        "prompt_json": _SALES_COPILOT_JSON,
        "description": "B2B sales pitch and competitive intelligence co-pilot",
    },
    "support_agent": {
        "indices": [HISTORY_INDEX],
        "prompt": _SUPPORT_AGENT,
        "prompt_json": _SUPPORT_AGENT_JSON,
        "description": "Real-time agent co-pilot with customer history context",
    },
    "recommendations": {
        "indices": [MARKET_INDEX, HISTORY_INDEX],
        "prompt": _RECOMMENDATIONS,
        "prompt_json": _RECOMMENDATIONS_JSON,
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
    answer: str | dict
    sources: list[RagSource]
    mode: str
    conversation_id: str
    total_context_chunks: int
    latency_ms: int


def _extract_snippet(hit: dict) -> str:
    """Get best text snippet from a hit, preferring highlighted versions."""
    highlights = hit.get("highlights", {})
    for f in ("text", "review_text", "raw_text"):
        if f in highlights:
            return " … ".join(highlights[f])
    for f in ("text", "review_text", "raw_text"):
        val = hit.get(f, "")
        if val:
            return val[:400]
    return ""


async def rag_query(
    question: str,
    mode: str,
    conversation_id: str | None = None,
    output_format: Literal["text", "json"] = "text",
) -> RagResponse:
    """
    Full RAG pipeline with optional multi-turn memory and structured output:
    1. Parallel hybrid RRF search across all mode-relevant indices
    2. Merge + re-rank by score, take top-K
    3. Build cited context string
    4. LLM generates a grounded answer (optionally as structured JSON)
    5. Persist turn to conversation memory
    """
    start = time.monotonic()
    settings = get_settings()
    config = MODE_CONFIG.get(mode)
    if not config:
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {list(MODE_CONFIG.keys())}")

    # Resolve conversation
    if conversation_id is None:
        conversation_id = conv_memory.new_conversation_id()
    history = conv_memory.get_history(conversation_id)

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
        empty_answer: str | dict = (
            {"summary": "No relevant information found.", "issue_type": "other",
             "severity": "low", "suggested_resolution": "Please check available data.",
             "next_steps": [], "escalation_required": False, "confidence": 0.0}
            if output_format == "json" else
            "I couldn't find relevant information to answer your question."
        )
        conv_memory.append_turn(conversation_id, question, str(empty_answer))
        return RagResponse(
            answer=empty_answer,
            sources=[],
            mode=mode,
            conversation_id=conversation_id,
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

    # Build messages: system + prior history + current query
    system_prompt = config["prompt_json"] if output_format == "json" else config["prompt"]
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}",
    })

    # LLM completion
    client = get_openai_client()
    completion_kwargs: dict = dict(
        model=settings.openai_model,
        messages=messages,
        temperature=0.3,
        max_tokens=900,
    )
    if output_format == "json":
        completion_kwargs["response_format"] = {"type": "json_object"}

    completion = await client.chat.completions.create(**completion_kwargs)
    raw_answer = completion.choices[0].message.content or ""

    # Parse JSON or fall back gracefully
    answer: str | dict
    if output_format == "json":
        try:
            answer = json.loads(raw_answer)
        except (json.JSONDecodeError, ValueError):
            logger.warning("RAG JSON parse failed, wrapping as plain text")
            answer = {"answer": raw_answer}
    else:
        answer = raw_answer

    latency_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        f"RAG [{mode}] answered in {latency_ms}ms using {len(top_hits)} chunks "
        f"(conv={conversation_id[:8]}, format={output_format})"
    )

    # Persist to conversation memory
    conv_memory.append_turn(conversation_id, question, answer)

    return RagResponse(
        answer=answer,
        sources=sources,
        mode=mode,
        conversation_id=conversation_id,
        total_context_chunks=len(top_hits),
        latency_ms=latency_ms,
    )
