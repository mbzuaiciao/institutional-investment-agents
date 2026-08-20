from __future__ import annotations

from pathlib import Path

import pytest

from institutional_investment_agents.phase2_schemas import HarnessLevel
from institutional_investment_agents.phase3_benchmark import load_observable_episodes
from institutional_investment_agents.phase3_config import build_plan, load_models, load_presets
from institutional_investment_agents.phase3_runner import run_cli
from institutional_investment_agents.phase3_schemas import ResourceLimits

ROOT = Path(__file__).resolve().parents[1]


def _inputs():
    models = load_models(ROOT / "configs/phase3_models.example.yaml", ("R0", "R1", "R2"))
    preset = load_presets(ROOT / "configs/phase3_protocol.yaml")["smoke"]
    return models, preset


def test_smoke_plan_reports_bounded_cells_calls_and_tokens() -> None:
    models, preset = _inputs()
    plan = build_plan(
        preset=preset,
        study="factorial",
        models=models,
        harnesses=tuple(HarnessLevel),
        limits=ResourceLimits(max_model_calls=500, max_total_tokens=500_000),
    )
    assert plan.planned_cells == 9
    assert plan.planned_episode_runs == 18
    assert plan.approximate_model_calls == 120
    assert plan.max_calls_per_episode == 10
    assert plan.estimated_upper_cost is None


def test_call_limit_aborts_before_execution() -> None:
    models, preset = _inputs()
    with pytest.raises(ValueError, match="max_model_calls"):
        build_plan(
            preset=preset,
            study="factorial",
            models=models,
            harnesses=tuple(HarnessLevel),
            limits=ResourceLimits(max_model_calls=10),
        )


def test_cost_limit_requires_user_pricing_metadata() -> None:
    models, preset = _inputs()
    with pytest.raises(ValueError, match="pricing_required"):
        build_plan(
            preset=preset,
            study="factorial",
            models=models,
            harnesses=tuple(HarnessLevel),
            limits=ResourceLimits(max_estimated_cost=5),
        )


def test_benchmark_has_fifteen_families_and_no_hidden_labels() -> None:
    episodes = load_observable_episodes(ROOT / "configs/phase3_benchmark.yaml")
    assert len(episodes) == 15
    assert len({item.family for item in episodes}) == 15
    assert "ground_truth_thesis_direction" not in episodes[0].model_dump()


def test_capstone_dry_run_makes_no_api_calls(capsys: pytest.CaptureFixture[str]) -> None:
    assert run_cli("capstone", ["--preset", "smoke", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "Approximate model calls" in output
    assert "NOT YET RUN" in output
    assert "no provider request was sent" in output


def test_live_execution_requires_explicit_environment_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PHASE3_ENABLE_LIVE_RUNS", raising=False)
    with pytest.raises(RuntimeError, match="PHASE3_ENABLE_LIVE_RUNS"):
        run_cli("capstone", ["--preset", "smoke", "--execute"])
