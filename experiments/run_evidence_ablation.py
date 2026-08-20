"""Compare otherwise identical workflows with and without verification."""

from institutional_investment_agents.evaluation import CAPSTONE_VARIANTS, run_evaluation


def main() -> None:
    result = run_evaluation((CAPSTONE_VARIANTS[3], CAPSTONE_VARIANTS[4]), seeds=(17,))
    print(result["summary"])


if __name__ == "__main__":
    main()
