"""
State Store — in-memory ring buffer for metrics + alert history.
Replace with Redis or TimescaleDB when scaling.
"""
from collections import deque
from typing import Optional
from ..models.schemas import Alert, MetricPayload

MAX_METRICS = 200
MAX_ALERTS = 500

_metrics_history: deque[MetricPayload] = deque(maxlen=MAX_METRICS)
_alerts_history: deque[Alert] = deque(maxlen=MAX_ALERTS)
_latest_metrics: Optional[MetricPayload] = None


def push_metrics(m: MetricPayload):
    global _latest_metrics
    _metrics_history.append(m)
    _latest_metrics = m


def push_alerts(alerts: list[Alert]):
    _alerts_history.extend(alerts)


def get_latest_metrics() -> Optional[MetricPayload]:
    return _latest_metrics


def get_metrics_history(limit: int = 60) -> list[MetricPayload]:
    return list(_metrics_history)[-limit:]


def get_alerts(limit: int = 50, unresolved_only: bool = False) -> list[Alert]:
    alerts = list(_alerts_history)
    if unresolved_only:
        alerts = [a for a in alerts if not a.resolved]
    return alerts[-limit:]


def resolve_alert(alert_id: str) -> bool:
    for alert in _alerts_history:
        if alert.id == alert_id:
            alert.resolved = True
            return True
    return False
