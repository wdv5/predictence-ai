"""
Webhook endpoints designed for n8n consumption.

n8n workflow pattern:
  Webhook Trigger  →  Switch (action type)  →  HTTP Request (AWS/GCP)  →  Slack
"""
from fastapi import APIRouter, Request
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger("webhooks")


@router.post("/n8n/alert", summary="n8n calls this to receive alerts from agent")
async def n8n_receive_alert(request: Request):
    """
    n8n polls or listens here.
    Configure n8n Webhook Trigger node → URL: POST /webhooks/n8n/alert
    """
    body = await request.json()
    logger.info(f"[WEBHOOK/n8n] received: {body}")
    return {"received": True, "timestamp": datetime.utcnow().isoformat()}


@router.post("/n8n/action-result", summary="n8n posts back execution results")
async def n8n_action_result(request: Request):
    """
    After n8n executes an action (scale, Slack, etc.) it posts result here.
    Use 'HTTP Request' node in n8n → POST /webhooks/n8n/action-result
    """
    body = await request.json()
    logger.info(f"[WEBHOOK/n8n] action result: {body}")
    return {"acknowledged": True}


@router.get("/n8n/pending-actions", summary="n8n polls for actions to execute")
def n8n_pending_actions():
    """
    Polling alternative for n8n.
    n8n 'Schedule Trigger' → every 30s → GET this endpoint → Switch node.
    """
    from core.state_store import get_alerts
    from core.rules_engine import recommend_action

    unresolved = get_alerts(limit=10, unresolved_only=True)
    actions = recommend_action(unresolved)

    return {
        "pending_actions": actions,
        "alert_count": len(unresolved),
        "timestamp": datetime.utcnow().isoformat(),
    }
