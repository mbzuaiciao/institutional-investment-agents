"""Tutorial 02: decompose a question into inspectable typed tasks."""

from institutional_investment_agents.workflow import (
    ResearchWorkbench,
    WorkflowConfig,
    default_question,
)


def main() -> None:
    workbench = ResearchWorkbench(WorkflowConfig(critic_enabled=False, verification_enabled=False))
    plan = workbench._create_plan(default_question("NRT"))
    for task in plan.tasks:
        print(f"{task.id}: {task.assigned_role} -> {task.objective}")
    print("A plan improves inspectability; it does not itself prove any claim.")


if __name__ == "__main__":
    main()
