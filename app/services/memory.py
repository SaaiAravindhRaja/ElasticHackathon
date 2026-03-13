"""
In-memory conversation store for multi-turn RAG sessions.
Conversations expire after 30 minutes of inactivity.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

_TTL_MINUTES = 30

# {conversation_id: {"messages": [...], "updated_at": datetime}}
_store: dict[str, dict] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cleanup() -> None:
    cutoff = _now() - timedelta(minutes=_TTL_MINUTES)
    expired = [cid for cid, v in _store.items() if v["updated_at"] < cutoff]
    for cid in expired:
        del _store[cid]
        logger.debug(f"Expired conversation {cid}")


def get_history(conversation_id: str) -> list[dict]:
    """Return prior [{role, content}] turns for this conversation (empty if unknown/expired)."""
    entry = _store.get(conversation_id)
    if entry is None:
        return []
    return list(entry["messages"])


def append_turn(conversation_id: str, question: str, answer: str) -> None:
    """Record a completed Q&A turn. Creates the entry if it doesn't exist."""
    _cleanup()
    if conversation_id not in _store:
        _store[conversation_id] = {"messages": [], "updated_at": _now()}
    entry = _store[conversation_id]
    entry["messages"].extend([
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer if isinstance(answer, str) else str(answer)},
    ])
    entry["updated_at"] = _now()


def new_conversation_id() -> str:
    return str(uuid.uuid4())
