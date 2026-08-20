"""Analysis helpers that preserve real-model result status and paired design."""

from __future__ import annotations

from collections import defaultdict
from statistics import fmean
from typing import Any

from institutional_investment_agents.phase3_metrics import paired_uplift
from institutional_investment_agents.phase3_schemas import (
    Phase3ScoredRun,
    ResultStatus,
)


def summarize_real_runs(runs: tuple[dict[str, Any], ...], status: ResultStatus) -> dict[str, Any]:
    if status == ResultStatus.NOT_YET_RUN:
        if runs:
            raise ValueError("NOT YET RUN summaries cannot contain run records")
        return {"result_status": status.value, "run_count": 0, "cells": []}
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for run in runs:
        grouped[(str(run["model_id"]), str(run["harness"]))].append(float(run["score"]))
    cells = [
        {"model_id": key[0], "harness": key[1], "mean_score": fmean(values), "n": len(values)}
        for key, values in sorted(grouped.items())
    ]
    return {"result_status": status.value, "run_count": len(runs), "cells": cells}


def compare_paired_conditions(
    control: tuple[float, ...], treatment: tuple[float, ...]
) -> dict[str, float]:
    return paired_uplift(control, treatment)


def analyze_scored_runs(runs: tuple[Phase3ScoredRun, ...]) -> dict[str, Any]:
    """Summarize cells, marginal means, paired condition effects, and cost/quality points."""
    if not runs:
        raise ValueError("real-model analysis requires scored run records")
    cell_values: dict[tuple[str, str], list[float]] = defaultdict(list)
    model_values: dict[str, list[float]] = defaultdict(list)
    harness_values: dict[str, list[float]] = defaultdict(list)
    condition_pairs: dict[tuple[str, str, int], dict[str, float]] = defaultdict(dict)
    for run in runs:
        cell_values[(run.model_id, run.harness.value)].append(run.research_quality)
        model_values[run.model_id].append(run.research_quality)
        harness_values[run.harness.value].append(run.research_quality)
        pair_key = (run.model_id, run.episode_id, run.repetition)
        condition_pairs[pair_key][run.condition] = run.research_quality
    conditions = sorted({run.condition for run in runs})
    paired_effect: dict[str, float] | None = None
    if len(conditions) == 2:
        complete = tuple(
            values for values in condition_pairs.values() if all(name in values for name in conditions)
        )
        if complete:
            paired_effect = paired_uplift(
                tuple(values[conditions[0]] for values in complete),
                tuple(values[conditions[1]] for values in complete),
            )
    cost_quality = [
        {
            "model_id": run.model_id,
            "harness": run.harness.value,
            "condition": run.condition,
            "research_quality": run.research_quality,
            "model_calls": run.model_calls,
            "total_tokens": run.total_tokens,
            "latency_seconds": run.latency_seconds,
            "monetary_cost": run.monetary_cost,
        }
        for run in sorted(runs, key=lambda item: (item.total_tokens, -item.research_quality))
    ]
    return {
        "run_count": len(runs),
        "model_means": {key: fmean(value) for key, value in sorted(model_values.items())},
        "harness_means": {key: fmean(value) for key, value in sorted(harness_values.items())},
        "cells": [
            {
                "model_id": key[0],
                "harness": key[1],
                "mean_research_quality": fmean(value),
                "n": len(value),
            }
            for key, value in sorted(cell_values.items())
        ],
        "paired_condition_order": conditions,
        "paired_condition_effect": paired_effect,
        "cost_quality_points": cost_quality,
        "interpretation": (
            "Descriptive paired analysis; model, harness, provider, prompt, repetition, and episode "
            "effects must not be conflated."
        ),
    }
