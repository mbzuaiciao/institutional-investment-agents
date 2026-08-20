"""Tutorial 11: compare harnesses on behavior, evidence, quality, and cost proxies."""

from institutional_investment_agents.evaluation import CAPSTONE_VARIANTS, run_evaluation


def main() -> None:
    result = run_evaluation(
        (CAPSTONE_VARIANTS[0], CAPSTONE_VARIANTS[4]), seeds=(17,), issuer_ids=("NRT", "CRH")
    )
    print(result["summary"])


if __name__ == "__main__":
    main()
