from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

SAFE_TRACE_ATTRIBUTES = {
    "route",
    "method",
    "status_code",
    "operation",
    "suite",
    "model_provider",
    "model_variant",
}


@contextmanager
def span(_name: str, **attributes: object) -> Iterator[dict[str, object]]:
    safe_attributes = {
        key: value for key, value in attributes.items() if key in SAFE_TRACE_ATTRIBUTES
    }
    yield safe_attributes
