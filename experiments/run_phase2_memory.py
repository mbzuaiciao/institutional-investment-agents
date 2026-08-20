"""Compare stateless and persistent structured research across five updates."""

from institutional_investment_agents.phase2_evaluation import run_memory_study


def main() -> None:
    result = run_memory_study()
    print(result["summary"])


if __name__ == "__main__":
    main()
