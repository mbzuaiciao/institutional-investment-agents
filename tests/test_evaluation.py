from pathlib import Path

from institutional_investment_agents.evaluation import (
    CAPSTONE_VARIANTS,
    run_evaluation,
    write_json,
    write_markdown,
)


def test_capstone_smoke_and_aggregation(tmp_path: Path) -> None:
    result = run_evaluation(CAPSTONE_VARIANTS[:2], seeds=(17,), issuer_ids=("NRT",))
    assert len(result["runs"]) == 2
    assert set(result["summary"]) == {"A", "B"}
    assert (
        result["summary"]["B"]["claim_support_rate"] > result["summary"]["A"]["claim_support_rate"]
    )
    json_path = tmp_path / "capstone.json"
    markdown_path = tmp_path / "capstone.md"
    write_json(result, json_path)
    write_markdown(result, markdown_path)
    assert json_path.read_text().endswith("\n")
    assert "Capstone architecture comparison" in markdown_path.read_text()


def test_all_required_variants_exist() -> None:
    assert [variant.key for variant in CAPSTONE_VARIANTS] == ["A", "B", "C", "D", "E", "F"]
