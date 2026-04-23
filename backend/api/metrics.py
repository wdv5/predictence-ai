from fastapi import APIRouter, Query
from ..models.schemas import MetricPayload, SystemStatus
from ..core import rules_engine, state_store, prometheus_sim, action_layer
from datetime import datetime

router = APIRouter()


@router.post("/ingest", summary="Receive real or Prometheus metrics")
def ingest_metrics(payload: MetricPayload):
    """
    Main ingestion endpoint.
    1. Store metric
    2. Evaluate rules
    3. Log + execute recommended actions
    """
    state_store.push_metrics(payload)
    alerts = rules_engine.evaluate(payload)
    state_store.push_alerts(alerts)

    actions_taken = []
    if alerts:
        for action in rules_engine.recommend_action(alerts):
            result = action_layer.execute(action, triggered_by=str([a.metric for a in alerts]))
            actions_taken.append(result.model_dump())

    return {
        "received": payload.model_dump(),
        "alerts_triggered": len(alerts),
        "alerts": [a.model_dump() for a in alerts],
        "actions": actions_taken,
    }


@router.get("/simulate", summary="Generate and ingest a simulated metric sample")
def simulate_metric(scenario: str = Query("random", enum=["normal", "cpu_spike", "latency", "cascade", "random"])):
    """Simulate a Prometheus scrape for testing."""
    payload = prometheus_sim.generate(scenario)
    return ingest_metrics(payload)


@router.get("/history", summary="Get recent metric history")
def get_history(limit: int = Query(60, le=200)):
    history = state_store.get_metrics_history(limit)
    return [m.model_dump() for m in history]


@router.get("/status", response_model=SystemStatus)
def get_status():
    alerts = state_store.get_alerts(limit=20, unresolved_only=True)
    return SystemStatus(
        status=rules_engine.compute_status(alerts),
        alerts=alerts,
        latest_metrics=state_store.get_latest_metrics(),
        timestamp=datetime.utcnow(),
    )
