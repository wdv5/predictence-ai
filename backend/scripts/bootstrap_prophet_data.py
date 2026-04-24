from __future__ import annotations

import argparse
import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_row(ts: datetime, idx: int, spike_every: int) -> dict:
    hour = ts.hour

    # Base daily wave + tiny trend + noise
    baseline = 52 + 18 * math.sin((2 * math.pi * hour) / 24)
    trend = (idx / 500.0) * 6.0
    noise = random.uniform(-5.5, 5.5)
    cpu = baseline + trend + noise

    # Optional synthetic spike to teach threshold scenarios
    if spike_every > 0 and idx % spike_every == 0:
        cpu += random.uniform(18, 30)

    cpu = max(1.0, min(cpu, 99.0))
    ram = max(15.0, min(95.0, cpu * 0.72 + random.uniform(10, 20)))
    latency = max(15.0, 90 + cpu * 5.0 + random.uniform(-30, 80))
    error_rate = max(0.0, min(25.0, (cpu - 70.0) * 0.15 + random.uniform(0, 2.2)))

    return {
        "timestamp": ts.isoformat(),
        "cpu_percent": round(cpu, 3),
        "ram_percent": round(ram, 3),
        "latency_ms": round(latency, 3),
        "error_rate": round(error_rate, 3),
        "source": "bootstrap",
    }


def bootstrap_csv(
    out_csv: Path,
    points: int,
    interval_minutes: int,
    spike_every: int,
    seed: int,
    append: bool,
) -> dict:
    random.seed(seed)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    file_exists = out_csv.exists()
    mode = "a" if append else "w"
    start = datetime.utcnow() - timedelta(minutes=points * interval_minutes)

    rows = []
    for i in range(points):
        ts = start + timedelta(minutes=i * interval_minutes)
        rows.append(generate_row(ts, i, spike_every))

    with out_csv.open(mode, newline="", encoding="utf-8") as f:
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
        if (not file_exists) or (not append):
            writer.writeheader()
        writer.writerows(rows)

    return {
        "csv_path": str(out_csv),
        "rows_written": len(rows),
        "append_mode": append,
        "from_utc": rows[0]["timestamp"] if rows else None,
        "to_utc": rows[-1]["timestamp"] if rows else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap synthetic metrics history for Prophet training.",
    )
    parser.add_argument(
        "--out",
        default="backend/data/metrics.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--points",
        type=int,
        default=240,
        help="How many metric points to generate.",
    )
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=60,
        help="Minutes between generated points.",
    )
    parser.add_argument(
        "--spike-every",
        type=int,
        default=18,
        help="Inject a CPU spike every N points. Use 0 to disable.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible synthetic data.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append instead of overwrite.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = bootstrap_csv(
        out_csv=Path(args.out),
        points=args.points,
        interval_minutes=args.interval_minutes,
        spike_every=args.spike_every,
        seed=args.seed,
        append=args.append,
    )
    print(result)


if __name__ == "__main__":
    main()
