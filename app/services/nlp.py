import json
import logging
from app.services.embedder import get_openai_client
from app.config import get_settings

logger = logging.getLogger(__name__)

_EXTRACT_PROMPT = """Analyze this customer message and extract structured information.
Return ONLY valid JSON with these exact keys:
{
  "sentiment": "positive" | "neutral" | "negative",
  "intent": "billing" | "technical_issue" | "refund_request" | "feature_request" | "compliment" | "other",
  "topics": ["topic1", "topic2", "topic3"]
}
topics should be 3-5 short phrases (2-4 words each) describing what the customer is talking about.
No explanation, just the JSON object."""


async def enrich(text: str) -> dict:
    """
    Extract sentiment, intent, and topics from customer text via LLM.
    Returns dict with keys: sentiment, intent, topics.
    Never raises — falls back to safe defaults on any failure so ingestion continues.
    """
    if not text or not text.strip():
        return {"sentiment": "neutral", "intent": "other", "topics": []}

    settings = get_settings()
    client = get_openai_client()
    truncated = text[:2000]

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": _EXTRACT_PROMPT},
                {"role": "user", "content": truncated},
            ],
            temperature=0.0,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "sentiment": result.get("sentiment", "neutral"),
            "intent": result.get("intent", "other"),
            "topics": result.get("topics", []),
        }
    except Exception as e:
        logger.warning(f"NLP enrichment failed (using defaults): {e}")
        return {"sentiment": "neutral", "intent": "other", "topics": []}
