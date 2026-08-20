"""Observable Phase 3 benchmark environment; hidden labels are intentionally absent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from institutional_investment_agents.phase3_config import load_json_yaml


class ObservableEpisode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    episode_id: str
    family: str
    difficulty: int
    task_instruction: str
    evidence: tuple[dict[str, Any], ...]
    available_tools: tuple[str, ...] = ()
    split: str


def load_observable_episodes(path: Any) -> tuple[ObservableEpisode, ...]:
    raw = load_json_yaml(path)
    forbidden = {
        "ground_truth_thesis_direction",
        "hidden_risk_factors",
        "required_evidence",
        "invalidation_conditions",
    }
    episodes: list[ObservableEpisode] = []
    for item in raw["episodes"]:
        leaked = forbidden.intersection(item)
        if leaked:
            raise ValueError(f"observable manifest leaks evaluator fields: {sorted(leaked)}")
        episodes.append(ObservableEpisode.model_validate(item))
    return tuple(episodes)


def research_context(episode: ObservableEpisode) -> tuple[str, ...]:
    return tuple(
        f"{item['evidence_id']} | {item['source']} | {item['text']}" for item in episode.evidence
    )
