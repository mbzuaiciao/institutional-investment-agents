"""Compare free-form versus explicit workflow with data, tools, and roles held fixed."""

from institutional_investment_agents.evaluation import ArchitectureVariant, run_evaluation

FREE_FORM = ArchitectureVariant(
    "free_form",
    "Free-form specialist research",
    {
        "architecture": "free_form",
        "specialists_enabled": True,
        "critic_enabled": False,
        "verification_enabled": False,
        "structured_outputs": False,
        "tool_access": True,
        "retrieval_enabled": True,
        "explicit_workflow": False,
    },
)
EXPLICIT = ArchitectureVariant(
    "explicit",
    "Explicit institutional workflow",
    {
        **FREE_FORM.overrides,
        "architecture": "explicit_workflow",
        "structured_outputs": True,
        "explicit_workflow": True,
    },
)


def main() -> None:
    result = run_evaluation((FREE_FORM, EXPLICIT), seeds=(17,))
    print(result["summary"])


if __name__ == "__main__":
    main()
