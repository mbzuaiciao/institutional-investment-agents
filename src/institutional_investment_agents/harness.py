"""Operational Phase 2 harness profiles, independent of model capability."""

from __future__ import annotations

from institutional_investment_agents.phase2_schemas import HarnessLevel, HarnessProfile

HARNESS_PROFILES: dict[str, HarnessProfile] = {
    "weak": HarnessProfile(
        name=HarnessLevel.H0_MINIMAL,
        strength=0,
        explicit_plan=False,
        deterministic_routing=False,
        evidence_ids=False,
        typed_tools=False,
        shared_state=False,
        specialist_partitioning=False,
        critic=False,
        verifier=False,
        contradiction_handling=False,
        revision_loop=False,
        approval_gate=False,
        stale_evidence_exclusion=False,
        audit_trace=False,
    ),
    "structured": HarnessProfile(
        name=HarnessLevel.H1_STRUCTURED,
        strength=1,
        explicit_plan=True,
        deterministic_routing=True,
        evidence_ids=True,
        typed_tools=True,
        shared_state=True,
        specialist_partitioning=False,
        critic=False,
        verifier=False,
        contradiction_handling=False,
        revision_loop=False,
        approval_gate=False,
        stale_evidence_exclusion=False,
        audit_trace=True,
    ),
    "strong": HarnessProfile(
        name=HarnessLevel.H2_STRONG,
        strength=2,
        explicit_plan=True,
        deterministic_routing=True,
        evidence_ids=True,
        typed_tools=True,
        shared_state=True,
        specialist_partitioning=True,
        critic=True,
        verifier=True,
        contradiction_handling=True,
        revision_loop=True,
        approval_gate=True,
        stale_evidence_exclusion=True,
        audit_trace=True,
    ),
}


def get_harness_profile(name: str) -> HarnessProfile:
    try:
        return HARNESS_PROFILES[name]
    except KeyError as error:
        raise KeyError(f"unknown harness profile: {name}") from error
