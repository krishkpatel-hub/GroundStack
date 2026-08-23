from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager

ALLOWED_LABELS = {"category", "method", "operation", "result", "route", "status", "suite"}


def _labels(labels: dict[str, str]) -> tuple[tuple[str, str], ...]:
    unsafe = set(labels) - ALLOWED_LABELS
    if unsafe:
        raise ValueError(f"Unsupported metric label(s): {', '.join(sorted(unsafe))}")
    return tuple(sorted((key, value[:80]) for key, value in labels.items()))


class MetricsRegistry:
    def __init__(self) -> None:
        self.counters: defaultdict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(
            float
        )
        self.histograms: defaultdict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = (
            defaultdict(list)
        )
        self.gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

    def increment(self, name: str, value: float = 1.0, **labels: str) -> None:
        self.counters[(name, _labels(labels))] += value

    def observe(self, name: str, value: float, **labels: str) -> None:
        self.histograms[(name, _labels(labels))].append(value)

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        self.gauges[(name, _labels(labels))] = value

    @contextmanager
    def timer(self, name: str, **labels: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.observe(name, time.perf_counter() - start, **labels)

    def render_prometheus(self) -> str:
        lines: list[str] = []
        for (name, labels), value in sorted(self.counters.items()):
            lines.append(f"{name}{_format_labels(labels)} {value:g}")
        for (name, labels), values in sorted(self.histograms.items()):
            if not values:
                continue
            count = len(values)
            total = sum(values)
            lines.append(f"{name}_count{_format_labels(labels)} {count}")
            lines.append(f"{name}_sum{_format_labels(labels)} {total:.6f}")
            lines.append(f"{name}_max{_format_labels(labels)} {max(values):.6f}")
        for (name, labels), value in sorted(self.gauges.items()):
            lines.append(f"{name}{_format_labels(labels)} {value:g}")
        return "\n".join(lines) + "\n"


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    rendered = ",".join(f'{key}="{value}"' for key, value in labels)
    return "{" + rendered + "}"


metrics = MetricsRegistry()
