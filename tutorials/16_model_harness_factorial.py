"""Tutorial 16: cross model and harness strength on one fixed hard case."""

from institutional_investment_agents.phase2_evaluation import run_factorial
from institutional_investment_agents.phase2_schemas import HardEpisodeFamily


def main() -> None:
    result = run_factorial(seeds=(11,), families=(HardEpisodeFamily.CONTRADICTORY_EVIDENCE,))
    for row in result["cell_summary"]:
        print(row["model_profile"], row["harness_profile"], row["research_quality_score_mean"])


if __name__ == "__main__":
    main()
