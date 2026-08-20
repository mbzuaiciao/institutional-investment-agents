"""Seeded synthetic model backend with systematic, profile-driven failure injection."""

from __future__ import annotations

import random
from dataclasses import dataclass

from institutional_investment_agents.phase2_schemas import (
    ConfidenceComponents,
    FailureType,
    ModelFailure,
    ModelOperation,
    ModelProfile,
    ModelRequest,
    ModelResponse,
)

MODEL_PROFILES: dict[str, ModelProfile] = {
    "weak": ModelProfile(
        name="weak",
        strength=0,
        reasoning_accuracy=0.62,
        retrieval_interpretation_accuracy=0.64,
        tool_selection_accuracy=0.66,
        arithmetic_without_tool_accuracy=0.55,
        contradiction_detection=0.52,
        risk_recall=0.58,
        citation_fidelity=0.62,
        revision_responsiveness=0.56,
        structured_output_fidelity=0.72,
        confidence_calibration=0.55,
    ),
    "medium": ModelProfile(
        name="medium",
        strength=1,
        reasoning_accuracy=0.80,
        retrieval_interpretation_accuracy=0.82,
        tool_selection_accuracy=0.84,
        arithmetic_without_tool_accuracy=0.74,
        contradiction_detection=0.73,
        risk_recall=0.76,
        citation_fidelity=0.81,
        revision_responsiveness=0.78,
        structured_output_fidelity=0.88,
        confidence_calibration=0.75,
    ),
    "strong": ModelProfile(
        name="strong",
        strength=2,
        reasoning_accuracy=0.94,
        retrieval_interpretation_accuracy=0.95,
        tool_selection_accuracy=0.96,
        arithmetic_without_tool_accuracy=0.90,
        contradiction_detection=0.91,
        risk_recall=0.92,
        citation_fidelity=0.95,
        revision_responsiveness=0.93,
        structured_output_fidelity=0.97,
        confidence_calibration=0.91,
    ),
}


@dataclass(frozen=True)
class ErrorCandidate:
    failure_type: FailureType
    capability: str
    scale: float


OPERATION_ERRORS: dict[ModelOperation, tuple[ErrorCandidate, ...]] = {
    ModelOperation.PLAN: (
        ErrorCandidate(FailureType.EVIDENCE_OMISSION, "reasoning_accuracy", 0.75),
        ErrorCandidate(FailureType.MALFORMED_OUTPUT, "structured_output_fidelity", 0.60),
    ),
    ModelOperation.EXECUTE_TASK: (
        ErrorCandidate(FailureType.EVIDENCE_OMISSION, "reasoning_accuracy", 0.65),
        ErrorCandidate(FailureType.MISSED_RISK, "risk_recall", 0.75),
    ),
    ModelOperation.ROUTE: (ErrorCandidate(FailureType.ROUTING_ERROR, "reasoning_accuracy", 0.80),),
    ModelOperation.RETRIEVE: (
        ErrorCandidate(FailureType.RETRIEVAL_MISS, "retrieval_interpretation_accuracy", 0.90),
        ErrorCandidate(FailureType.STALE_EVIDENCE, "retrieval_interpretation_accuracy", 0.55),
    ),
    ModelOperation.INTERPRET_EVIDENCE: (
        ErrorCandidate(FailureType.EVIDENCE_OMISSION, "retrieval_interpretation_accuracy", 0.80),
        ErrorCandidate(FailureType.IGNORED_CONTRADICTION, "contradiction_detection", 0.90),
    ),
    ModelOperation.SELECT_TOOL: (
        ErrorCandidate(FailureType.INCORRECT_TOOL, "tool_selection_accuracy", 0.75),
        ErrorCandidate(FailureType.MISSED_TOOL, "tool_selection_accuracy", 0.65),
        ErrorCandidate(FailureType.DUPLICATE_TOOL, "tool_selection_accuracy", 0.35),
        ErrorCandidate(FailureType.ARITHMETIC_ERROR, "arithmetic_without_tool_accuracy", 0.55),
    ),
    ModelOperation.GENERATE_CLAIMS: (
        ErrorCandidate(FailureType.UNSUPPORTED_CLAIM, "reasoning_accuracy", 0.85),
        ErrorCandidate(FailureType.CITATION_MISMATCH, "citation_fidelity", 0.90),
        ErrorCandidate(FailureType.MALFORMED_OUTPUT, "structured_output_fidelity", 0.60),
        ErrorCandidate(FailureType.INCORRECT_CONFIDENCE, "confidence_calibration", 0.65),
        ErrorCandidate(FailureType.OVERCONFIDENT_UNSUPPORTED, "confidence_calibration", 0.45),
    ),
    ModelOperation.SYNTHESIZE: (
        ErrorCandidate(FailureType.PREMATURE_SYNTHESIS, "reasoning_accuracy", 0.70),
        ErrorCandidate(FailureType.MISSED_RISK, "risk_recall", 0.80),
        ErrorCandidate(FailureType.IGNORED_CONTRADICTION, "contradiction_detection", 0.75),
        ErrorCandidate(FailureType.INCORRECT_CONFIDENCE, "confidence_calibration", 0.50),
    ),
    ModelOperation.CRITIQUE: (
        ErrorCandidate(FailureType.MISSED_RISK, "risk_recall", 0.60),
        ErrorCandidate(FailureType.IGNORED_CONTRADICTION, "contradiction_detection", 0.65),
        ErrorCandidate(FailureType.FALSE_CHALLENGE, "reasoning_accuracy", 0.35),
    ),
    ModelOperation.REVISE: (
        ErrorCandidate(FailureType.FAILED_REVISION, "revision_responsiveness", 0.90),
        ErrorCandidate(FailureType.MALFORMED_OUTPUT, "structured_output_fidelity", 0.35),
    ),
    ModelOperation.VERIFY: (
        ErrorCandidate(FailureType.CITATION_MISMATCH, "citation_fidelity", 0.40),
        ErrorCandidate(FailureType.IGNORED_CONTRADICTION, "contradiction_detection", 0.40),
    ),
}


TOKEN_UNITS: dict[ModelOperation, int] = {
    ModelOperation.PLAN: 180,
    ModelOperation.EXECUTE_TASK: 260,
    ModelOperation.ROUTE: 60,
    ModelOperation.RETRIEVE: 90,
    ModelOperation.INTERPRET_EVIDENCE: 220,
    ModelOperation.SELECT_TOOL: 80,
    ModelOperation.GENERATE_CLAIMS: 240,
    ModelOperation.SYNTHESIZE: 320,
    ModelOperation.CRITIQUE: 220,
    ModelOperation.REVISE: 180,
    ModelOperation.VERIFY: 160,
}


def get_model_profile(name: str) -> ModelProfile:
    try:
        return MODEL_PROFILES[name]
    except KeyError as error:
        raise KeyError(f"unknown model profile: {name}") from error


class StochasticSyntheticModel:
    """A causal simulator: profile capabilities determine seeded failure probabilities."""

    def __init__(self, profile: ModelProfile | str = "medium", *, seed: int = 17) -> None:
        self.profile = get_model_profile(profile) if isinstance(profile, str) else profile
        self.seed = seed
        self._rng = random.Random(seed)
        self.call_count = 0

    def chance(self, probability: float) -> bool:
        """Draw a seeded Bernoulli outcome for runner-level research behavior."""
        bounded = min(1.0, max(0.0, probability))
        return self._rng.random() < bounded

    def generate(self, prompt: str, *, context: tuple[str, ...] = ()) -> str:
        material = " ".join(context)
        return f"[{self.profile.name} synthetic model] {prompt}: {material[:240]}"

    def execute(self, request: ModelRequest) -> ModelResponse:
        self.call_count += 1
        failures: list[ModelFailure] = []
        for candidate in OPERATION_ERRORS.get(request.operation, ()):
            accuracy = float(getattr(self.profile, candidate.capability))
            if self.chance((1.0 - accuracy) * candidate.scale):
                failures.append(
                    ModelFailure(
                        failure_type=candidate.failure_type,
                        operation=request.operation,
                        detail=(
                            f"{self.profile.name} profile injected {candidate.failure_type.value} "
                            f"during {request.operation.value}"
                        ),
                    )
                )
        confidence = self._confidence(request.operation, failures)
        token_units = TOKEN_UNITS[request.operation]
        return ModelResponse(
            operation=request.operation,
            structured_output={
                "episode_id": request.episode_id,
                "operation": request.operation.value,
                "status": "degraded" if failures else "complete",
            },
            failures=tuple(failures),
            confidence=confidence,
            usage={"simulated_token_units": token_units, "model_calls": 1},
        )

    def _confidence(
        self, operation: ModelOperation, failures: list[ModelFailure]
    ) -> ConfidenceComponents:
        profile = self.profile
        penalty = min(0.25, len(failures) * 0.07)
        judgment = max(0.05, profile.reasoning_accuracy - penalty)
        consistency = max(0.05, profile.contradiction_detection - penalty)
        overall = (
            profile.retrieval_interpretation_accuracy
            + profile.tool_selection_accuracy
            + consistency
            + judgment
        ) / 4
        if any(item.failure_type == FailureType.INCORRECT_CONFIDENCE for item in failures):
            overall = min(1.0, overall + (1.0 - profile.confidence_calibration) * 0.35)
        calculation = (
            profile.tool_selection_accuracy
            if operation == ModelOperation.SELECT_TOOL
            else profile.arithmetic_without_tool_accuracy
        )
        return ConfidenceComponents(
            evidence=round(profile.citation_fidelity, 4),
            calculation=round(calculation, 4),
            retrieval=round(profile.retrieval_interpretation_accuracy, 4),
            consistency=round(consistency, 4),
            model_judgment=round(judgment, 4),
            overall=round(min(1.0, max(0.0, overall)), 4),
        )
