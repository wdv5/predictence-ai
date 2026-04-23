from fastapi import APIRouter
from ..core.action_layer import execute, ACTION_DESCRIPTIONS
from typing import Literal

router = APIRouter()

ActionName = Literal["scale_up", "clear_cache", "restart_service", "alert_team"]


@router.post("/trigger/{action}", summary="Manually trigger an action (for n8n or testing)")
def trigger_action(action: ActionName, reason: str = "manual"):
    result = execute(action, triggered_by=reason)
    return result.model_dump()


@router.get("/available")
def list_actions():
    return ACTION_DESCRIPTIONS