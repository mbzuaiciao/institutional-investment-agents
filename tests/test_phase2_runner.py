from institutional_investment_agents.failure_taxonomy import FAILURE_TAXONOMY, classify_failure
from institutional_investment_agents.hard_episodes import generate_hard_episode
from institutional_investment_agents.harness import HARNESS_PROFILES, get_harness_profile
from institutional_investment_agents.phase2_runner import run_phase2_episode
from institutional_investment_agents.phase2_schemas import FailureType, HardEpisodeFamily
from institutional_investment_agents.stochastic_model import StochasticSyntheticModel


def test_harness_profiles_are_operationally_ordered() -> None:
    weak = HARNESS_PROFILES["weak"]
    structured = HARNESS_PROFILES["structured"]
    strong = HARNESS_PROFILES["strong"]
    assert weak.strength < structured.strength < strong.strength
    assert not weak.explicit_plan and structured.explicit_plan
    assert not structured.verifier and strong.verifier
    assert strong.stale_evidence_exclusion and strong.revision_loop


def test_unknown_harness_fails() -> None:
    try:
        get_harness_profile("imaginary")
    except KeyError as error:
        assert "unknown harness" in str(error)
    else:
        raise AssertionError("unknown harness should fail")


def test_phase2_episode_is_reproducible() -> None:
    episode = generate_hard_episode(HardEpisodeFamily.MULTI_HOP_EVIDENCE, seed=4)
    first = run_phase2_episode(
        StochasticSyntheticModel("weak", seed=99), HARNESS_PROFILES["strong"], episode, seed=4
    )
    second = run_phase2_episode(
        StochasticSyntheticModel("weak", seed=99), HARNESS_PROFILES["strong"], episode, seed=4
    )
    assert first == second


def test_strong_harness_excludes_stale_evidence() -> None:
    episode = generate_hard_episode(HardEpisodeFamily.STALE_EVIDENCE, seed=9)
    run = run_phase2_episode(
        StochasticSyntheticModel("weak", seed=2), HARNESS_PROFILES["strong"], episode, seed=9
    )
    assert run.metrics.stale_evidence_usage_rate == 0


def test_cost_accounting_increases_with_harness_strength() -> None:
    episode = generate_hard_episode(HardEpisodeFamily.CONTRADICTORY_EVIDENCE, seed=1)
    weak = run_phase2_episode(
        StochasticSyntheticModel("medium", seed=7), HARNESS_PROFILES["weak"], episode, seed=1
    )
    strong = run_phase2_episode(
        StochasticSyntheticModel("medium", seed=7), HARNESS_PROFILES["strong"], episode, seed=1
    )
    assert strong.cost.model_calls > weak.cost.model_calls
    assert strong.cost.simulated_cost_units > weak.cost.simulated_cost_units
    assert strong.cost.critic_calls == 1 and strong.cost.verifier_calls == 1


def test_failure_taxonomy_covers_every_failure_type() -> None:
    assert set(FAILURE_TAXONOMY) == set(FailureType)
    assert classify_failure(FailureType.UNSUPPORTED_CLAIM).metrics
