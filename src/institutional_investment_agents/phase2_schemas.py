"""Typed Phase 2 objects for model/harness experiments and longitudinal research."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ModelOperation(StrEnum):
    PLAN = "plan_generation"
    EXECUTE_TASK = "task_execution"
    ROUTE = "routing"
    RETRIEVE = "retrieval"
    INTERPRET_EVIDENCE = "evidence_interpretation"
    SELECT_TOOL = "tool_selection"
    GENERATE_CLAIMS = "claim_generation"
    SYNTHESIZE = "thesis_synthesis"
    CRITIQUE = "critique"
    REVISE = "revision"
    VERIFY = "verification_assistance"


class FailureType(StrEnum):
    EVIDENCE_OMISSION = "evidence_omission"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    ARITHMETIC_ERROR = "arithmetic_error"
    INCORRECT_TOOL = "incorrect_tool_selection"
    MISSED_TOOL = "failure_to_call_needed_tool"
    DUPLICATE_TOOL = "duplicate_tool_call"
    RETRIEVAL_MISS = "retrieval_miss"
    ROUTING_ERROR = "routing_error"
    PREMATURE_SYNTHESIS = "premature_synthesis"
    IGNORED_CONTRADICTION = "ignored_contradiction"
    INCORRECT_CONFIDENCE = "incorrect_confidence"
    OVERCONFIDENT_UNSUPPORTED = "overconfident_unsupported_claim"
    MISSED_RISK = "missed_risk_factor"
    MALFORMED_OUTPUT = "malformed_structured_output"
    STALE_EVIDENCE = "stale_evidence_use"
    FAILED_REVISION = "failure_to_revise_after_critique"
    CITATION_MISMATCH = "citation_mismatch"
    FALSE_CHALLENGE = "false_challenge"
    MEMORY_FAILURE = "memory_failure"


class FailureOrigin(StrEnum):
    MODEL = "model"
    HARNESS = "harness"
    BOTH = "both"


class EvidenceFreshness(StrEnum):
    CURRENT = "current"
    STALE = "stale"
    SUPERSEDED = "superseded"


class HardEpisodeFamily(StrEnum):
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    MISLEADING_CHEAPNESS = "misleading_cheapness"
    TOOL_NECESSITY = "tool_necessity"
    RETRIEVAL_DISTRACTORS = "retrieval_distractors"
    STALE_EVIDENCE = "stale_evidence"
    MISSING_DATA = "missing_data"
    SCENARIO_SENSITIVITY = "scenario_sensitivity"
    FALSE_CORRELATION = "false_correlation"
    MULTI_HOP_EVIDENCE = "multi_hop_evidence"


class HarnessLevel(StrEnum):
    H0_MINIMAL = "H0_minimal"
    H1_STRUCTURED = "H1_structured"
    H2_STRONG = "H2_strong"


class ModelRequest(FrozenModel):
    operation: ModelOperation
    episode_id: str
    instruction: str
    context: tuple[str, ...] = ()
    available_tools: tuple[str, ...] = ()
    required_schema: str | None = None


class ModelFailure(FrozenModel):
    failure_type: FailureType
    operation: ModelOperation
    detail: str
    origin: FailureOrigin = FailureOrigin.MODEL


class ConfidenceComponents(FrozenModel):
    """Heuristic internal scores; these are not calibrated probabilities."""

    evidence: float = Field(ge=0.0, le=1.0)
    calculation: float = Field(ge=0.0, le=1.0)
    retrieval: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    model_judgment: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    calibrated: bool = False


class ModelResponse(FrozenModel):
    operation: ModelOperation
    structured_output: dict[str, Any] = Field(default_factory=dict)
    failures: tuple[ModelFailure, ...] = ()
    confidence: ConfidenceComponents
    usage: dict[str, int | float] = Field(default_factory=dict)


class ModelProfile(FrozenModel):
    name: str
    reasoning_accuracy: float = Field(ge=0.0, le=1.0)
    retrieval_interpretation_accuracy: float = Field(ge=0.0, le=1.0)
    tool_selection_accuracy: float = Field(ge=0.0, le=1.0)
    arithmetic_without_tool_accuracy: float = Field(ge=0.0, le=1.0)
    contradiction_detection: float = Field(ge=0.0, le=1.0)
    risk_recall: float = Field(ge=0.0, le=1.0)
    citation_fidelity: float = Field(ge=0.0, le=1.0)
    revision_responsiveness: float = Field(ge=0.0, le=1.0)
    structured_output_fidelity: float = Field(ge=0.0, le=1.0)
    confidence_calibration: float = Field(ge=0.0, le=1.0)
    strength: int = Field(ge=0, le=2)


class HarnessProfile(FrozenModel):
    name: HarnessLevel
    strength: int = Field(ge=0, le=2)
    explicit_plan: bool
    deterministic_routing: bool
    evidence_ids: bool
    typed_tools: bool
    shared_state: bool
    specialist_partitioning: bool
    critic: bool
    verifier: bool
    contradiction_handling: bool
    revision_loop: bool
    approval_gate: bool
    stale_evidence_exclusion: bool
    audit_trace: bool


class VersionedEvidence(FrozenModel):
    id: str
    version: int = Field(ge=1)
    source: str
    text: str
    published_date: str
    valid_until: str | None = None
    supersedes_id: str | None = None
    relevant: bool = True
    supports: tuple[str, ...] = ()


class HardResearchEpisode(FrozenModel):
    id: str
    family: HardEpisodeFamily
    issuer_id: str
    as_of_date: str
    evidence: tuple[VersionedEvidence, ...]
    required_risks: tuple[str, ...]
    expected_direction: str
    requires_tool: bool = False
    has_contradiction: bool = False
    missing_fields: tuple[str, ...] = ()
    complexity: int = Field(ge=1, le=5)
    metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class CostAccount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_calls: int = Field(default=0, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    retrieval_operations: int = Field(default=0, ge=0)
    workflow_steps: int = Field(default=0, ge=0)
    critic_calls: int = Field(default=0, ge=0)
    verifier_calls: int = Field(default=0, ge=0)
    revision_cycles: int = Field(default=0, ge=0)
    simulated_token_units: int = Field(default=0, ge=0)
    simulated_cost_units: float = Field(default=0.0, ge=0.0)

    def record_model_call(self, operation: ModelOperation, token_units: int) -> None:
        self.model_calls += 1
        self.workflow_steps += 1
        self.simulated_token_units += token_units
        self.simulated_cost_units = round(self.simulated_cost_units + token_units / 1000, 4)
        if operation == ModelOperation.CRITIQUE:
            self.critic_calls += 1
        elif operation == ModelOperation.VERIFY:
            self.verifier_calls += 1
        elif operation == ModelOperation.REVISE:
            self.revision_cycles += 1


class Phase2Metrics(FrozenModel):
    research_quality_score: float = Field(ge=0.0, le=100.0)
    directional_accuracy: float = Field(ge=0.0, le=1.0)
    risk_factor_recall: float = Field(ge=0.0, le=1.0)
    contradiction_detection: float = Field(ge=0.0, le=1.0)
    calculation_accuracy: float = Field(ge=0.0, le=1.0)
    claim_support_rate: float = Field(ge=0.0, le=1.0)
    citation_validity: float = Field(ge=0.0, le=1.0)
    stale_evidence_usage_rate: float = Field(ge=0.0, le=1.0)
    inappropriate_confidence_rate: float = Field(ge=0.0, le=1.0)
    unsupported_claims: int = Field(ge=0)
    invalid_citations: int = Field(ge=0)
    unresolved_contradictions: int = Field(ge=0)
    revisions: int = Field(ge=0)
    correct_revisions: int = Field(ge=0)
    unnecessary_revisions: int = Field(ge=0)
    false_challenges: int = Field(ge=0)
    control_quality_score: float = Field(ge=0.0, le=100.0)


class Phase2Run(FrozenModel):
    run_id: str
    seed: int
    model_profile: str
    harness_profile: HarnessLevel
    episode_id: str
    episode_family: HardEpisodeFamily
    metrics: Phase2Metrics
    confidence: ConfidenceComponents
    cost: CostAccount
    injected_failures: tuple[ModelFailure, ...]
    unresolved_failures: tuple[ModelFailure, ...]
    detected_failures: tuple[FailureType, ...] = ()


class LongitudinalMetrics(FrozenModel):
    update_accuracy: float = Field(ge=0.0, le=1.0)
    consistency: float = Field(ge=0.0, le=1.0)
    stale_evidence_usage_rate: float = Field(ge=0.0, le=1.0)
    redundant_research_operations: int = Field(ge=0)
    revision_quality: float = Field(ge=0.0, le=1.0)
    forgetting_rate: float = Field(ge=0.0, le=1.0)
    anchoring_rate: float = Field(ge=0.0, le=1.0)
    quality_by_episode: tuple[float, ...]


class LongitudinalRun(FrozenModel):
    seed: int
    model_profile: str
    persistent: bool
    metrics: LongitudinalMetrics
    cost: CostAccount


class LongitudinalState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    issuer_id: str
    prior_thesis: str | None = None
    evidence_versions: dict[str, VersionedEvidence] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    invalidation_conditions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    confidence_history: list[float] = Field(default_factory=list)
    thesis_history: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def confidence_matches_thesis_history(self) -> LongitudinalState:
        if len(self.confidence_history) != len(self.thesis_history):
            raise ValueError("confidence and thesis histories must have equal length")
        return self
