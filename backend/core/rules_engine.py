"""
Rules Engine — evaluates metrics and emits alerts + recommended actions.

Designed to be replaced by ML in Phase 2:
  - replace `evaluate()` with a model inference call
  - keep same Alert/ActionRecommendation return types
"""
import uuid
from datetime import datetime
from typing import NamedTuple
from ..models.schemas import Alert, MetricPayload


class Rule(NamedTuple):
    metric: str
    threshold: float
    operator: str  # "gt" | "lt"
    severity: str  # "WARNING" | "CRITICAL"
    message_template: str
    recommended_action: str


# ─── Rule Definitions ────────────────────────────────────────────────────────
RULES: list[Rule] = [
    Rule("cpu_percent",  80,  "gt", "WARNING",  "CPU {val:.1f}% > 80%",  "scale_up"),
    Rule("cpu_percent",  90,  "gt", "CRITICAL", "CPU {val:.1f}% > 90%",  "scale_up"),
    Rule("ram_percent",  85,  "gt", "WARNING",  "RAM {val:.1f}% > 85%",  "clear_cache"),
    Rule("ram_percent",  95,  "gt", "CRITICAL", "RAM {val:.1f}% > 95%",  "restart_service"),
    Rule("latency_ms",  500,  "gt", "WARNING",  "Latency {val:.0f}ms > 500ms", "clear_cache"),
    Rule("latency_ms", 1000,  "gt", "CRITICAL", "Latency {val:.0f}ms > 1000ms","scale_up"),
    Rule("error_rate",    5,  "gt", "WARNING",  "Error rate {val:.1f}% > 5%",  "alert_team"),
    Rule("error_rate",   10,  "gt", "CRITICAL", "Error rate {val:.1f}% > 10%", "alert_team"),
]

ACTION_PRIORITY = {"CRITICAL": 2, "WARNING": 1}


def _matches(rule: Rule, value: float) -> bool:
    if rule.operator == "gt":
        return value > rule.threshold
    if rule.operator == "lt":
        return value < rule.threshold
    return False


def evaluate(metrics: MetricPayload) -> list[Alert]:
    """
    Evaluate all rules against incoming metrics.
    Returns list of triggered alerts (deduplicated: only worst severity per metric).
    """
    triggered: dict[str, Alert] = {}

    for rule in RULES:
        value = getattr(metrics, rule.metric)
        if not _matches(rule, value):
            continue

        # Keep only worst severity per metric
        existing = triggered.get(rule.metric)
        if existing and ACTION_PRIORITY[existing.severity] >= ACTION_PRIORITY[rule.severity]:
            continue

        alert = Alert(
            id=str(uuid.uuid4()),
            severity=rule.severity,
            metric=rule.metric,
            value=value,
            threshold=rule.threshold,
            message=rule.message_template.format(val=value),
            timestamp=metrics.timestamp or datetime.utcnow(),
        )
        triggered[rule.metric] = alert

    return list(triggered.values())


def recommend_action(alerts: list[Alert]) -> list[str]:
    """Map alerts → recommended actions (deduped)."""
    actions = set()
    for alert in alerts:
        for rule in RULES:
            if rule.metric == alert.metric and rule.severity == alert.severity:
                actions.add(rule.recommended_action)
    return list(actions)


def compute_status(alerts: list[Alert]) -> str:
    if not alerts:
        return "OK"
    if any(a.severity == "CRITICAL" for a in alerts):
        return "CRITICAL"
    return "WARNING"
