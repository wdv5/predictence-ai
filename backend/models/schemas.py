from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class MetricPayload(BaseModel):
    cpu_percent: float = Field(..., ge=0, le=100, description="CPU usage %")
    ram_percent: float = Field(..., ge=0, le=100, description="RAM usage %")
    latency_ms: float = Field(..., ge=0, description="Response latency in ms")
    error_rate: float = Field(..., ge=0, le=100, description="HTTP error rate %")
    source: Optional[str] = "manual"
    timestamp: Optional[datetime] = None

    def model_post_init(self, _):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


class Alert(BaseModel):
    id: str
    severity: Literal["WARNING", "CRITICAL"]
    metric: str
    value: float
    threshold: float
    message: str
    timestamp: datetime
    resolved: bool = False


class SystemStatus(BaseModel):
    status: Literal["OK", "WARNING", "CRITICAL"]
    alerts: list[Alert]
    latest_metrics: Optional[MetricPayload]
    timestamp: datetime


class ActionResult(BaseModel):
    action: str
    triggered_by: str
    status: Literal["simulated", "delegated", "failed"]
    message: str
    timestamp: datetime
