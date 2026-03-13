"""
POST /agent-builder

Takes any customer input → searches Elasticsearch for real matching context
→ passes everything to Amazon Nova Lite on AWS Bedrock → returns a massive
structured intelligence report.

Demo flow:
  "Zendesk support is slow and nobody replies"
       ↓
  ES finds: similar reviews, tickets, knowledge base entries (live data)
       ↓
  Amazon Nova Lite reads everything and builds:
  - situation analysis & pain points
  - risk assessment (churn probability, P0-P3 severity)
  - step-by-step resolution playbook
  - ready-to-send message templates
  - escalation protocol
  - product signals from the data
  - agent coaching notes
"""
import json
import re
import time
import asyncio
import logging
import boto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import get_settings
from app.services.search import hybrid_search
from app.indices.market_intelligence import INDEX_NAME as REVIEWS_INDEX
from app.indices.customer_history import INDEX_NAME as HISTORY_INDEX
from app.indices.company_knowledge import INDEX_NAME as KNOWLEDGE_INDEX

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent-builder", tags=["agent-builder"])

MODEL_ID = "amazon.nova-lite-v1:0"

_bedrock_client = None


def _get_bedrock():
    global _bedrock_client
    if _bedrock_client is None:
        settings = get_settings()
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            raise HTTPException(
                status_code=503,
                detail="AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not set in .env",
            )
        _bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
    return _bedrock_client


_SYSTEM_PROMPT = """\
You are an elite Customer Intelligence Agent. You receive a raw customer input \
(review, complaint, feedback) together with real data pulled from a live \
Elasticsearch database — similar reviews, support tickets, and knowledge base entries.

Your job: transform this into a comprehensive, production-grade intelligence report \
that a Fortune 500 CX team would actually use.

Be specific. Be detailed. Use the real evidence from the context provided. \
Do not be generic. Every section must contain concrete, actionable content.

Return ONLY a valid JSON object with exactly this structure, no extra text:
{
  "executive_summary": "3-sentence summary of the situation, its severity, and the recommended action",

  "trigger_analysis": {
    "original_input": "the raw customer text",
    "detected_sentiment": "furious | frustrated | disappointed | neutral | positive",
    "urgency": "critical | high | medium | low",
    "primary_intent": "churn_risk | refund_request | technical_issue | billing | feature_request | compliment | venting",
    "pain_points": ["specific pain point 1", "specific pain point 2", "specific pain point 3"],
    "emotion_signals": ["exact words or phrases that reveal emotion"],
    "complaint_pattern": "describe if this matches a known pattern from the data"
  },

  "context_intelligence": {
    "similar_complaints_found": 0,
    "pattern_summary": "what the broader data says about this topic",
    "worst_examples_from_data": ["direct quote from real data 1", "direct quote from real data 2"],
    "how_common_is_this": "rare | occasional | frequent | epidemic",
    "competitor_context": "what the data reveals about how this company handles this issue"
  },

  "risk_assessment": {
    "churn_probability": "0-100%",
    "severity": "P0-CRITICAL | P1-HIGH | P2-MEDIUM | P3-LOW",
    "business_impact": "describe revenue/reputation impact if unresolved",
    "time_to_resolve_sla": "e.g. 2 hours | 24 hours | 3 days",
    "escalation_required": true,
    "escalate_to": "e.g. Senior Support Agent | Customer Success Manager | VP of CX"
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
      },
      {
        "step": 2,
        "action": "next action",
        "channel": "email",
        "owner": "Support Agent",
        "timing": "within 2 hours",
        "goal": "confirm resolution"
      },
      {
        "step": 3,
        "action": "follow-up action",
        "channel": "email",
        "owner": "Customer Success",
        "timing": "within 24 hours",
        "goal": "ensure satisfaction and prevent churn"
      }
    ]
  },

  "response_templates": {
    "immediate_acknowledgement": "full ready-to-send message acknowledging the issue, empathetic and specific",
    "resolution_follow_up": "full message to send once the issue is resolved",
    "internal_escalation_note": "internal note for the next agent or manager picking this up"
  },

  "product_signals": [
    {
      "signal": "specific product or process issue revealed by the data",
      "evidence": "direct quote or pattern from the data",
      "recommended_action": "what the product or ops team should fix",
      "priority": "high | medium | low"
    }
  ],

  "agent_coaching_notes": "2-3 sentences of guidance for the agent — tone to use, what NOT to say, watch-outs",

  "sources_used": 0
}"""


class AgentBuilderRequest(BaseModel):
    input: str
    company: str | None = None        # focus ES search on a specific company
    customer_id: str | None = None    # pull specific customer history


class AgentBuilderResponse(BaseModel):
    report: dict
    sources_searched: int
    latency_ms: int
    model: str


@router.post("", response_model=AgentBuilderResponse)
async def build_agent(payload: AgentBuilderRequest):
    """
    The showpiece endpoint — powered by Amazon Nova Lite on AWS Bedrock.

    Feed it any customer text → searches live Elasticsearch for real matching
    reviews, tickets, and knowledge → Nova reads all of it and builds a full
    structured customer intelligence report.

    One sentence in → complete agent output out.
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

    # ── 3. Build context block ────────────────────────────────────────────────
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
        context_parts.append(f"[{i}] {index_label}  {'  |  '.join(meta)}\n{text}")

    context = "\n\n".join(context_parts) if context_parts else "No matching data found in database."

    user_message = f"""CUSTOMER INPUT:
"{payload.input}"

REAL DATA FROM ELASTICSEARCH ({len(top_hits)} results):
{context}

Build the full intelligence report now. Use the real data above as evidence. Return only the JSON object."""

    # ── 4. Call Amazon Nova Lite on AWS Bedrock (sync in thread) ─────────────
    def _call_bedrock():
        client = _get_bedrock()
        body = {
            "messages": [
                {"role": "user", "content": [{"text": user_message}]}
            ],
            "system": [{"text": _SYSTEM_PROMPT}],
            "inferenceConfig": {
                "maxTokens": 4096,
                "temperature": 0.3,
            },
        }
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        return json.loads(response["body"].read())

    # boto3 is sync — run it in a thread so we don't block the async event loop
    loop = asyncio.get_event_loop()
    bedrock_response = await loop.run_in_executor(None, _call_bedrock)

    raw = bedrock_response["output"]["message"]["content"][0]["text"]

    # ── 5. Parse JSON from response ───────────────────────────────────────────
    def _clean_and_parse(text: str) -> dict:
        # strip ```json ... ``` wrappers
        text = text.strip()
        m = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
        if m:
            text = m.group(1).strip()
        # remove trailing commas before } or ] (common LLM quirk)
        text = re.sub(r",\s*([}\]])", r"\1", text)
        return json.loads(text)

    try:
        report = _clean_and_parse(raw)
    except (json.JSONDecodeError, Exception):
        report = {"raw_output": raw}

    report["sources_used"] = len(top_hits)

    return AgentBuilderResponse(
        report=report,
        sources_searched=len(top_hits),
        latency_ms=int((time.monotonic() - start) * 1000),
        model=MODEL_ID,
    )
