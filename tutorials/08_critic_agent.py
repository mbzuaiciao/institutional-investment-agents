"""Tutorial 08: the critic attacks assumptions and records challenges."""

from institutional_investment_agents.workflow import ResearchWorkbench


def main() -> None:
    run = ResearchWorkbench().run("CRH")
    for challenge in run.state.challenges:
        print(challenge.model_dump_json(indent=2))
    print("Risks after challenge:", [risk.name for risk in run.memo.key_risks])


if __name__ == "__main__":
    main()
