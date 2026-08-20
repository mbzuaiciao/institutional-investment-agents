"""Tutorial 10: an approval is an explicit decision, not output visibility."""

from institutional_investment_agents.workflow import ResearchWorkbench


def main() -> None:
    decision = ResearchWorkbench().run("NRT").memo.approval
    print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
