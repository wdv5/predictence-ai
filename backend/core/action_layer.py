import httpx
import logging
from datetime import datetime
from ..models.schemas import ActionResult

logger = logging.getLogger("actions")

N8N_WEBHOOK_URL = "http://localhost:5678/webhook/agent-alert"
N8N_ENABLED = False

ACTION_DESCRIPTIONS = {
    "scale_up":        "Trigger horizontal scale-up via orchestrator",
    "clear_cache":     "Flush application and CDN cache layers",
    "restart_service": "Rolling restart of degraded service pods",
    "alert_team":      "Send PagerDuty + Slack notification to on-call team",
}


def execute(action: str, triggered_by: str) -> ActionResult:
    description = ACTION_DESCRIPTIONS.get(action, f"Unknown action: {action}")
    logger.warning(f"[ACTION] {action} | reason={triggered_by} | {description}")
    if N8N_ENABLED:
        status = _n8n_delegate(action, triggered_by)
    else:
        status = "simulated"
        logger.info(f"[ACTION SIMULATED] {description}")
    return ActionResult(
        action=action,
        triggered_by=triggered_by,
        status=status,
        message=description,
        timestamp=datetime.utcnow(),
    )


def _n8n_delegate(action: str, triggered_by: str) -> str:
    try:
        payload = {"action": action, "triggered_by": triggered_by, "timestamp": datetime.utcnow().isoformat()}
        resp = httpx.post(N8N_WEBHOOK_URL, json=payload, timeout=5.0)
        resp.raise_for_status()
        return "delegated"
    except Exception as e:
        logger.error(f"[N8N] failed to delegate {action}: {e}")
        return "failed"