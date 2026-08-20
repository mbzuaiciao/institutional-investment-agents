"""Optional one-episode smoke runner for an OpenAI-compatible real model backend."""

import argparse

from institutional_investment_agents.adapters import OpenAICompatibleAdapter
from institutional_investment_agents.hard_episodes import generate_hard_episode
from institutional_investment_agents.harness import get_harness_profile
from institutional_investment_agents.phase2_schemas import (
    HardEpisodeFamily,
    ModelOperation,
    ModelRequest,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("openai-compatible",), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--harness", choices=("weak", "structured", "strong"), default="strong")
    parser.add_argument(
        "--family",
        choices=tuple(item.value for item in HardEpisodeFamily),
        default=HardEpisodeFamily.CONTRADICTORY_EVIDENCE.value,
    )
    args = parser.parse_args()
    harness = get_harness_profile(args.harness)
    episode = generate_hard_episode(args.family)
    backend = OpenAICompatibleAdapter(model=args.model)
    response = backend.execute(
        ModelRequest(
            operation=ModelOperation.SYNTHESIZE,
            episode_id=episode.id,
            instruction=f"Synthesize a thesis under {harness.name.value} controls.",
            context=tuple(item.text for item in episode.evidence),
            required_schema="ResearchContribution",
        )
    )
    print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
