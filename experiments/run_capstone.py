"""Run the reproducible multi-seed architecture capstone."""

from pathlib import Path

from institutional_investment_agents.evaluation import (
    run_evaluation,
    write_json,
    write_markdown,
    write_plots,
)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = run_evaluation()
    write_json(result, root / "results" / "capstone.json")
    write_markdown(result, root / "results" / "capstone.md")
    outputs = write_plots(result, root / "results" / "figures")
    print(f"capstone: {len(result['runs'])} runs; wrote {2 + len(outputs)} artifacts")


if __name__ == "__main__":
    main()
