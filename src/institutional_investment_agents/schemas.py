"""Typed domain objects for auditable institutional credit research."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AgentRole(StrEnum):
    PLANNER = "research_planner"
    CREDIT = "credit_analyst"
    MACRO = "macro_rates_analyst"
    RELATIVE_VALUE = "relative_value_analyst"
    EVIDENCE = "evidence_researcher"
    SYNTHESIZER = "thesis_synthesizer"
    CRITIC = "challenge_agent"
    VERIFIER = "evidence_verifier"
    HUMAN = "human_reviewer"
    SINGLE = "single_research_agent"


class ClaimType(StrEnum):
    FACTUAL = "factual"
    CALCULATED = "calculated"
    INFERRED = "inferred"
    JUDGMENT = "judgment"


class TaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETE = "complete"
    BLOCKED = "blocked"


class ApprovalStatus(StrEnum):
    APPROVED = "approved"
    REVISE = "revise"
    REJECTED = "rejected"


class ResearchQuestion(FrozenModel):
    issuer_id: str
    horizon_years: int = Field(default=5, ge=1, le=30)
    text: str = Field(min_length=10)


class ResearchTask(FrozenModel):
    id: str
    title: str
    objective: str
    assigned_role: AgentRole
    status: TaskStatus = TaskStatus.PENDING


class ResearchPlan(FrozenModel):
    id: str
    question: ResearchQuestion
    tasks: tuple[ResearchTask, ...]


class ToolCall(FrozenModel):
    id: str
    tool_name: str
    arguments: dict[str, Any]
    actor: AgentRole


class ToolResult(FrozenModel):
    id: str
    call_id: str
    tool_name: str
    value: float | str | dict[str, float]
    units: str | None = None
    inputs: dict[str, Any]


class Citation(FrozenModel):
    evidence_id: str
    source: str
    locator: str


class EvidenceItem(FrozenModel):
    id: str
    source: str
    title: str
    text: str
    locator: str
    issuer_id: str | None = None
    published_date: str | None = None
    tags: tuple[str, ...] = ()


class Claim(FrozenModel):
    id: str
    text: str
    claim_type: ClaimType
    evidence_ids: tuple[str, ...] = ()
    tool_result_ids: tuple[str, ...] = ()
    confidence: float = Field(ge=0.0, le=1.0)
    assumptions: tuple[str, ...] = ()
    author: AgentRole

    @model_validator(mode="after")
    def require_support_pointer(self) -> Claim:
        if self.claim_type == ClaimType.FACTUAL and not self.evidence_ids:
            raise ValueError("factual claims require at least one evidence ID")
        if self.claim_type == ClaimType.CALCULATED and not self.tool_result_ids:
            raise ValueError("calculated claims require at least one tool-result ID")
        return self


class ResearchObservation(FrozenModel):
    id: str
    task_id: str
    actor: AgentRole
    summary: str
    evidence_ids: tuple[str, ...] = ()
    claim_ids: tuple[str, ...] = ()


class RiskFactor(FrozenModel):
    id: str
    name: str
    description: str
    severity: int = Field(ge=1, le=5)
    evidence_ids: tuple[str, ...] = ()
    trigger: str


class Scenario(FrozenModel):
    name: str
    probability: float = Field(ge=0.0, le=1.0)
    spread_change_bps: float
    rate_change_bps: float
    default_probability: float = Field(ge=0.0, le=1.0)
    rationale: str


class InvestmentThesis(FrozenModel):
    issuer_id: str
    conclusion: str
    rationale_claim_ids: tuple[str, ...]
    risks: tuple[RiskFactor, ...]
    scenarios: tuple[Scenario, ...]
    invalidation_conditions: tuple[str, ...]
    confidence: float = Field(ge=0.0, le=1.0)


class Challenge(FrozenModel):
    id: str
    target_claim_id: str | None
    issue_type: str
    severity: int = Field(ge=1, le=5)
    explanation: str
    conflicting_evidence_ids: tuple[str, ...] = ()
    resolution_status: str = "open"


class VerificationResult(FrozenModel):
    valid: bool
    claim_support_rate: float
    citation_validity: float
    evidence_coverage: float
    unsupported_claim_ids: tuple[str, ...]
    missing_evidence_ids: tuple[str, ...]
    unresolved_contradictions: int
    notes: tuple[str, ...] = ()


class ApprovalDecision(FrozenModel):
    status: ApprovalStatus
    reviewer: str
    rationale: str
    conditions: tuple[str, ...] = ()


class AuditEvent(FrozenModel):
    sequence: int = Field(ge=1)
    event_type: str
    actor: AgentRole
    object_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime | None = None


class ResearchState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: ResearchQuestion
    plan: ResearchPlan | None = None
    completed_task_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, EvidenceItem] = Field(default_factory=dict)
    claims: dict[str, Claim] = Field(default_factory=dict)
    tool_results: dict[str, ToolResult] = Field(default_factory=dict)
    observations: list[ResearchObservation] = Field(default_factory=list)
    risks: list[RiskFactor] = Field(default_factory=list)
    challenges: list[Challenge] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    audit: list[AuditEvent] = Field(default_factory=list)


class ResearchMemo(FrozenModel):
    issuer_id: str
    executive_summary: str
    issuer_overview: str
    fundamental_credit_analysis: str
    market_pricing: str
    peer_relative_value: str
    macro_rates_context: str
    scenarios: tuple[Scenario, ...]
    thesis: InvestmentThesis
    key_risks: tuple[RiskFactor, ...]
    invalidation_conditions: tuple[str, ...]
    evidence_table: tuple[Citation, ...]
    unresolved_questions: tuple[str, ...]
    confidence_assessment: str
    approval: ApprovalDecision
    audit_metadata: dict[str, str | int | float]
