"""Measure verification and revision when support errors arise naturally."""

from institutional_investment_agents.phase2_evaluation import run_verification_study


def main() -> None:
    result = run_verification_study()
    print(result["summary"])


if __name__ == "__main__":
    main()
