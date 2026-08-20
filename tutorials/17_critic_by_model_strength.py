"""Tutorial 17: critic value is conditional on base-model risk capability."""

from institutional_investment_agents.phase2_evaluation import run_critic_study


def main() -> None:
    summary = run_critic_study(seeds=(11,))["summary"]
    for model in ("weak", "medium", "strong"):
        off = summary[f"{model}|False"]["risk_factor_recall_mean"]
        on = summary[f"{model}|True"]["risk_factor_recall_mean"]
        print(f"{model}: critic Δ risk recall = {on - off:+.3f}")


if __name__ == "__main__":
    main()
