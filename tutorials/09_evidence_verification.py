"""Tutorial 09: verify claim pointers and citation support mechanically."""

from institutional_investment_agents.verification import verify_state
from institutional_investment_agents.workflow import ResearchWorkbench


def main() -> None:
    run = ResearchWorkbench().run("NRT")
    print(verify_state(run.state).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
