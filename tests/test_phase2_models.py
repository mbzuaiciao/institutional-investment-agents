from institutional_investment_agents.model import DeterministicResearchModel
from institutional_investment_agents.phase2_schemas import ModelOperation, ModelRequest
from institutional_investment_agents.stochastic_model import (
    MODEL_PROFILES,
    StochasticSyntheticModel,
)


def _request(operation: ModelOperation = ModelOperation.GENERATE_CLAIMS) -> ModelRequest:
    return ModelRequest(operation=operation, episode_id="test", instruction="test operation")


def test_named_profiles_are_systematically_ordered() -> None:
    fields = (
        "reasoning_accuracy",
        "retrieval_interpretation_accuracy",
        "tool_selection_accuracy",
        "contradiction_detection",
        "risk_recall",
        "citation_fidelity",
        "revision_responsiveness",
    )
    for field in fields:
        assert getattr(MODEL_PROFILES["weak"], field) < getattr(MODEL_PROFILES["medium"], field)
        assert getattr(MODEL_PROFILES["medium"], field) < getattr(MODEL_PROFILES["strong"], field)


def test_stochastic_backend_is_seed_reproducible() -> None:
    first = StochasticSyntheticModel("weak", seed=81)
    second = StochasticSyntheticModel("weak", seed=81)
    operations = tuple(ModelOperation) * 3
    first_results = [first.execute(_request(operation)) for operation in operations]
    second_results = [second.execute(_request(operation)) for operation in operations]
    assert first_results == second_results


def test_weak_profile_injects_more_errors_over_repeated_operations() -> None:
    weak = StochasticSyntheticModel("weak", seed=9)
    strong = StochasticSyntheticModel("strong", seed=9)
    requests = [_request(operation) for operation in tuple(ModelOperation) * 25]
    weak_errors = sum(len(weak.execute(request).failures) for request in requests)
    strong_errors = sum(len(strong.execute(request).failures) for request in requests)
    assert weak_errors > strong_errors


def test_deterministic_backend_supports_typed_operations() -> None:
    response = DeterministicResearchModel().execute(_request(ModelOperation.PLAN))
    assert response.operation == ModelOperation.PLAN
    assert not response.failures
    assert response.confidence.overall == 1.0


def test_confidence_components_are_explicitly_uncalibrated() -> None:
    response = StochasticSyntheticModel("medium", seed=1).execute(_request())
    assert response.confidence.calibrated is False
    assert 0 <= response.confidence.overall <= 1
