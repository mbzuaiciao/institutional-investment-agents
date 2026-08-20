import pytest

from institutional_investment_agents.schemas import (
    AgentRole,
    Claim,
    ClaimType,
    EvidenceItem,
    ResearchState,
)
from institutional_investment_agents.state import StateManager, assert_audit_sequence
from institutional_investment_agents.verification import verify_state
from institutional_investment_agents.workflow import default_question


def test_claim_must_reference_existing_state_object() -> None:
    manager = StateManager(ResearchState(question=default_question("NRT")))
    claim = Claim(
        id="c",
        text="Debt is $9bn",
        claim_type=ClaimType.FACTUAL,
        evidence_ids=("missing",),
        confidence=0.8,
        author=AgentRole.CREDIT,
    )
    with pytest.raises(ValueError):
        manager.add_claim(claim)


def test_supported_and_unsupported_claim_detection() -> None:
    state = ResearchState(question=default_question("NRT"))
    manager = StateManager(state)
    evidence = EvidenceItem(
        id="ev",
        source="source",
        title="filing",
        text="Northstar debt is $9bn and EBITDA is $2bn.",
        locator="p1",
    )
    manager.add_evidence(evidence, AgentRole.EVIDENCE)
    manager.add_claim(
        Claim(
            id="supported",
            text="Northstar debt is $9bn.",
            claim_type=ClaimType.FACTUAL,
            evidence_ids=("ev",),
            confidence=0.9,
            author=AgentRole.CREDIT,
        )
    )
    manager.add_claim(
        Claim(
            id="unsupported",
            text="Management quality is exceptional.",
            claim_type=ClaimType.JUDGMENT,
            confidence=0.5,
            author=AgentRole.CREDIT,
        )
    )
    result = verify_state(state)
    assert result.claim_support_rate == 0.5
    assert result.unsupported_claim_ids == ("unsupported",)
    assert not result.valid


def test_audit_sequence() -> None:
    state = ResearchState(question=default_question("NRT"))
    manager = StateManager(state)
    manager.event("one", AgentRole.PLANNER)
    manager.event("two", AgentRole.PLANNER)
    assert_audit_sequence(state)
    state.audit[1] = state.audit[1].model_copy(update={"sequence": 4})
    with pytest.raises(ValueError):
        assert_audit_sequence(state)
