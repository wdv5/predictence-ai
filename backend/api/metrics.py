from fastapi import APIRouter, Query
from ..models.schemas import MetricPayload, SystemStatus
from ..core import rules_engine, state_store, prometheus_sim, action_layer
from ..core import predictive_monitor
from datetime import datetime

router = APIRouter()


@router.post("/ingest", summary="Receive real or Prometheus metrics")
def ingest_metrics(payload: MetricPayload):
    state_store.push_metrics(payload)
    predictive_monitor.persist_metric_row(payload)
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


@router.get("/predict/cpu", summary="Predict CPU usage for the next 24 hours")
def predict_cpu(
    threshold: float = Query(90.0, ge=0, le=100),
    trigger_webhook: bool = Query(True),
<<<<<<< codex/implement-predictive-monitoring-system-with-fastapi-oe340g
    force_webhook: bool = Query(False),
):
    forecast = predictive_monitor.predict_cpu_next_24h(threshold=threshold)
    webhook = None
    should_trigger = bool(forecast.get("threshold_exceeded")) or force_webhook
    if trigger_webhook and should_trigger:
        webhook_payload = {
            **forecast,
            "trigger_reason": "forced_test" if force_webhook and not forecast.get("threshold_exceeded") else "threshold_breach",
            "forced": force_webhook,
        }
        webhook = predictive_monitor.trigger_n8n_threshold_webhook(webhook_payload)
    return {"forecast": forecast, "webhook": webhook, "should_trigger_webhook": should_trigger}
=======
):
    forecast = predictive_monitor.predict_cpu_next_24h(threshold=threshold)
    webhook = None
    if trigger_webhook and forecast.get("threshold_exceeded"):
        webhook = predictive_monitor.trigger_n8n_threshold_webhook(forecast)
    return {"forecast": forecast, "webhook": webhook}
>>>>>>> main


@router.get("/debug/prophet-dataset", summary="Preview Prophet-compatible dataset")
def debug_prophet_dataset(limit: int = Query(50, ge=1, le=500)):
    df = predictive_monitor.load_prophet_dataset(metric="cpu_percent")
    rows = [
        {"ds": row.ds.isoformat(), "y": float(row.y)}
        for row in df.tail(limit).itertuples(index=False)
    ]
    return {
        "csv_path": str(predictive_monitor.METRICS_CSV_PATH),
        "rows_total": len(df),
        "rows_preview": rows,
    }
