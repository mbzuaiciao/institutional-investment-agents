from __future__ import annotations

from typing import cast

import pytest

from institutional_investment_agents.phase2_schemas import HarnessLevel
from institutional_investment_agents.phase3_analysis import analyze_scored_runs
from institutional_investment_agents.phase3_evaluator import (
    counterfactual_consistency,
    premise_resistance_score,
    tool_necessity_score,
)
from institutional_investment_agents.phase3_metrics import (
    calibration_metrics,
    paired_uplift,
    stability_metrics,
)
from institutional_investment_agents.phase3_schemas import (
    ClaimCalibrationRecord,
    Phase3ScoredRun,
    StabilityRecord,
)


def test_stability_metrics_separate_output_variation() -> None:
    runs = (
        StabilityRecord(thesis="avoid", score=80, risk_recall=.8, citation_validity=1, tool_calls=1, route="credit"),
        StabilityRecord(thesis="avoid", score=90, risk_recall=1, citation_validity=.8, tool_calls=1, route="credit"),
        StabilityRecord(thesis="watch", score=70, risk_recall=.6, citation_validity=1, tool_calls=0, route="general"),
    )
    metrics = stability_metrics(runs)
    assert metrics["final_thesis_consistency"] == pytest.approx(2 / 3)
    assert metrics["score_standard_deviation"] > 0
    assert metrics["routing_consistency"] == pytest.approx(2 / 3)


def test_calibration_reports_reliability_ece_and_brier() -> None:
    records = (
        ClaimCalibrationRecord(confidence=.9, correct_or_supported=True),
        ClaimCalibrationRecord(confidence=.8, correct_or_supported=False),
        ClaimCalibrationRecord(confidence=.2, correct_or_supported=False),
    )
    metrics = calibration_metrics(records)
    assert 0 <= cast(float, metrics["expected_calibration_error"]) <= 1
    assert 0 <= cast(float, metrics["brier_score"]) <= 1
    assert metrics["source"] == "self_reported"
    assert metrics["reliability_bins"]


def test_premise_resistance_rewards_correction_not_rationalization() -> None:
    good = premise_resistance_score(
        accepted_false_premise=False,
        corrected_premise=True,
        sought_evidence=True,
        hedged=True,
        unsupported_rationalization=False,
    )
    bad = premise_resistance_score(
        accepted_false_premise=True,
        corrected_premise=False,
        sought_evidence=False,
        hedged=False,
        unsupported_rationalization=True,
    )
    assert good == 100
    assert bad == 0


def test_counterfactual_consistency_requires_directional_response() -> None:
    assert counterfactual_consistency("avoid", "buy", evidence_reversed=True) == 1
    assert counterfactual_consistency("avoid", "avoid", evidence_reversed=True) == 0


def test_tool_necessity_detects_avoidance_and_overuse() -> None:
    correct = tool_necessity_score(
        required=True,
        called=True,
        unnecessary_calls=0,
        internal_arithmetic_when_prohibited=False,
        incorporated_correctly=True,
    )
    avoided = tool_necessity_score(
        required=True,
        called=False,
        unnecessary_calls=1,
        internal_arithmetic_when_prohibited=True,
        incorporated_correctly=False,
    )
    assert correct == 1
    assert avoided == 0


def test_paired_uplift_preserves_episode_pairing() -> None:
    result = paired_uplift((60, 80, 70), (70, 83, 72))
    assert result["mean_uplift"] == 5
    assert result["ci95_half_width"] > 0


def test_phase3_analysis_reports_cells_pairing_and_cost_frontier() -> None:
    runs = tuple(
        Phase3ScoredRun(
            model_id="R0",
            harness=HarnessLevel.H2_STRONG,
            condition=condition,
            episode_id=episode,
            repetition=0,
            research_quality=score,
            control_quality=80,
            risk_recall=.8,
            citation_validity=.9,
            unsupported_claims=0,
            model_calls=9 if condition == "off" else 10,
            total_tokens=900 if condition == "off" else 1000,
            latency_seconds=2,
        )
        for episode, before, after in (("E1", 70, 80), ("E2", 75, 80))
        for condition, score in (("off", before), ("on", after))
    )
    analysis = analyze_scored_runs(runs)
    assert analysis["run_count"] == 4
    assert analysis["paired_condition_effect"]["mean_uplift"] == 7.5
    assert len(analysis["cost_quality_points"]) == 4
