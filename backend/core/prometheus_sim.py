"""
Prometheus Simulator — generates realistic metric samples.
Replace `generate()` with actual Prometheus scrape in production:
  - pip install prometheus-client
  - scrape /metrics endpoint or use prometheus_api_client
"""
import random
import math
from datetime import datetime
from models.schemas import MetricPayload


_tick = 0  # global step counter for waveform simulation


def generate(scenario: str = "normal") -> MetricPayload:
    """
    Generate a simulated MetricPayload.

    Scenarios:
      normal    — healthy baseline with light noise
      cpu_spike — sustained high CPU
      latency   — degraded latency + some errors
      cascade   — all metrics bad (CRITICAL)
      random    — random scenario each call
    """
    global _tick
    _tick += 1

    if scenario == "random":
        scenario = random.choice(["normal", "normal", "cpu_spike", "latency", "cascade"])

    t = _tick * 0.1

    if scenario == "normal":
        return MetricPayload(
            cpu_percent=40 + 15 * math.sin(t) + random.gauss(0, 3),
            ram_percent=55 + 5 * math.sin(t * 0.5) + random.gauss(0, 2),
            latency_ms=120 + 40 * abs(math.sin(t * 0.7)) + random.gauss(0, 15),
            error_rate=0.5 + random.uniform(0, 1.5),
            source="prometheus_sim",
            timestamp=datetime.utcnow(),
        )

    if scenario == "cpu_spike":
        return MetricPayload(
            cpu_percent=min(98, 82 + random.gauss(0, 5)),
            ram_percent=70 + random.gauss(0, 3),
            latency_ms=350 + random.gauss(0, 50),
            error_rate=2 + random.uniform(0, 2),
            source="prometheus_sim",
            timestamp=datetime.utcnow(),
        )

    if scenario == "latency":
        return MetricPayload(
            cpu_percent=55 + random.gauss(0, 5),
            ram_percent=60 + random.gauss(0, 3),
            latency_ms=600 + random.gauss(0, 100),
            error_rate=6 + random.uniform(0, 4),
            source="prometheus_sim",
            timestamp=datetime.utcnow(),
        )

    if scenario == "cascade":
        return MetricPayload(
            cpu_percent=min(99, 91 + random.gauss(0, 3)),
            ram_percent=min(99, 93 + random.gauss(0, 2)),
            latency_ms=1100 + random.gauss(0, 150),
            error_rate=min(30, 12 + random.uniform(0, 5)),
            source="prometheus_sim",
            timestamp=datetime.utcnow(),
        )

    return generate("normal")
