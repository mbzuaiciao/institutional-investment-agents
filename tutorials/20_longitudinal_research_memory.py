"""Tutorial 20: persistent state is tested across five dated research updates."""

from institutional_investment_agents.longitudinal import run_longitudinal_research


def main() -> None:
    for persistent in (False, True):
        run = run_longitudinal_research("medium", persistent=persistent, seed=11)
        print("persistent" if persistent else "stateless", run.metrics.model_dump())


if __name__ == "__main__":
    main()
