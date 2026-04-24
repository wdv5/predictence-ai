from __future__ import annotations

import csv
import logging
import os
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from prophet import Prophet

from ..models.schemas import MetricPayload

logger = logging.getLogger("predictive_monitor")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
METRICS_CSV_PATH = DATA_DIR / "metrics.csv"
N8N_PREDICTIVE_WEBHOOK_URL = os.getenv(
    "N8N_PREDICTIVE_WEBHOOK_URL",
    "http://localhost:5678/webhook/cpu-threshold-forecast",
)


def persist_metric_row(payload: MetricPayload) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    exists = METRICS_CSV_PATH.exists()

    with METRICS_CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "cpu_percent",
                "ram_percent",
                "latency_ms",
                "error_rate",
                "source",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": payload.timestamp.isoformat(),
                "cpu_percent": payload.cpu_percent,
                "ram_percent": payload.ram_percent,
                "latency_ms": payload.latency_ms,
                "error_rate": payload.error_rate,
                "source": payload.source,
            }
        )


def load_prophet_dataset(metric: str = "cpu_percent") -> pd.DataFrame:
    if not METRICS_CSV_PATH.exists():
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.read_csv(METRICS_CSV_PATH)
    if df.empty or metric not in df.columns:
        return pd.DataFrame(columns=["ds", "y"])

    dataset = df[["timestamp", metric]].copy()
    dataset["timestamp"] = pd.to_datetime(dataset["timestamp"], errors="coerce")
    before_drop = len(dataset)
    dataset = dataset.dropna()
    dropped = before_drop - len(dataset)
    if dropped > 0:
        logger.warning(
            "[prophet_dataset] dropped %s rows due to invalid/missing timestamp or metric values",
            dropped,
        )
    dataset = dataset.rename(columns={"timestamp": "ds", metric: "y"})
    dataset = dataset.sort_values("ds").reset_index(drop=True)
    return dataset


def train_cpu_model() -> tuple[Prophet | None, pd.DataFrame]:
    train_df = load_prophet_dataset("cpu_percent")
    if len(train_df) < 10:
        return None, train_df

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=True,
    )
    model.fit(train_df)
    return model, train_df


def predict_cpu_next_24h(threshold: float = 90.0) -> dict:
    model, train_df = train_cpu_model()
    if model is None:
        return {
            "trained": False,
            "reason": "Not enough historical samples. Need at least 10.",
            "history_points": len(train_df),
            "threshold": threshold,
            "predictions": [],
            "threshold_exceeded": False,
        }

    future = model.make_future_dataframe(periods=24, freq="h")
    forecast = model.predict(future)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    next_24 = forecast.tail(24).copy()
    next_24["will_exceed"] = next_24["yhat"] > threshold

    predictions = [
        {
            "timestamp": row.ds.isoformat(),
            "predicted_cpu": float(row.yhat),
            "lower_bound": float(row.yhat_lower),
            "upper_bound": float(row.yhat_upper),
            "will_exceed": bool(row.will_exceed),
        }
        for row in next_24.itertuples(index=False)
    ]

    threshold_exceeded = bool(next_24["will_exceed"].any())
    first_breach = None
    if threshold_exceeded:
        first = next_24[next_24["will_exceed"]].iloc[0]
        first_breach = {
            "timestamp": first["ds"].isoformat(),
            "predicted_cpu": float(first["yhat"]),
            "threshold": threshold,
        }

    return {
        "trained": True,
        "history_points": len(train_df),
        "threshold": threshold,
        "predictions": predictions,
        "threshold_exceeded": threshold_exceeded,
        "first_breach": first_breach,
    }


def trigger_n8n_threshold_webhook(forecast: dict) -> dict:
    payload = {
        "event": "cpu_forecast_threshold_exceeded",
        "triggered_at": datetime.utcnow().isoformat(),
        "forecast": forecast,
    }
    try:
        resp = httpx.post(N8N_PREDICTIVE_WEBHOOK_URL, json=payload, timeout=5.0)
        resp.raise_for_status()
        return {"triggered": True, "status_code": resp.status_code}
    except Exception as exc:
        logger.error(f"[predictive webhook] failed: {exc}")
        return {"triggered": False, "error": str(exc)}
