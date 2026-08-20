"""Tutorial 18: verification detects and may repair naturally occurring errors."""

from institutional_investment_agents.phase2_evaluation import run_verification_study


def main() -> None:
    summary = run_verification_study(seeds=(11,))["summary"]
    for model in ("weak", "medium", "strong"):
        off = summary[f"{model}|False"]
        on = summary[f"{model}|True"]
        print(
            f"{model}: unsupported {off['unsupported_claims_mean']:.2f} → {on['unsupported_claims_mean']:.2f}; cost {off['simulated_cost_units_mean']:.2f} → {on['simulated_cost_units_mean']:.2f}"
        )


if __name__ == "__main__":
    main()
