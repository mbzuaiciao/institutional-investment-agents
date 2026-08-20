"""Explicit research-state transitions and reconstruction-friendly audit events."""

from __future__ import annotations

from typing import Any

from institutional_investment_agents.schemas import (
    AgentRole,
    AuditEvent,
    Claim,
    EvidenceItem,
    ResearchObservation,
    ResearchPlan,
    ResearchState,
    ToolResult,
)


class StateManager:
    def __init__(self, state: ResearchState) -> None:
        self.state = state

    def event(
        self,
        event_type: str,
        actor: AgentRole,
        object_id: str | None = None,
        **details: Any,
    ) -> None:
        self.state.audit.append(
            AuditEvent(
                sequence=len(self.state.audit) + 1,
                event_type=event_type,
                actor=actor,
                object_id=object_id,
                details=details,
            )
        )

    def set_plan(self, plan: ResearchPlan) -> None:
        self.state.plan = plan
        self.event("plan_created", AgentRole.PLANNER, plan.id, task_count=len(plan.tasks))

    def add_evidence(self, item: EvidenceItem, actor: AgentRole) -> None:
        if item.id not in self.state.evidence:
            self.state.evidence[item.id] = item
            self.event("evidence_added", actor, item.id, source=item.source, locator=item.locator)

    def add_tool_result(self, result: ToolResult, actor: AgentRole) -> None:
        self.state.tool_results[result.id] = result
        self.event("tool_result", actor, result.id, tool=result.tool_name, call_id=result.call_id)

    def add_claim(self, claim: Claim) -> None:
        missing_evidence = set(claim.evidence_ids) - self.state.evidence.keys()
        missing_results = set(claim.tool_result_ids) - self.state.tool_results.keys()
        if missing_evidence or missing_results:
            raise ValueError("claim support must be added to state before the claim")
        self.state.claims[claim.id] = claim
        self.event(
            "claim_created",
            claim.author,
            claim.id,
            claim_type=claim.claim_type.value,
            evidence_ids=list(claim.evidence_ids),
            tool_result_ids=list(claim.tool_result_ids),
        )

    def complete_task(self, task_id: str, observation: ResearchObservation) -> None:
        if task_id not in self.state.completed_task_ids:
            self.state.completed_task_ids.append(task_id)
        self.state.observations.append(observation)
        self.event("task_completed", observation.actor, task_id, observation_id=observation.id)


def assert_audit_sequence(state: ResearchState) -> None:
    expected = list(range(1, len(state.audit) + 1))
    actual = [event.sequence for event in state.audit]
    if actual != expected:
        raise ValueError("audit sequence is not contiguous")
