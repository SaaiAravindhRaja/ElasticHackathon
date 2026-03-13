"""
Percolator-based alert registration.

Register an Elasticsearch query as an alert. When new documents are ingested,
they are automatically matched against all registered alerts. If a document
matches an alert query, the alert name is logged and returned.

Example — register a churn signal alert:
    POST /alerts
    {
        "name": "Churn Signal",
        "description": "Fires when a review mentions cancellation intent",
        "target_index": "market-intelligence-index",
        "query_dsl": {"match": {"review_text": "cancel subscription"}}
    }
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from app.services.elasticsearch import get_es_client
from app.indices.alerts import INDEX_NAME as ALERTS_INDEX

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertCreateRequest(BaseModel):
    name: str
    description: str = ""
    target_index: str
    query_dsl: dict[str, Any]


class AlertResponse(BaseModel):
    id: str
    name: str
    description: str
    target_index: str
    query_dsl: dict[str, Any]
    created_at: str


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(payload: AlertCreateRequest):
    """Register a new percolator alert query."""
    client = get_es_client()
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "name": payload.name,
        "description": payload.description,
        "target_index": payload.target_index,
        "query": payload.query_dsl,   # stored as percolator type
        "created_at": now,
    }
    response = await client.index(index=ALERTS_INDEX, document=doc, refresh=True)
    alert_id = response["_id"]
    logger.info(f"Registered alert '{payload.name}' (id={alert_id}) for {payload.target_index}")
    return AlertResponse(
        id=alert_id,
        name=payload.name,
        description=payload.description,
        target_index=payload.target_index,
        query_dsl=payload.query_dsl,
        created_at=now,
    )


@router.get("", response_model=list[AlertResponse])
async def list_alerts():
    """List all registered percolator alerts."""
    client = get_es_client()
    response = await client.search(
        index=ALERTS_INDEX,
        body={"query": {"match_all": {}}, "size": 100, "_source": True},
    )
    alerts = []
    for hit in response["hits"]["hits"]:
        src = hit["_source"]
        alerts.append(
            AlertResponse(
                id=hit["_id"],
                name=src.get("name", ""),
                description=src.get("description", ""),
                target_index=src.get("target_index", ""),
                query_dsl=src.get("query", {}),
                created_at=src.get("created_at", ""),
            )
        )
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Retrieve a single alert by ID."""
    client = get_es_client()
    try:
        hit = await client.get(index=ALERTS_INDEX, id=alert_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    src = hit["_source"]
    return AlertResponse(
        id=hit["_id"],
        name=src.get("name", ""),
        description=src.get("description", ""),
        target_index=src.get("target_index", ""),
        query_dsl=src.get("query", {}),
        created_at=src.get("created_at", ""),
    )


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: str):
    """Remove a registered alert."""
    client = get_es_client()
    try:
        await client.delete(index=ALERTS_INDEX, id=alert_id, refresh=True)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    logger.info(f"Deleted alert {alert_id}")
