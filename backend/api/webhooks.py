from fastapi import APIRouter, Request
from ..core.state_store import get_alerts
from ..core.rules_engine import recommend_action
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger("webhooks")


@router.post("/n8n/alert")
async def n8n_receive_alert(request: Request):
    body = await request.json()
    logger.info(f"[WEBHOOK/n8n] received: {body}")
    return {"received": True, "timestamp": datetime.utcnow().isoformat()}


@router.post("/n8n/action-result")
async def n8n_action_result(request: Request):
    body = await request.json()
    logger.info(f"[WEBHOOK/n8n] action result: {body}")
    return {"acknowledged": True}


@router.get("/n8n/pending-actions")
def n8n_pending_actions():
    unresolved = get_alerts(limit=10, unresolved_only=True)
    actions = recommend_action(unresolved)
    return {
        "pending_actions": actions,
        "alert_count": len(unresolved),
        "timestamp": datetime.utcnow().isoformat(),
    }