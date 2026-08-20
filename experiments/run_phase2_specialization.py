"""Test context partitioning under complex cases with a fixed model-call budget."""

from institutional_investment_agents.phase2_evaluation import run_specialization_study


def main() -> None:
    result = run_specialization_study()
    print(result["summary"])


if __name__ == "__main__":
    main()
