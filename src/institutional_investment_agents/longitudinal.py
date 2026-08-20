"""Multi-episode credit research benchmark where structured memory can matter."""

from __future__ import annotations

from institutional_investment_agents.hard_episodes import generate_longitudinal_sequence
from institutional_investment_agents.phase2_schemas import (
    CostAccount,
    LongitudinalMetrics,
    LongitudinalRun,
    LongitudinalState,
    ModelOperation,
)
from institutional_investment_agents.stochastic_model import StochasticSyntheticModel


def run_longitudinal_research(
    model_profile: str,
    *,
    persistent: bool,
    seed: int,
) -> LongitudinalRun:
    """Run five dated updates with or without versioned cross-episode state."""
    model = StochasticSyntheticModel(model_profile, seed=seed)
    sequence = generate_longitudinal_sequence(seed)
    state = LongitudinalState(
        issuer_id="P2-LONG",
        assumptions=["refinancing access remains available"],
        invalidation_conditions=["EBITDA declines more than 10%"],
    )
    cost = CostAccount()
    quality_by_episode: list[float] = []
    update_correct = 0
    consistent = 0
    revisions_required = 0
    revisions_correct = 0
    forgetting_events = 0
    anchoring_events = 0
    stale_uses = 0
    stale_opportunities = 0
    redundant_research = 0
    previous_direction: str | None = None

    for index, episode in enumerate(sequence):
        cost.record_model_call(ModelOperation.INTERPRET_EVIDENCE, 220)
        cost.record_model_call(ModelOperation.SYNTHESIZE, 320)
        cost.retrieval_operations += 1
        if persistent:
            redundant_research += 2 if index == 0 else 1
            context_boost = 0.13 if index > 0 else 0.0
        else:
            redundant_research += 3
            context_boost = 0.0
            if index > 0 and model.chance(0.72):
                forgetting_events += 1

        changed = (
            previous_direction is not None and episode.expected_direction != previous_direction
        )
        if changed:
            revisions_required += 1
        anchoring = False
        if persistent and changed:
            anchoring_probability = (1.0 - model.profile.revision_responsiveness) * 0.55
            anchoring = model.chance(anchoring_probability)
            anchoring_events += int(anchoring)

        probability = min(0.99, model.profile.reasoning_accuracy + context_boost)
        if anchoring:
            probability -= 0.35
        correct = model.chance(probability)
        update_correct += int(correct)
        if changed and correct:
            revisions_correct += 1
        if (
            previous_direction is None
            or correct
            or episode.expected_direction == previous_direction
        ):
            consistent += 1

        if persistent and index > 0:
            stale_opportunities += len(state.evidence_versions)
            # Version-aware state excludes superseded evidence before synthesis.
            stale_uses += 0
        elif not persistent and index > 0:
            stale_opportunities += 1
            stale_uses += int(
                model.chance(0.12 * (1.0 - model.profile.retrieval_interpretation_accuracy))
            )

        episode_quality = 100 * (
            0.55 * float(correct)
            + 0.20 * (1.0 - float(anchoring))
            + 0.15 * (1.0 if persistent or index == 0 else 0.65)
            + 0.10 * (1.0 if stale_uses == 0 else 0.0)
        )
        quality_by_episode.append(round(episode_quality, 2))

        evidence = episode.evidence[0]
        if persistent:
            if evidence.supersedes_id:
                state.evidence_versions.pop(evidence.supersedes_id, None)
            state.evidence_versions[evidence.id] = evidence
            thesis = episode.expected_direction if correct else (previous_direction or "unknown")
            state.prior_thesis = thesis
            state.thesis_history.append(thesis)
            state.confidence_history.append(round(model.profile.reasoning_accuracy, 4))
            if index == 1 and "EBITDA declines more than 10%" in state.invalidation_conditions:
                state.unresolved_questions.append(
                    "Can refinancing access offset the EBITDA breach?"
                )
        previous_direction = episode.expected_direction

    count = len(sequence)
    revision_quality = revisions_correct / revisions_required if revisions_required else 1.0
    metrics = LongitudinalMetrics(
        update_accuracy=round(update_correct / count, 4),
        consistency=round(consistent / count, 4),
        stale_evidence_usage_rate=round(
            stale_uses / stale_opportunities if stale_opportunities else 0.0, 4
        ),
        redundant_research_operations=redundant_research,
        revision_quality=round(revision_quality, 4),
        forgetting_rate=round(forgetting_events / max(1, count - 1), 4),
        anchoring_rate=round(anchoring_events / max(1, revisions_required), 4),
        quality_by_episode=tuple(quality_by_episode),
    )
    return LongitudinalRun(
        seed=seed,
        model_profile=model_profile,
        persistent=persistent,
        metrics=metrics,
        cost=cost,
    )
