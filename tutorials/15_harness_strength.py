"""Tutorial 15: harness strength changes constraints, not model identity."""

from institutional_investment_agents.harness import HARNESS_PROFILES


def main() -> None:
    for name, profile in HARNESS_PROFILES.items():
        enabled = [key for key, value in profile.model_dump().items() if value is True]
        print(f"{name} ({profile.name.value}): {', '.join(enabled) or 'minimal controls'}")


if __name__ == "__main__":
    main()
