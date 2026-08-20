import pytest

from institutional_investment_agents.schemas import ApprovalStatus
from institutional_investment_agents.workflow import ResearchWorkbench, WorkflowConfig


@pytest.mark.parametrize("issuer_id", ["NRT", "CRH", "BAY", "VTX"])
def test_full_workflow_is_complete_and_auditable(issuer_id: str) -> None:
    run = ResearchWorkbench().run(issuer_id)
    assert run.metrics["task_completion"] == 1.0
    assert run.metrics["directional_accuracy"] == 1.0
    assert run.verification.claim_support_rate == 1.0
    assert run.memo.approval.status == ApprovalStatus.APPROVED
    assert [event.sequence for event in run.state.audit] == list(range(1, len(run.state.audit) + 1))
    assert {
        "research_started",
        "plan_created",
        "tool_called",
        "challenge_created",
        "verification_completed",
        "approval_decision",
        "memo_generated",
        "research_completed",
    } <= {event.event_type for event in run.state.audit}


def test_trace_reconstructs_claim_support() -> None:
    run = ResearchWorkbench().run("NRT")
    for claim in run.state.claims.values():
        assert set(claim.evidence_ids) <= run.state.evidence.keys()
        assert set(claim.tool_result_ids) <= run.state.tool_results.keys()
    claim_events = [event for event in run.state.audit if event.event_type == "claim_created"]
    assert len(claim_events) == len(run.state.claims)


def test_baseline_exposes_unsupported_judgment() -> None:
    config = WorkflowConfig(
        architecture="baseline",
        specialists_enabled=False,
        critic_enabled=False,
        verification_enabled=False,
        structured_outputs=False,
        tool_access=False,
        retrieval_enabled=False,
        explicit_workflow=False,
    )
    run = ResearchWorkbench(config).run("NRT")
    assert run.metrics["unsupported_claims"] == 1
    assert run.metrics["tool_calls"] == 0


def test_critic_improves_or_preserves_risk_recall() -> None:
    without = ResearchWorkbench(WorkflowConfig(critic_enabled=False)).run("CRH")
    with_critic = ResearchWorkbench(WorkflowConfig(critic_enabled=True)).run("CRH")
    assert with_critic.metrics["risk_factor_recall"] >= without.metrics["risk_factor_recall"]
    assert with_critic.state.challenges


def test_reproducible_run_excluding_object_identity() -> None:
    first = ResearchWorkbench(WorkflowConfig(seed=23)).run("BAY")
    second = ResearchWorkbench(WorkflowConfig(seed=23)).run("BAY")
    assert first.memo == second.memo
    assert first.metrics == second.metrics
    assert first.state.model_dump() == second.state.model_dump()
