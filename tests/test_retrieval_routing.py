from institutional_investment_agents.dataset import generate_universe
from institutional_investment_agents.retrieval import LocalRetriever
from institutional_investment_agents.routing import route_task, routing_accuracy
from institutional_investment_agents.schemas import AgentRole
from institutional_investment_agents.workflow import (
    ResearchWorkbench,
    WorkflowConfig,
    default_question,
)


def test_retrieval_scopes_issuer_and_preserves_provenance() -> None:
    results = LocalRetriever(generate_universe().documents).search(
        "debt EBITDA spread", issuer_id="NRT", limit=5
    )
    assert results
    assert all(item.issuer_id in {"NRT", None} for item in results)
    assert all(item.id and item.source and item.locator for item in results)


def test_duplicate_evidence_ids_rejected() -> None:
    item = generate_universe().documents[0]
    try:
        LocalRetriever([item, item])
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("duplicate evidence should fail")


def test_routing_rules() -> None:
    assert route_task("Macro and rates", "curve") == AgentRole.MACRO
    assert route_task("Peer relative value", "spread") == AgentRole.RELATIVE_VALUE
    assert route_task("Evidence", "provenance") == AgentRole.EVIDENCE
    assert route_task("Anything", "anything", naive=True) == AgentRole.SINGLE


def test_plan_routing_accuracy() -> None:
    workbench = ResearchWorkbench(WorkflowConfig(critic_enabled=False))
    plan = workbench._create_plan(default_question("NRT"))
    assert routing_accuracy(plan.tasks) == 1.0
