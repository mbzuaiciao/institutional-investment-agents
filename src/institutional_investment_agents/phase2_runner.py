"""Controlled Phase 2 episode runner separating model errors from harness controls."""

from __future__ import annotations

import random
from collections import Counter

from institutional_investment_agents.hard_episodes import evidence_freshness
from institutional_investment_agents.phase2_schemas import (
    ConfidenceComponents,
    CostAccount,
    EvidenceFreshness,
    FailureOrigin,
    FailureType,
    HardResearchEpisode,
    HarnessProfile,
    ModelFailure,
    ModelOperation,
    ModelRequest,
    Phase2Metrics,
    Phase2Run,
)
from institutional_investment_agents.stochastic_model import StochasticSyntheticModel

BASE_OPERATIONS = (
    ModelOperation.EXECUTE_TASK,
    ModelOperation.RETRIEVE,
    ModelOperation.GENERATE_CLAIMS,
    ModelOperation.SYNTHESIZE,
)

STRUCTURED_OPERATIONS = (
    ModelOperation.PLAN,
    ModelOperation.ROUTE,
    ModelOperation.RETRIEVE,
    ModelOperation.INTERPRET_EVIDENCE,
    ModelOperation.EXECUTE_TASK,
    ModelOperation.GENERATE_CLAIMS,
    ModelOperation.SYNTHESIZE,
)


def run_phase2_episode(
    model: StochasticSyntheticModel,
    harness: HarnessProfile,
    episode: HardResearchEpisode,
    *,
    seed: int,
) -> Phase2Run:
    """Run one episode; injected errors precede deterministic harness mitigation."""
    cost = CostAccount()
    injected: list[ModelFailure] = []
    detected: set[FailureType] = set()
    responses = []
    operations: list[ModelOperation] = list(
        STRUCTURED_OPERATIONS if harness.explicit_plan else BASE_OPERATIONS
    )
    if episode.requires_tool:
        operations.insert(-2, ModelOperation.SELECT_TOOL)

    for operation in operations:
        request = ModelRequest(
            operation=operation,
            episode_id=episode.id,
            instruction=f"Perform {operation.value} for {episode.family.value}",
            context=tuple(item.text for item in episode.evidence),
            available_tools=("credit_ratios", "portfolio_impact") if episode.requires_tool else (),
            required_schema="Phase2ResearchContribution" if harness.evidence_ids else None,
        )
        response = model.execute(request)
        responses.append(response)
        injected.extend(response.failures)
        token_units = int(response.usage.get("simulated_token_units", 0))
        cost.record_model_call(operation, token_units)
        if operation == ModelOperation.RETRIEVE:
            cost.retrieval_operations += 1
        elif operation == ModelOperation.SELECT_TOOL:
            cost.tool_calls += 1

    # Episode-specific draws convert profile capabilities into observable research failures.
    found_risks = 0
    risk_probability = model.profile.risk_recall
    if harness.explicit_plan:
        risk_probability += (1.0 - risk_probability) * 0.16
    if harness.specialist_partitioning and episode.complexity >= 4:
        risk_probability += (1.0 - risk_probability) * 0.22
    for risk in episode.required_risks:
        if model.chance(risk_probability):
            found_risks += 1
        else:
            injected.append(
                _failure(FailureType.MISSED_RISK, ModelOperation.SYNTHESIZE, f"missed {risk}")
            )

    contradiction_detected = not episode.has_contradiction or model.chance(
        model.profile.contradiction_detection + (0.08 if harness.explicit_plan else 0.0)
    )
    if not contradiction_detected:
        injected.append(
            _failure(
                FailureType.IGNORED_CONTRADICTION,
                ModelOperation.INTERPRET_EVIDENCE,
                "failed to reconcile conflicting episode signals",
            )
        )

    calculation_correct = True
    if episode.requires_tool:
        tool_selected = model.chance(model.profile.tool_selection_accuracy)
        if tool_selected:
            calculation_correct = harness.typed_tools or model.chance(
                model.profile.arithmetic_without_tool_accuracy
            )
        else:
            injected.append(
                _failure(
                    FailureType.MISSED_TOOL,
                    ModelOperation.SELECT_TOOL,
                    "required quantitative tool was not selected",
                )
            )
            calculation_correct = model.chance(model.profile.arithmetic_without_tool_accuracy)
        if not calculation_correct:
            injected.append(
                _failure(
                    FailureType.ARITHMETIC_ERROR,
                    ModelOperation.SELECT_TOOL,
                    "scenario calculation was incorrect",
                )
            )

    claim_count = episode.complexity + 2
    unsupported = sum(
        not model.chance(model.profile.reasoning_accuracy) for _ in range(claim_count)
    )
    invalid_citations = sum(
        not model.chance(model.profile.citation_fidelity) for _ in range(claim_count)
    )
    if harness.evidence_ids:
        unsupported = sum(model.chance(0.30) for _ in range(unsupported))
        invalid_citations = sum(model.chance(0.38) for _ in range(invalid_citations))
    injected.extend(
        _failure(
            FailureType.UNSUPPORTED_CLAIM,
            ModelOperation.GENERATE_CLAIMS,
            f"unsupported claim {index + 1}",
        )
        for index in range(unsupported)
    )
    injected.extend(
        _failure(
            FailureType.CITATION_MISMATCH,
            ModelOperation.GENERATE_CLAIMS,
            f"citation mismatch {index + 1}",
        )
        for index in range(invalid_citations)
    )

    stale_candidates = [
        item
        for item in episode.evidence
        if evidence_freshness(item, as_of_date=episode.as_of_date, corpus=episode.evidence)
        != EvidenceFreshness.CURRENT
    ]
    stale_used = 0
    for item in stale_candidates:
        probability = 1.0 - model.profile.retrieval_interpretation_accuracy
        if not harness.evidence_ids:
            probability += 0.35
        if harness.stale_evidence_exclusion:
            probability = 0.0
            detected.add(FailureType.STALE_EVIDENCE)
        if model.chance(probability):
            stale_used += 1
            injected.append(
                _failure(
                    FailureType.STALE_EVIDENCE,
                    ModelOperation.RETRIEVE,
                    f"used stale or superseded evidence {item.id}",
                )
            )

    inappropriate_confidence = int(
        not model.chance(model.profile.confidence_calibration)
        or any(item.failure_type == FailureType.OVERCONFIDENT_UNSUPPORTED for item in injected)
    )
    if inappropriate_confidence:
        injected.append(
            _failure(
                FailureType.INCORRECT_CONFIDENCE,
                ModelOperation.SYNTHESIZE,
                "confidence did not reflect unresolved support errors",
            )
        )

    unresolved = list(injected)
    # Structured constraints prevent specific failures from propagating.
    if harness.deterministic_routing:
        _resolve_all(unresolved, detected, FailureType.ROUTING_ERROR)
    if harness.explicit_plan:
        _resolve_all(unresolved, detected, FailureType.PREMATURE_SYNTHESIS)
        _resolve_all(unresolved, detected, FailureType.MALFORMED_OUTPUT)
    if harness.typed_tools and calculation_correct:
        _resolve_all(unresolved, detected, FailureType.ARITHMETIC_ERROR)

    false_challenges = sum(item.failure_type == FailureType.FALSE_CHALLENGE for item in unresolved)
    revisions = 0
    correct_revisions = 0
    unnecessary_revisions = 0

    if harness.critic:
        critic_response = model.execute(
            ModelRequest(
                operation=ModelOperation.CRITIQUE,
                episode_id=episode.id,
                instruction="Challenge the base thesis and identify omitted risks",
                context=tuple(item.text for item in episode.evidence),
                required_schema="Challenge",
            )
        )
        responses.append(critic_response)
        injected.extend(critic_response.failures)
        unresolved.extend(
            item
            for item in critic_response.failures
            if item.failure_type == FailureType.FALSE_CHALLENGE
        )
        cost.record_model_call(
            ModelOperation.CRITIQUE,
            int(critic_response.usage.get("simulated_token_units", 0)),
        )
        false_challenges = sum(
            item.failure_type == FailureType.FALSE_CHALLENGE for item in unresolved
        )
        missing = len(episode.required_risks) - found_risks
        for _ in range(missing):
            recovery_probability = 0.40 + 0.45 * model.profile.contradiction_detection
            if model.chance(recovery_probability):
                found_risks += 1
                correct_revisions += 1
                detected.add(FailureType.MISSED_RISK)
                _resolve_one(unresolved, FailureType.MISSED_RISK)
        if (
            episode.has_contradiction
            and not contradiction_detected
            and model.chance(0.45 + 0.45 * model.profile.contradiction_detection)
        ):
            contradiction_detected = True
            correct_revisions += 1
            detected.add(FailureType.IGNORED_CONTRADICTION)
            _resolve_all(unresolved, detected, FailureType.IGNORED_CONTRADICTION)

    if harness.verifier:
        verifier_response = model.execute(
            ModelRequest(
                operation=ModelOperation.VERIFY,
                episode_id=episode.id,
                instruction="Check claim support, citations, confidence, and contradictions",
                context=tuple(item.text for item in episode.evidence),
                required_schema="VerificationResult",
            )
        )
        responses.append(verifier_response)
        injected.extend(verifier_response.failures)
        cost.record_model_call(
            ModelOperation.VERIFY,
            int(verifier_response.usage.get("simulated_token_units", 0)),
        )
        for failure_type in (
            FailureType.UNSUPPORTED_CLAIM,
            FailureType.CITATION_MISMATCH,
            FailureType.INCORRECT_CONFIDENCE,
        ):
            if any(item.failure_type == failure_type for item in unresolved):
                detected.add(failure_type)
        repairable = [
            item
            for item in unresolved
            if item.failure_type
            in {
                FailureType.UNSUPPORTED_CLAIM,
                FailureType.CITATION_MISMATCH,
                FailureType.INCORRECT_CONFIDENCE,
            }
        ]
        if repairable and harness.revision_loop:
            revisions = 1
            revision = model.execute(
                ModelRequest(
                    operation=ModelOperation.REVISE,
                    episode_id=episode.id,
                    instruction="Revise claims flagged by deterministic verification",
                    required_schema="VerifiedResearchContribution",
                )
            )
            responses.append(revision)
            injected.extend(revision.failures)
            unresolved.extend(revision.failures)
            cost.record_model_call(
                ModelOperation.REVISE,
                int(revision.usage.get("simulated_token_units", 0)),
            )
            revision_failed = any(
                item.failure_type == FailureType.FAILED_REVISION for item in revision.failures
            )
            if not revision_failed and model.chance(model.profile.revision_responsiveness):
                for item in repairable:
                    if item in unresolved:
                        unresolved.remove(item)
                        correct_revisions += 1
                unsupported = 0
                invalid_citations = 0
                inappropriate_confidence = 0
        elif harness.revision_loop and false_challenges and model.chance(0.25):
            revisions = 1
            unnecessary_revisions = 1

    unresolved_counts = Counter(item.failure_type for item in unresolved)
    unsupported = unresolved_counts[FailureType.UNSUPPORTED_CLAIM]
    invalid_citations = unresolved_counts[FailureType.CITATION_MISMATCH]
    unresolved_contradictions = int(
        episode.has_contradiction
        and (not contradiction_detected or unresolved_counts[FailureType.IGNORED_CONTRADICTION] > 0)
    )
    stale_used = unresolved_counts[FailureType.STALE_EVIDENCE]
    inappropriate_confidence = int(
        unresolved_counts[FailureType.INCORRECT_CONFIDENCE] > 0
        or unresolved_counts[FailureType.OVERCONFIDENT_UNSUPPORTED] > 0
    )

    risk_recall = found_risks / len(episode.required_risks)
    support_rate = max(0.0, 1.0 - unsupported / claim_count)
    citation_validity = max(0.0, 1.0 - invalid_citations / claim_count)
    stale_rate = min(1.0, stale_used / len(stale_candidates)) if stale_candidates else 0.0
    contradiction_score = float(not unresolved_contradictions)
    direction_probability = model.profile.reasoning_accuracy
    if harness.explicit_plan:
        direction_probability += (1.0 - direction_probability) * 0.18
    if risk_recall < 0.5:
        direction_probability -= 0.12
    if unresolved_contradictions:
        direction_probability -= 0.15
    if not calculation_correct:
        direction_probability -= 0.12
    directional_accuracy = float(
        _paired_chance(model.seed, episode.id, "direction", direction_probability)
    )

    quality = 100 * (
        0.22 * directional_accuracy
        + 0.22 * risk_recall
        + 0.12 * contradiction_score
        + 0.14 * float(calculation_correct)
        + 0.15 * support_rate
        + 0.10 * citation_validity
        + 0.05 * (1.0 - stale_rate)
    )
    control_quality = 100 * (
        0.30 * support_rate
        + 0.25 * citation_validity
        + 0.20 * contradiction_score
        + 0.15 * (1.0 - stale_rate)
        + 0.10 * float(harness.approval_gate)
    )
    if harness.audit_trace:
        cost.workflow_steps += 2
    if harness.approval_gate:
        cost.workflow_steps += 1
    if any(item.failure_type == FailureType.DUPLICATE_TOOL for item in injected):
        cost.tool_calls += 1

    confidence = _aggregate_confidence(responses, inappropriate_confidence)
    metrics = Phase2Metrics(
        research_quality_score=round(quality, 4),
        directional_accuracy=directional_accuracy,
        risk_factor_recall=round(risk_recall, 4),
        contradiction_detection=contradiction_score,
        calculation_accuracy=float(calculation_correct),
        claim_support_rate=round(support_rate, 4),
        citation_validity=round(citation_validity, 4),
        stale_evidence_usage_rate=round(stale_rate, 4),
        inappropriate_confidence_rate=float(inappropriate_confidence),
        unsupported_claims=unsupported,
        invalid_citations=invalid_citations,
        unresolved_contradictions=unresolved_contradictions,
        revisions=revisions,
        correct_revisions=correct_revisions,
        unnecessary_revisions=unnecessary_revisions,
        false_challenges=false_challenges,
        control_quality_score=round(control_quality, 4),
    )
    return Phase2Run(
        run_id=f"{model.profile.name}-{harness.name.value}-{episode.id}-{seed}",
        seed=seed,
        model_profile=model.profile.name,
        harness_profile=harness.name,
        episode_id=episode.id,
        episode_family=episode.family,
        metrics=metrics,
        confidence=confidence,
        cost=cost,
        injected_failures=tuple(injected),
        unresolved_failures=tuple(unresolved),
        detected_failures=tuple(sorted(detected, key=str)),
    )


def _failure(
    failure_type: FailureType,
    operation: ModelOperation,
    detail: str,
) -> ModelFailure:
    return ModelFailure(
        failure_type=failure_type,
        operation=operation,
        detail=detail,
        origin=FailureOrigin.MODEL,
    )


def _paired_chance(seed: int, episode_id: str, key: str, probability: float) -> bool:
    bounded = min(1.0, max(0.0, probability))
    return random.Random(f"{seed}:{episode_id}:{key}").random() < bounded


def _resolve_all(
    unresolved: list[ModelFailure],
    detected: set[FailureType],
    failure_type: FailureType,
) -> None:
    if any(item.failure_type == failure_type for item in unresolved):
        detected.add(failure_type)
    unresolved[:] = [item for item in unresolved if item.failure_type != failure_type]


def _resolve_one(unresolved: list[ModelFailure], failure_type: FailureType) -> None:
    for index, item in enumerate(unresolved):
        if item.failure_type == failure_type:
            unresolved.pop(index)
            return


def _aggregate_confidence(
    responses: list,
    inappropriate_confidence: int,
) -> ConfidenceComponents:
    if not responses:
        return ConfidenceComponents(
            evidence=0.0,
            calculation=0.0,
            retrieval=0.0,
            consistency=0.0,
            model_judgment=0.0,
            overall=0.0,
        )
    fields = ("evidence", "calculation", "retrieval", "consistency", "model_judgment")
    averages = {
        field: sum(float(getattr(response.confidence, field)) for response in responses)
        / len(responses)
        for field in fields
    }
    overall = sum(averages.values()) / len(averages)
    if inappropriate_confidence:
        overall = min(1.0, overall + 0.08)
    return ConfidenceComponents(
        evidence=round(averages["evidence"], 4),
        calculation=round(averages["calculation"], 4),
        retrieval=round(averages["retrieval"], 4),
        consistency=round(averages["consistency"], 4),
        model_judgment=round(averages["model_judgment"], 4),
        overall=round(overall, 4),
    )
