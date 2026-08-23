from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReportSummary:
    total_requests: int
    failures: int
    median_ms: float | None
    p95_ms: float | None
    p99_ms: float | None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round((self.total_requests - self.failures) / self.total_requests, 4)


def summarize_locust_csv(stats_csv: Path) -> ReportSummary:
    if not stats_csv.exists():
        return ReportSummary(0, 0, None, None, None)
    with stats_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    aggregate = next((row for row in rows if row.get("Name") == "Aggregated"), None)
    if not aggregate:
        return ReportSummary(0, 0, None, None, None)
    return ReportSummary(
        total_requests=int(float(aggregate.get("Request Count") or 0)),
        failures=int(float(aggregate.get("Failure Count") or 0)),
        median_ms=_float_or_none(aggregate.get("Median Response Time")),
        p95_ms=_float_or_none(aggregate.get("95%")),
        p99_ms=_float_or_none(aggregate.get("99%")),
    )


def _float_or_none(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    return float(value)


def write_summary(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
