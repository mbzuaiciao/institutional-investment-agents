"""Tutorial 12: integrate plan, specialists, tools, critic, verifier, and gate."""

from institutional_investment_agents.workflow import ResearchWorkbench


def main() -> None:
    run = ResearchWorkbench().run("NRT")
    print(run.memo.model_dump_json(indent=2))
    print("metrics:", run.metrics)


if __name__ == "__main__":
    main()
