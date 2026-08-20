"""Preregistered Phase 3 treatment contrasts and metrics."""

from __future__ import annotations

from dataclasses import dataclass

from institutional_investment_agents.phase2_schemas import HarnessLevel, ModelOperation
from institutional_investment_agents.phase3_runtime import HARNESS_OPERATIONS


@dataclass(frozen=True)
class StudyCondition:
    name: str
    base_harness: HarnessLevel
    operations: tuple[ModelOperation, ...]
    treatment: str
    context_mode: str = "shared"
    persistent_state: bool = False


@dataclass(frozen=True)
class StudyDefinition:
    name: str
    conditions: tuple[StudyCondition, ...]
    metrics: tuple[str, ...]
    paired_by: tuple[str, ...] = ("model", "episode", "repetition")


def _without(*excluded: ModelOperation) -> tuple[ModelOperation, ...]:
    return tuple(
        item for item in HARNESS_OPERATIONS[HarnessLevel.H2_STRONG] if item not in excluded
    )


MAIN_CONDITIONS = tuple(
    StudyCondition(
        name=harness.value,
        base_harness=harness,
        operations=HARNESS_OPERATIONS[harness],
        treatment="frozen main-matrix harness",
    )
    for harness in HarnessLevel
)

STUDIES: dict[str, StudyDefinition] = {
    "factorial": StudyDefinition(
        "factorial",
        MAIN_CONDITIONS,
        ("research_quality", "control_quality", "calls", "tokens", "latency", "cost"),
    ),
    "capstone": StudyDefinition(
        "capstone",
        MAIN_CONDITIONS,
        ("research_quality", "control_quality", "stability", "calibration", "cost"),
    ),
    "critic": StudyDefinition(
        "critic",
        (
            StudyCondition(
                "critic_off",
                HarnessLevel.H2_STRONG,
                _without(ModelOperation.CRITIQUE, ModelOperation.REVISE),
                "H2 controls held fixed; critic and critic-triggered revision disabled",
            ),
            StudyCondition(
                "critic_on",
                HarnessLevel.H2_STRONG,
                HARNESS_OPERATIONS[HarnessLevel.H2_STRONG],
                "H2 controls held fixed; critic and bounded revision enabled",
            ),
        ),
        (
            "risk_recall", "contradiction_detection", "revisions", "beneficial_revisions",
            "harmful_revisions", "false_challenges", "calls", "tokens", "latency", "cost",
        ),
    ),
    "verification": StudyDefinition(
        "verification",
        (
            StudyCondition(
                "verification_off",
                HarnessLevel.H2_STRONG,
                _without(ModelOperation.VERIFY),
                "H2 controls held fixed; final verification disabled",
            ),
            StudyCondition(
                "verification_on",
                HarnessLevel.H2_STRONG,
                HARNESS_OPERATIONS[HarnessLevel.H2_STRONG],
                "H2 controls held fixed; final verification enabled",
            ),
        ),
        (
            "research_quality", "risk_recall", "thesis_direction", "scenario_coverage",
            "unsupported_claims", "invalid_citations", "evidence_mismatch",
            "unresolved_contradictions", "untraceable_calculations", "overconfidence",
        ),
    ),
    "specialization": StudyDefinition(
        "specialization",
        (
            StudyCondition(
                "single_shared_context",
                HarnessLevel.H1_STRUCTURED,
                HARNESS_OPERATIONS[HarnessLevel.H1_STRUCTURED],
                "single-agent shared context",
            ),
            StudyCondition(
                "specialists_partitioned_context",
                HarnessLevel.H1_STRUCTURED,
                HARNESS_OPERATIONS[HarnessLevel.H1_STRUCTURED],
                "same calls with operation-specific evidence partitions",
                context_mode="partitioned",
            ),
        ),
        (
            "research_quality", "evidence_coverage", "risk_recall", "context_redundancy",
            "duplicate_work", "calls", "tokens", "cost", "latency",
        ),
    ),
    "longitudinal": StudyDefinition(
        "longitudinal",
        (
            StudyCondition(
                "stateless",
                HarnessLevel.H1_STRUCTURED,
                HARNESS_OPERATIONS[HarnessLevel.H1_STRUCTURED],
                "fresh state for each dated update",
            ),
            StudyCondition(
                "persistent_structured_state",
                HarnessLevel.H1_STRUCTURED,
                HARNESS_OPERATIONS[HarnessLevel.H1_STRUCTURED],
                "versioned state carried across five updates",
                persistent_state=True,
            ),
        ),
        (
            "update_accuracy", "confidence_change", "redundant_research", "anchoring",
            "forgetting", "stale_evidence_reuse", "revision_quality",
        ),
    ),
    "premise": StudyDefinition(
        "premise",
        MAIN_CONDITIONS,
        ("premise_acceptance", "premise_correction", "evidence_seeking", "hedging", "rationalization"),
    ),
    "counterfactual": StudyDefinition(
        "counterfactual",
        MAIN_CONDITIONS,
        ("counterfactual_consistency", "thesis_direction", "confidence_change"),
    ),
}


def get_study(name: str) -> StudyDefinition:
    return STUDIES[name]
