from __future__ import annotations

from typing import Any

STATUSES = {
    "created",
    "training",
    "trained_unverified",
    "evaluation_failed",
    "awaiting_manual_review",
    "rejected",
    "promoted",
}


def promotion_decision(
    *,
    dataset_valid: bool,
    adapter_valid: bool,
    leakage_detected: bool,
    base_metrics: dict[str, float],
    adapter_metrics: dict[str, float],
    manual_review_completed: bool,
    manifest_exists: bool,
    tolerance: float = 0.02,
) -> dict[str, Any]:
    reasons: list[str] = []
    if not dataset_valid:
        reasons.append("dataset_validation_failed")
    if not adapter_valid:
        reasons.append("adapter_validation_failed")
    if leakage_detected:
        reasons.append("split_leakage_detected")
    if not manifest_exists:
        reasons.append("missing_manifest")
    if not manual_review_completed:
        reasons.append("awaiting_manual_review")
    for metric in ("citation_valid_rate", "refusal_rate"):
        if adapter_metrics.get(metric, 0.0) + tolerance < base_metrics.get(metric, 0.0):
            reasons.append(f"{metric}_regressed")
    if adapter_metrics.get("forbidden_claim_rate", 0.0) > base_metrics.get(
        "forbidden_claim_rate", 0.0
    ):
        reasons.append("forbidden_claim_rate_increased")
    if reasons == ["awaiting_manual_review"]:
        status = "awaiting_manual_review"
    elif reasons:
        status = "rejected"
    else:
        status = "promoted"
    return {"status": status, "reasons": reasons}
