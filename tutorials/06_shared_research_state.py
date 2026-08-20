"""Tutorial 06: shared research state is not just appended chat history."""

from institutional_investment_agents.workflow import ResearchWorkbench, WorkflowConfig


def main() -> None:
    run = ResearchWorkbench(WorkflowConfig(critic_enabled=False, verification_enabled=False)).run(
        "NRT"
    )
    state = run.state
    print(
        {
            "tasks": state.completed_task_ids,
            "evidence": list(state.evidence),
            "claims": list(state.claims),
            "tool_results": list(state.tool_results),
            "audit_events": len(state.audit),
        }
    )


if __name__ == "__main__":
    main()
