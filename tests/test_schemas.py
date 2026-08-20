import pytest
from pydantic import ValidationError

from institutional_investment_agents.schemas import AgentRole, Claim, ClaimType


def test_factual_claim_requires_evidence() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="c",
            text="A fact",
            claim_type=ClaimType.FACTUAL,
            confidence=0.8,
            author=AgentRole.CREDIT,
        )


def test_calculated_claim_requires_tool_result() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="c",
            text="A calculation",
            claim_type=ClaimType.CALCULATED,
            confidence=1.0,
            author=AgentRole.CREDIT,
        )


def test_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Claim(
            id="c",
            text="A view",
            claim_type=ClaimType.JUDGMENT,
            confidence=1.1,
            author=AgentRole.CREDIT,
        )


def test_judgment_can_expose_absence_of_support() -> None:
    claim = Claim(
        id="c",
        text="A view",
        claim_type=ClaimType.JUDGMENT,
        confidence=0.5,
        author=AgentRole.CREDIT,
    )
    assert claim.evidence_ids == ()
