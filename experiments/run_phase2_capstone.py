"""Run the Phase 2 model × harness matrix and all focused studies."""

from pathlib import Path

from institutional_investment_agents.phase2_evaluation import (
    run_phase2_capstone,
    write_phase2_csv,
    write_phase2_json,
    write_phase2_markdown,
    write_phase2_plots,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = run_phase2_capstone()
    write_phase2_json(result, root / "results" / "phase2_capstone.json")
    write_phase2_markdown(result, root / "results" / "phase2_capstone.md")
    write_phase2_csv(result, root / "results" / "phase2_summary.csv")
    figures = write_phase2_plots(result, root / "results" / "figures")
    print(
        f"phase2 capstone: {result['primary_run_count']} primary / "
        f"{result['total_run_count']} total runs; wrote {3 + len(figures)} artifacts"
    )


if __name__ == "__main__":
    main()
