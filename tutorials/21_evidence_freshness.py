"""Tutorial 21: current, stale, and superseded evidence are explicit states."""

from institutional_investment_agents.hard_episodes import evidence_freshness, generate_hard_episode
from institutional_investment_agents.phase2_schemas import HardEpisodeFamily


def main() -> None:
    episode = generate_hard_episode(HardEpisodeFamily.STALE_EVIDENCE)
    for item in episode.evidence:
        status = evidence_freshness(item, as_of_date=episode.as_of_date, corpus=episode.evidence)
        print(item.id, item.version, status.value)


if __name__ == "__main__":
    main()
