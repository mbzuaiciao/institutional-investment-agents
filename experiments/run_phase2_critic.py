"""Measure critic value separately for weak, medium, and strong model profiles."""

from institutional_investment_agents.phase2_evaluation import run_critic_study


def main() -> None:
    result = run_critic_study()
    print(result["summary"])


if __name__ == "__main__":
    main()
