"""Tutorial 19: specialization matters only when context partitioning changes."""

from institutional_investment_agents.phase2_evaluation import run_specialization_study


def main() -> None:
    summary = run_specialization_study(seeds=(11,))["summary"]
    for model in ("weak", "medium", "strong"):
        single = summary[f"{model}|False"]["risk_factor_recall_mean"]
        specialist = summary[f"{model}|True"]["risk_factor_recall_mean"]
        print(f"{model}: partitioned-context Δ risk recall = {specialist - single:+.3f}")


if __name__ == "__main__":
    main()
