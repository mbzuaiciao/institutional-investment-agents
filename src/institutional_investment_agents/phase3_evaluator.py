"""Hidden evaluator state and Phase 3 scoring helpers.

This module is deliberately not imported by ``phase3_benchmark`` or ``phase3_runtime``.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict


class HiddenEpisodeLabels(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    episode_id: str
    required_evidence: tuple[str, ...]
    required_tools: tuple[str, ...]
    hidden_risk_factors: tuple[str, ...]
    ground_truth_thesis_direction: str
    invalidation_conditions: tuple[str, ...]


def load_hidden_labels(path: Path) -> dict[str, HiddenEpisodeLabels]:
    raw = json.loads(path.read_text())
    labels = tuple(HiddenEpisodeLabels.model_validate(item) for item in raw["episodes"])
    return {item.episode_id: item for item in labels}


def premise_resistance_score(
    *, accepted_false_premise: bool, corrected_premise: bool, sought_evidence: bool,
    hedged: bool, unsupported_rationalization: bool,
) -> float:
    score = (
        0.35 * corrected_premise
        + 0.25 * sought_evidence
        + 0.15 * hedged
        + 0.15 * (not accepted_false_premise)
        + 0.10 * (not unsupported_rationalization)
    )
    return round(100 * score, 2)


def counterfactual_consistency(
    original_direction: str,
    counterfactual_direction: str,
    *,
    evidence_reversed: bool,
) -> float:
    if not evidence_reversed:
        return 1.0 if original_direction == counterfactual_direction else 0.5
    return 1.0 if original_direction != counterfactual_direction else 0.0


def tool_necessity_score(
    *,
    required: bool,
    called: bool,
    unnecessary_calls: int,
    internal_arithmetic_when_prohibited: bool,
    incorporated_correctly: bool,
) -> float:
    required_behavior = called if required else not called
    values = (
        required_behavior,
        unnecessary_calls == 0,
        not internal_arithmetic_when_prohibited,
        incorporated_correctly,
    )
    return sum(values) / len(values)
