"""Tutorial 22: diagnose failures by meaning, origin, detector, and metric."""

from institutional_investment_agents.failure_taxonomy import FAILURE_TAXONOMY


def main() -> None:
    for failure_type, definition in FAILURE_TAXONOMY.items():
        print(f"{failure_type.value}: {definition.origin.value} | {', '.join(definition.metrics)}")


if __name__ == "__main__":
    main()
