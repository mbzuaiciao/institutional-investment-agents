"""Observable five-update sequence for the Phase 3 memory replication."""

from __future__ import annotations

from institutional_investment_agents.hard_episodes import generate_longitudinal_sequence
from institutional_investment_agents.phase3_benchmark import ObservableEpisode


def observable_longitudinal_sequence(seed: int = 17) -> tuple[ObservableEpisode, ...]:
    episodes: list[ObservableEpisode] = []
    for index, source in enumerate(generate_longitudinal_sequence(seed), start=1):
        evidence = tuple(
            {
                "evidence_id": item.id,
                "source": item.source,
                "text": item.text,
                "published_date": item.published_date,
                "valid_until": item.valid_until,
                "supersedes_id": item.supersedes_id,
            }
            for item in source.evidence
        )
        episodes.append(
            ObservableEpisode(
                episode_id=source.id,
                family=f"longitudinal_update_{index}",
                difficulty=source.complexity,
                task_instruction=(
                    "Update the issuer thesis, confidence, invalidation conditions, and unresolved "
                    "questions using this dated evidence version."
                ),
                evidence=evidence,
                available_tools=(),
                split="evaluation",
            )
        )
    return tuple(episodes)
