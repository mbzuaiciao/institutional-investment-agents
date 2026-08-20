"""Configuration, benchmark freezing, and cost guardrails for Phase 3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from institutional_investment_agents.phase2_schemas import HarnessLevel
from institutional_investment_agents.phase3_schemas import (
    ExperimentPlan,
    ExperimentPreset,
    RealModelConfig,
    ResourceLimits,
)

HARNESS_CALL_BUDGETS = {
    HarnessLevel.H0_MINIMAL: 3,
    HarnessLevel.H1_STRUCTURED: 7,
    HarnessLevel.H2_STRONG: 10,
}
ESTIMATED_INPUT_TOKENS_PER_CALL = 1200


def load_json_yaml(path: Path) -> dict[str, Any]:
    """Load JSON-compatible YAML without adding a runtime YAML dependency."""
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"configuration must be an object: {path}")
    return value


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_presets(path: Path) -> dict[str, ExperimentPreset]:
    raw = load_json_yaml(path)["presets"]
    if not isinstance(raw, dict):
        raise TypeError("presets must be an object")
    return {
        str(name): ExperimentPreset(name=str(name), **value)
        for name, value in raw.items()
        if isinstance(value, dict)
    }


def load_models(path: Path, selected: tuple[str, ...]) -> tuple[RealModelConfig, ...]:
    raw_models = load_json_yaml(path)["models"]
    if not isinstance(raw_models, list):
        raise TypeError("models must be a list")
    models = tuple(RealModelConfig.model_validate(item) for item in raw_models)
    by_id = {model.identifier: model for model in models}
    missing = set(selected) - set(by_id)
    if missing:
        raise KeyError(f"unknown model identifiers: {sorted(missing)}")
    return tuple(by_id[name] for name in selected)


def build_plan(
    *,
    preset: ExperimentPreset,
    study: str,
    models: tuple[RealModelConfig, ...],
    harnesses: tuple[HarnessLevel, ...],
    limits: ResourceLimits,
    conditions: tuple[str, ...] | None = None,
    calls_per_condition: tuple[int, ...] | None = None,
) -> ExperimentPlan:
    condition_names = conditions or tuple(item.value for item in harnesses)
    call_budgets = calls_per_condition or tuple(
        HARNESS_CALL_BUDGETS[harness] for harness in harnesses
    )
    if len(condition_names) != len(harnesses) or len(call_budgets) != len(harnesses):
        raise ValueError("conditions, harnesses, and call budgets must align")
    per_repetition_calls = sum(call_budgets)
    episode_runs = len(models) * len(harnesses) * len(preset.families) * preset.repetitions
    calls = len(models) * len(preset.families) * preset.repetitions * per_repetition_calls
    max_output = max(model.max_output_tokens for model in models)
    token_upper_bound = calls * (ESTIMATED_INPUT_TOKENS_PER_CALL + max_output)
    costs: list[float] = []
    for model in models:
        if model.pricing is None:
            costs = []
            break
        model_calls = len(preset.families) * preset.repetitions * per_repetition_calls
        costs.append(
            model_calls
            * (
                ESTIMATED_INPUT_TOKENS_PER_CALL * model.pricing.input_per_million
                + max_output * model.pricing.output_per_million
            )
            / 1_000_000
        )
    estimated_cost = round(sum(costs), 6) if costs else None
    plan = ExperimentPlan(
        preset=preset.name,
        study=study,
        model_ids=tuple(model.identifier for model in models),
        harnesses=harnesses,
        conditions=condition_names,
        families=preset.families,
        repetitions=preset.repetitions,
        planned_cells=len(models) * len(harnesses),
        planned_episode_runs=episode_runs,
        approximate_model_calls=calls,
        approximate_total_tokens=token_upper_bound,
        max_calls_per_episode=max(call_budgets),
        configured_cost_limit=limits.max_estimated_cost,
        estimated_upper_cost=estimated_cost,
    )
    enforce_limits(plan, limits)
    return plan


def enforce_limits(plan: ExperimentPlan, limits: ResourceLimits) -> None:
    failures: list[str] = []
    if plan.approximate_model_calls > limits.max_model_calls:
        failures.append("max_model_calls")
    if plan.max_calls_per_episode > limits.max_calls_per_episode:
        failures.append("max_calls_per_episode")
    if plan.approximate_total_tokens > limits.max_total_tokens:
        failures.append("max_total_tokens")
    if limits.max_estimated_cost is not None:
        if plan.estimated_upper_cost is None:
            failures.append("pricing_required_for_max_estimated_cost")
        elif plan.estimated_upper_cost > limits.max_estimated_cost:
            failures.append("max_estimated_cost")
    if failures:
        raise ValueError(f"planned experiment exceeds hard limits: {', '.join(failures)}")


def format_plan(plan: ExperimentPlan) -> str:
    cost = "unknown (no pricing metadata)" if plan.estimated_upper_cost is None else str(
        plan.estimated_upper_cost
    )
    return "\n".join(
        (
            f"Phase 3 study: {plan.study}",
            f"Preset: {plan.preset}",
            f"Models: {', '.join(plan.model_ids)}",
            f"Harnesses: {', '.join(item.value for item in plan.harnesses)}",
            f"Conditions: {', '.join(plan.conditions)}",
            f"Planned cells: {plan.planned_cells}",
            f"Episode runs: {plan.planned_episode_runs}",
            f"Approximate model calls (upper bound): {plan.approximate_model_calls}",
            f"Approximate total tokens (planning bound): {plan.approximate_total_tokens}",
            f"Estimated monetary cost upper bound: {cost}",
            f"Configured monetary limit: {plan.configured_cost_limit}",
        )
    )
