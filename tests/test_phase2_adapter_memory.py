import pytest

from institutional_investment_agents.adapters import OpenAICompatibleAdapter
from institutional_investment_agents.longitudinal import run_longitudinal_research
from institutional_investment_agents.phase2_schemas import ModelOperation, ModelRequest


def test_openai_compatible_adapter_uses_injected_transport() -> None:
    observed = {}

    def transport(url, headers, payload):
        observed.update({"url": url, "headers": headers, "payload": payload})
        return {
            "choices": [{"message": {"content": "structured answer"}}],
            "usage": {"total_tokens": 42},
        }

    adapter = OpenAICompatibleAdapter(
        model="mock-model",
        base_url="https://example.test/v1",
        api_key="test-key",
        transport=transport,
    )
    response = adapter.execute(
        ModelRequest(operation=ModelOperation.PLAN, episode_id="mock", instruction="plan")
    )
    assert response.structured_output["text"] == "structured answer"
    assert response.usage["actual_total_tokens"] == 42
    assert observed["url"] == "https://example.test/v1/chat/completions"
    assert observed["headers"]["Authorization"] == "Bearer test-key"


def test_adapter_requires_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_COMPATIBLE_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPATIBLE_API_KEY", raising=False)
    with pytest.raises(ValueError):
        OpenAICompatibleAdapter(model="missing")


def test_longitudinal_run_is_reproducible_and_tracks_cost() -> None:
    first = run_longitudinal_research("medium", persistent=True, seed=17)
    second = run_longitudinal_research("medium", persistent=True, seed=17)
    assert first == second
    assert len(first.metrics.quality_by_episode) == 5
    assert first.cost.model_calls == 10
    assert first.metrics.redundant_research_operations == 6
