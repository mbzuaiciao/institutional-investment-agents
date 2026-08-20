"""Tutorial 14: named model strengths are operational capability vectors."""

from institutional_investment_agents.stochastic_model import MODEL_PROFILES


def main() -> None:
    for name, profile in MODEL_PROFILES.items():
        print(name, profile.model_dump(exclude={"name", "strength"}))


if __name__ == "__main__":
    main()
