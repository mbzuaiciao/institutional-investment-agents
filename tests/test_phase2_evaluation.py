from pathlib import Path

from institutional_investment_agents.phase2_evaluation import (
    run_factorial,
    run_memory_study,
    run_phase2_capstone,
    run_specialization_study,
    write_phase2_csv,
    write_phase2_json,
    write_phase2_markdown,
)
from institutional_investment_agents.phase2_schemas import HardEpisodeFamily


def test_factorial_count_aggregation_and_interaction() -> None:
    result = run_factorial(seeds=(11,), families=(HardEpisodeFamily.TOOL_NECESSITY,))
    assert result["run_count"] == 9
    assert len(result["cell_summary"]) == 9
    attribution = result["attribution"]["research_quality_score"]
    assert set(attribution["variance_share"]) == {"model", "harness", "interaction", "residual"}
    assert abs(sum(attribution["variance_share"].values()) - 1.0) < 0.001


def test_factorial_reproducibility() -> None:
    kwargs = {"seeds": (5,), "families": (HardEpisodeFamily.STALE_EVIDENCE,)}
    assert run_factorial(**kwargs) == run_factorial(**kwargs)


def test_specialization_study_holds_model_call_budget() -> None:
    result = run_specialization_study(seeds=(11,))
    summary = result["summary"]
    for model in ("weak", "medium", "strong"):
        assert (
            summary[f"{model}|False"]["model_calls_mean"]
            == summary[f"{model}|True"]["model_calls_mean"]
        )


def test_memory_study_tracks_stateless_and_persistent() -> None:
    result = run_memory_study(seeds=(11,))
    assert result["run_count"] == 6
    for model in ("weak", "medium", "strong"):
        stateless = result["summary"][f"{model}|False"]
        persistent = result["summary"][f"{model}|True"]
        assert (
            persistent["redundant_research_operations"] < stateless["redundant_research_operations"]
        )


def test_phase2_capstone_smoke_and_writers(tmp_path: Path) -> None:
    result = run_phase2_capstone(seeds=(11,))
    assert result["primary_run_count"] == 81
    assert result["total_run_count"] > result["primary_run_count"]
    json_path = tmp_path / "phase2.json"
    markdown_path = tmp_path / "phase2.md"
    csv_path = tmp_path / "phase2.csv"
    write_phase2_json(result, json_path)
    write_phase2_markdown(result, markdown_path)
    write_phase2_csv(result, csv_path)
    assert json_path.read_text().endswith("\n")
    assert "model × harness" in markdown_path.read_text()
    assert csv_path.read_text().startswith("model_profile,harness_profile")
