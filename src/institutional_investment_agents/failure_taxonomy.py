"""Machine-readable attribution taxonomy for Phase 2 failures."""

from __future__ import annotations

from dataclasses import dataclass

from institutional_investment_agents.phase2_schemas import FailureOrigin, FailureType


@dataclass(frozen=True)
class FailureDefinition:
    meaning: str
    detection: str
    origin: FailureOrigin
    metrics: tuple[str, ...]


FAILURE_TAXONOMY: dict[FailureType, FailureDefinition] = {
    FailureType.RETRIEVAL_MISS: FailureDefinition(
        "Relevant evidence was not retrieved.",
        "Compare retrieved IDs with episode-relevant evidence.",
        FailureOrigin.BOTH,
        ("evidence_coverage",),
    ),
    FailureType.EVIDENCE_OMISSION: FailureDefinition(
        "Available relevant evidence was omitted from reasoning.",
        "Compare claim lineage with required evidence.",
        FailureOrigin.MODEL,
        ("risk_factor_recall", "claim_support_rate"),
    ),
    FailureType.ROUTING_ERROR: FailureDefinition(
        "A task was assigned to the wrong capability or role.",
        "Compare route with deterministic task requirements.",
        FailureOrigin.BOTH,
        ("routing_accuracy",),
    ),
    FailureType.INCORRECT_TOOL: FailureDefinition(
        "The selected tool cannot answer the required calculation.",
        "Validate tool contract against episode requirement.",
        FailureOrigin.MODEL,
        ("calculation_accuracy", "tool_calls"),
    ),
    FailureType.MISSED_TOOL: FailureDefinition(
        "A required deterministic calculation was attempted without its tool.",
        "Check required-tool flag against calls.",
        FailureOrigin.BOTH,
        ("calculation_accuracy",),
    ),
    FailureType.DUPLICATE_TOOL: FailureDefinition(
        "The same calculation was called without new inputs.",
        "Compare tool names and normalized arguments.",
        FailureOrigin.MODEL,
        ("tool_calls", "simulated_cost_units"),
    ),
    FailureType.ARITHMETIC_ERROR: FailureDefinition(
        "A quantitative result is incorrect.",
        "Compare with deterministic tool ground truth.",
        FailureOrigin.MODEL,
        ("calculation_accuracy",),
    ),
    FailureType.PREMATURE_SYNTHESIS: FailureDefinition(
        "The thesis was formed before required tasks completed.",
        "Inspect plan completion at synthesis event.",
        FailureOrigin.BOTH,
        ("task_completion",),
    ),
    FailureType.IGNORED_CONTRADICTION: FailureDefinition(
        "Conflicting evidence was not surfaced or reconciled.",
        "Compare contradiction labels with state and thesis.",
        FailureOrigin.BOTH,
        ("contradiction_detection", "unresolved_contradictions"),
    ),
    FailureType.UNSUPPORTED_CLAIM: FailureDefinition(
        "A claim has no valid evidence or calculation lineage.",
        "Run deterministic support verification.",
        FailureOrigin.BOTH,
        ("unsupported_claims", "claim_support_rate"),
    ),
    FailureType.CITATION_MISMATCH: FailureDefinition(
        "A citation exists but does not support its claim.",
        "Compare cited evidence with required support.",
        FailureOrigin.BOTH,
        ("invalid_citations", "citation_validity"),
    ),
    FailureType.MISSED_RISK: FailureDefinition(
        "A ground-truth risk factor is absent from the thesis.",
        "Compare thesis risks with episode labels.",
        FailureOrigin.MODEL,
        ("risk_factor_recall",),
    ),
    FailureType.MALFORMED_OUTPUT: FailureDefinition(
        "Output violates the requested structured schema.",
        "Apply schema validation.",
        FailureOrigin.BOTH,
        ("structured_output_validity",),
    ),
    FailureType.STALE_EVIDENCE: FailureDefinition(
        "Expired or superseded evidence influences the current conclusion.",
        "Apply evidence freshness classification and inspect lineage.",
        FailureOrigin.BOTH,
        ("stale_evidence_usage_rate",),
    ),
    FailureType.FAILED_REVISION: FailureDefinition(
        "A detected issue remains after a requested revision.",
        "Compare pre/post revision failures.",
        FailureOrigin.MODEL,
        ("correct_revisions", "revision_cycles"),
    ),
    FailureType.INCORRECT_CONFIDENCE: FailureDefinition(
        "Heuristic confidence is inconsistent with known errors.",
        "Compare confidence components with unresolved failures.",
        FailureOrigin.MODEL,
        ("inappropriate_confidence_rate",),
    ),
    FailureType.OVERCONFIDENT_UNSUPPORTED: FailureDefinition(
        "An unsupported claim is expressed with excessive confidence.",
        "Join support results with claim confidence.",
        FailureOrigin.MODEL,
        ("inappropriate_confidence_rate", "unsupported_claims"),
    ),
    FailureType.FALSE_CHALLENGE: FailureDefinition(
        "Critique raises an issue not supported by episode ground truth.",
        "Compare challenges with risk and contradiction labels.",
        FailureOrigin.BOTH,
        ("false_challenges", "unnecessary_revisions"),
    ),
    FailureType.MEMORY_FAILURE: FailureDefinition(
        "Prior state is forgotten, stale, or incorrectly anchors an update.",
        "Compare longitudinal state with episode history.",
        FailureOrigin.BOTH,
        ("forgetting_rate", "anchoring_rate", "revision_quality"),
    ),
}


def classify_failure(failure_type: FailureType) -> FailureDefinition:
    return FAILURE_TAXONOMY[failure_type]
