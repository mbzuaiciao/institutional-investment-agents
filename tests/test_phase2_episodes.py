from institutional_investment_agents.hard_episodes import (
    current_evidence,
    evidence_freshness,
    generate_hard_episode,
    generate_hard_suite,
    generate_longitudinal_sequence,
)
from institutional_investment_agents.phase2_schemas import EvidenceFreshness, HardEpisodeFamily


def test_all_hard_episode_families_are_generated() -> None:
    suite = generate_hard_suite(17)
    assert len(suite) == 9
    assert {episode.family for episode in suite} == set(HardEpisodeFamily)
    assert all(episode.required_risks and episode.evidence for episode in suite)


def test_hard_episode_generation_is_seeded() -> None:
    first = generate_hard_suite(17)
    assert first == generate_hard_suite(17)
    assert first != generate_hard_suite(18)


def test_stale_and_superseded_evidence_are_classified() -> None:
    episode = generate_hard_episode(HardEpisodeFamily.STALE_EVIDENCE)
    statuses = {
        item.id: evidence_freshness(item, as_of_date=episode.as_of_date, corpus=episode.evidence)
        for item in episode.evidence
    }
    assert EvidenceFreshness.SUPERSEDED in statuses.values()
    assert EvidenceFreshness.CURRENT in statuses.values()
    assert all(
        item.id
        not in {key for key, value in statuses.items() if value != EvidenceFreshness.CURRENT}
        for item in current_evidence(episode)
    )


def test_episode_properties_surface_specific_failure_modes() -> None:
    tool = generate_hard_episode(HardEpisodeFamily.TOOL_NECESSITY)
    missing = generate_hard_episode(HardEpisodeFamily.MISSING_DATA)
    contradiction = generate_hard_episode(HardEpisodeFamily.CONTRADICTORY_EVIDENCE)
    assert tool.requires_tool
    assert missing.expected_direction == "unknown" and missing.missing_fields
    assert contradiction.has_contradiction


def test_longitudinal_sequence_has_five_ordered_updates() -> None:
    sequence = generate_longitudinal_sequence(17)
    assert len(sequence) == 5
    assert [episode.metadata["episode_number"] for episode in sequence] == [1, 2, 3, 4, 5]
    assert [episode.as_of_date for episode in sequence] == sorted(
        episode.as_of_date for episode in sequence
    )
