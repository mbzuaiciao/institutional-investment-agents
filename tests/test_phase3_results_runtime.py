from __future__ import annotations

import json
from pathlib import Path

import pytest

from institutional_investment_agents.phase2_schemas import HarnessLevel
from institutional_investment_agents.phase3_analysis import summarize_real_runs
from institutional_investment_agents.phase3_benchmark import load_observable_episodes
from institutional_investment_agents.phase3_longitudinal import observable_longitudinal_sequence
from institutional_investment_agents.phase3_runtime import HARNESS_OPERATIONS, prepare_calls
from institutional_investment_agents.phase3_schemas import RealModelConfig, ResultStatus
from institutional_investment_agents.phase3_studies import get_study

ROOT = Path(__file__).resolve().parents[1]


def test_harness_semantics_have_stable_call_budgets() -> None:
    assert len(HARNESS_OPERATIONS[HarnessLevel.H0_MINIMAL]) == 3
    assert len(HARNESS_OPERATIONS[HarnessLevel.H1_STRUCTURED]) == 7
    assert len(HARNESS_OPERATIONS[HarnessLevel.H2_STRONG]) == 10


def test_prepared_calls_include_prompt_and_input_identity() -> None:
    episode = load_observable_episodes(ROOT / "configs/phase3_benchmark.yaml")[0]
    model = RealModelConfig(identifier="R0", model="fixture")
    calls = prepare_calls(
        model=model,
        harness=HarnessLevel.H2_STRONG,
        episode=episode,
        repetition=1,
    )
    assert len(calls) == 10
    assert len({item.spec.input_hash for item in calls}) == 10
    assert all(item.spec.prompt_version == "1.0.0" for item in calls)


def test_unrun_summary_cannot_contain_fake_records() -> None:
    assert summarize_real_runs((), ResultStatus.NOT_YET_RUN)["run_count"] == 0
    with pytest.raises(ValueError, match="cannot contain"):
        summarize_real_runs(({"score": 100},), ResultStatus.NOT_YET_RUN)


def test_checked_in_phase3_artifacts_are_unambiguously_unrun() -> None:
    manifest = json.loads((ROOT / "results/phase3/manifest.json").read_text())
    failures = json.loads((ROOT / "results/phase3/failures.json").read_text())
    assert manifest["result_status"] == ResultStatus.NOT_YET_RUN
    assert manifest["real_model_calls"] == 0
    assert failures["observed_failures"] == []
    assert "NOT YET RUN" in (ROOT / "results/phase3/report.md").read_text()


def test_focused_studies_hold_base_harness_and_budget_mechanisms_explicit() -> None:
    critic = get_study("critic")
    assert {item.base_harness for item in critic.conditions} == {HarnessLevel.H2_STRONG}
    assert len(critic.conditions[1].operations) > len(critic.conditions[0].operations)
    specialization = get_study("specialization")
    assert len(specialization.conditions[0].operations) == len(
        specialization.conditions[1].operations
    )
    assert specialization.conditions[1].context_mode == "partitioned"


def test_real_longitudinal_protocol_has_five_blind_updates() -> None:
    sequence = observable_longitudinal_sequence()
    assert len(sequence) == 5
    assert [item.family for item in sequence] == [
        f"longitudinal_update_{index}" for index in range(1, 6)
    ]
    assert all("expected_direction" not in item.model_dump() for item in sequence)
    memory = get_study("longitudinal")
    assert not memory.conditions[0].persistent_state
    assert memory.conditions[1].persistent_state
