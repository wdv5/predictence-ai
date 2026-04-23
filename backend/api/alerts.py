from fastapi import APIRouter, Query
from ..core import state_store

router = APIRouter()


@router.get("/", summary="List alerts")
def list_alerts(
    limit: int = Query(50, le=500),
    unresolved_only: bool = Query(False),
):
    alerts = state_store.get_alerts(limit=limit, unresolved_only=unresolved_only)
    return [a.model_dump() for a in alerts]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    ok = state_store.resolve_alert(alert_id)
    return {"resolved": ok, "alert_id": alert_id}