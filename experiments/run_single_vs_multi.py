"""Compare single versus specialist ownership with every other setting held fixed."""

from institutional_investment_agents.evaluation import ArchitectureVariant, run_evaluation

SINGLE = ArchitectureVariant(
    "single",
    "Single agent, structured workflow",
    {
        "architecture": "single_structured",
        "specialists_enabled": False,
        "critic_enabled": False,
        "verification_enabled": False,
        "structured_outputs": True,
        "tool_access": True,
        "retrieval_enabled": True,
        "explicit_workflow": True,
    },
)
MULTI = ArchitectureVariant(
    "multi",
    "Specialist agents, structured workflow",
    {**SINGLE.overrides, "architecture": "multi_structured", "specialists_enabled": True},
)


def main() -> None:
    result = run_evaluation((SINGLE, MULTI), seeds=(17,))
    print(result["summary"])


if __name__ == "__main__":
    main()
