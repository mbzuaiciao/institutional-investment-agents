"""Repeated-run stability, calibration, and paired Phase 3 analysis metrics."""

from __future__ import annotations

import math
from collections import Counter
from statistics import fmean, pstdev

from institutional_investment_agents.phase3_schemas import (
    ClaimCalibrationRecord,
    StabilityRecord,
)


def stability_metrics(records: tuple[StabilityRecord, ...]) -> dict[str, float]:
    if not records:
        raise ValueError("at least one repeated run is required")
    thesis_counts = Counter(item.thesis for item in records)
    route_counts = Counter(item.route for item in records)
    count = len(records)
    return {
        "final_thesis_consistency": max(thesis_counts.values()) / count,
        "score_standard_deviation": pstdev(item.score for item in records),
        "risk_recall_standard_deviation": pstdev(item.risk_recall for item in records),
        "citation_standard_deviation": pstdev(item.citation_validity for item in records),
        "tool_use_standard_deviation": pstdev(item.tool_calls for item in records),
        "routing_consistency": max(route_counts.values()) / count,
    }


def calibration_metrics(
    records: tuple[ClaimCalibrationRecord, ...], *, bins: int = 5
) -> dict[str, object]:
    if not records:
        raise ValueError("at least one confidence observation is required")
    if bins < 1:
        raise ValueError("bins must be positive")
    reliability: list[dict[str, float | int]] = []
    expected_calibration_error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = tuple(
            item
            for item in records
            if lower <= item.confidence <= upper
            and (index == bins - 1 or item.confidence < upper)
        )
        if not selected:
            continue
        mean_confidence = fmean(item.confidence for item in selected)
        empirical_accuracy = fmean(float(item.correct_or_supported) for item in selected)
        expected_calibration_error += (
            len(selected) / len(records) * abs(mean_confidence - empirical_accuracy)
        )
        reliability.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(selected),
                "mean_confidence": mean_confidence,
                "empirical_accuracy": empirical_accuracy,
            }
        )
    brier = fmean(
        (item.confidence - float(item.correct_or_supported)) ** 2 for item in records
    )
    return {
        "source": records[0].source,
        "expected_calibration_error": expected_calibration_error,
        "brier_score": brier,
        "reliability_bins": reliability,
    }


def paired_uplift(control: tuple[float, ...], treatment: tuple[float, ...]) -> dict[str, float]:
    if not control or len(control) != len(treatment):
        raise ValueError("paired samples must have the same non-zero length")
    differences = tuple(after - before for before, after in zip(control, treatment, strict=True))
    mean = fmean(differences)
    standard_error = pstdev(differences) / math.sqrt(len(differences))
    return {"mean_uplift": mean, "ci95_half_width": 1.96 * standard_error}
