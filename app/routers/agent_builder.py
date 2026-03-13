"""
POST /agent-builder

Takes any customer input (a complaint, a review, a message) → searches
Elasticsearch for real matching context → passes everything to Claude →
returns a massive, structured intelligence report.

Demo flow:
  "Zendesk support is slow and nobody replies"
       ↓
  ES finds: similar reviews, matching tickets, knowledge base entries
       ↓
  Claude reads all of it and builds a full agent output:
  - situation analysis
  - pain point breakdown
  - response playbook (step by step)
  - draft message templates (email, chat, internal)
  - escalation protocol
  - product signals
  - executive summary
"""
import time
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from app.config import get_settings
from app.services.search import hybrid_search
from app.indices.market_intelligence import INDEX_NAME as REVIEWS_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX
from app.indices.company_knowledge import INDEX_NAME as KNOWLEDGE_INDEX

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-builder", tags=["agent-builder"])

_claude: AsyncAnthropic | None = None


def _get_claude() -> AsyncAnthropic:
    global _claude
    if _claude is None:
        key = get_settings().anthropic_api_key
        if not key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY not set. Add it to your .env file.",
            )
        _claude = AsyncAnthropic(api_key=key)
    return _claude


_SYSTEM = """\
You are an elite Customer Intelligence Agent. You receive a raw customer input \
(review, complaint, feedback) together with real data pulled from a live \
Elasticsearch database — similar reviews, support tickets, and knowledge base entries.

Your job: transform this into a comprehensive, production-grade intelligence report \
that a Fortune 500 CX team would actually use.

Be specific. Be detailed. Use the real evidence from the context provided. \
Do not be generic. Every section must contain concrete, actionable content.

Return a single JSON object with exactly this structure:
{
  "executive_summary": "3-sentence summary of the situation, its severity, and the recommended action",

  "trigger_analysis": {
    "original_input": "the raw customer text",
    "detected_sentiment": "furious | frustrated | disappointed | neutral | positive",
    "urgency": "critical | high | medium | low",
    "primary_intent": "churn_risk | refund_request | technical_issue | billing | feature_request | compliment | venting",
    "pain_points": ["specific pain point 1", "specific pain point 2", "specific pain point 3"],
    "emotion_signals": ["exact words or phrases that reveal emotion"],
    "is_repeat_complaint": true or false,
    "complaint_pattern": "describe if this matches a known pattern from the data"
  },

  "context_intelligence": {
    "similar_complaints_found": 0,
    "pattern_summary": "what the broader data says about this topic",
    "worst_examples_from_data": ["quote from real data 1", "quote from real data 2"],
    "how_common_is_this": "rare | occasional | frequent | epidemic",
    "competitor_context": "what the data reveals about how competitors handle this"
  },

  "risk_assessment": {
    "churn_probability": "0–100%",
    "severity": "P0-CRITICAL | P1-HIGH | P2-MEDIUM | P3-LOW",
    "business_impact": "describe the revenue/reputation impact if unresolved",
    "time_to_resolve_sla": "e.g. 2 hours | 24 hours | 3 days",
    "escalation_required": true or false,
    "escalate_to": "e.g. Senior Support Agent | Customer Success Manager | VP of CX | Engineering"
  },

  "resolution_playbook": {
    "strategy": "one sentence describing the overall resolution strategy",
    "steps": [
      {
        "step": 1,
        "action": "specific action to take",
        "channel": "email | phone | live_chat | internal",
        "owner": "role responsible",
        "timing": "e.g. within 15 minutes",
        "goal": "what success looks like for this step"
      }
    ]
  },

  "response_templates": {
    "immediate_acknowledgement": "full ready-to-send message acknowledging the issue (empathetic, specific, not generic)",
    "resolution_follow_up": "full message to send once resolved",
    "internal_escalation_note": "internal note for the next agent or manager picking this up"
  },

  "product_signals": [
    {
      "signal": "specific product or process issue revealed",
      "evidence": "quote or pattern from the data",
      "recommended_action": "what the product/ops team should do about it",
      "priority": "high | medium | low"
    }
  ],

  "agent_coaching_notes": "2-3 sentences of guidance for the agent handling this — tone, watch-outs, what NOT to say",

  "sources_used": 0
}
"""


class AgentBuilderRequest(BaseModel):
    input: str
    company: str | None = None          # optional: focus search on a specific company
    customer_id: str | None = None      # optional: pull specific customer history


class AgentBuilderResponse(BaseModel):
    report: dict
    sources_searched: int
    latency_ms: int
    model: str


@router.post("", response_model=AgentBuilderResponse)
async def build_agent(payload: AgentBuilderRequest):
    """
    The showpiece endpoint.

    Feed it any customer text → it searches the live Elasticsearch database for
    real matching reviews, tickets, and knowledge → Claude reads everything and
    builds a complete customer intelligence report.

    Great for demos: one sentence in, full structured agent output out.
    """
    start = time.monotonic()

    # ── 1. Parallel ES search across all 3 indices ───────────────────────────
    review_filters = {}
    if payload.company:
        review_filters["company_name"] = payload.company

    history_filters = {}
    if payload.customer_id:
        history_filters["customer_id"] = payload.customer_id

    tasks = [
        hybrid_search(REVIEWS_INDEX,   payload.input, filters=review_filters or None, top_k=6),
        hybrid_search(HISTORY_INDEX,   payload.input, filters=history_filters or None, top_k=4),
        hybrid_search(KNOWLEDGE_INDEX, payload.input, top_k=3),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # ── 2. Collect all hits ───────────────────────────────────────────────────
    all_hits: list[dict] = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning(f"Agent builder search error: {r}")
            continue
        all_hits.extend(r.get("hits", []))

    all_hits.sort(key=lambda h: h.get("score", 0), reverse=True)
    top_hits = all_hits[:12]

    # ── 3. Build context block for Claude ────────────────────────────────────
    context_parts = []
    for i, hit in enumerate(top_hits, 1):
        index_label = hit["index"].replace("-index", "").replace("-", " ").title()
        text = (
            hit.get("review_text")
            or hit.get("raw_text")
            or hit.get("text")
            or ""
        )[:500]
        meta = []
        if hit.get("company_name"): meta.append(f"company={hit['company_name']}")
        if hit.get("sentiment"):    meta.append(f"sentiment={hit['sentiment']}")
        if hit.get("rating"):       meta.append(f"rating={hit['rating']}★")
        if hit.get("intent"):       meta.append(f"intent={hit['intent']}")
        meta_str = "  |  ".join(meta)
        context_parts.append(f"[{i}] {index_label}  {meta_str}\n{text}")

    context = "\n\n".join(context_parts) if context_parts else "No matching data found in database."

    user_message = f"""CUSTOMER INPUT:
\"{payload.input}\"

REAL DATA FROM ELASTICSEARCH ({len(top_hits)} results):
{context}

Build the full intelligence report now. Use the real data above as evidence throughout."""

    # ── 4. Call Claude ────────────────────────────────────────────────────────
    claude = _get_claude()
    message = await claude.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = message.content[0].text

    # ── 5. Parse JSON ─────────────────────────────────────────────────────────
    import json, re
    try:
        report = json.loads(raw)
    except json.JSONDecodeError:
        # Claude sometimes wraps in ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", raw)
        if match:
            report = json.loads(match.group(1))
        else:
            report = {"raw_output": raw}

    report["sources_used"] = len(top_hits)

    return AgentBuilderResponse(
        report=report,
        sources_searched=len(top_hits),
        latency_ms=int((time.monotonic() - start) * 1000),
        model="claude-opus-4-6",
    )
