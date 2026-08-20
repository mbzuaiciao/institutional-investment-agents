"""Tutorial 07: specialists contribute typed claims to one evidence layer."""

from collections import Counter

from institutional_investment_agents.workflow import ResearchWorkbench, WorkflowConfig


def main() -> None:
    run = ResearchWorkbench(WorkflowConfig(critic_enabled=False, verification_enabled=False)).run(
        "NRT"
    )
    contributions = Counter(claim.author for claim in run.state.claims.values())
    for role, count in contributions.items():
        print(role, count)


if __name__ == "__main__":
    main()
