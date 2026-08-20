from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from institutional_investment_agents.phase2_schemas import (
    HarnessLevel,
    ModelOperation,
    ModelRequest,
)
from institutional_investment_agents.phase3_backend import (
    MalformedModelResponse,
    Phase3OpenAICompatibleBackend,
    Phase3ProviderError,
    parse_structured_content,
)
from institutional_investment_agents.phase3_cache import ResponseCache
from institutional_investment_agents.phase3_schemas import (
    ParseStatus,
    Phase3CallSpec,
    ProviderErrorKind,
    RealModelConfig,
)

VALID_OUTPUT = {
    "output": "plan",
    "claims": [],
    "risks": [],
    "citations": [],
    "tool_requests": [],
    "thesis_direction": "uncertain",
    "confidence": 0.5,
    "uncertainties": [],
}


def _spec(config: RealModelConfig, *, version: str = "1.0.0") -> Phase3CallSpec:
    return Phase3CallSpec(
        model=config,
        harness=HarnessLevel.H1_STRUCTURED,
        episode_id="episode",
        repetition=0,
        operation=ModelOperation.PLAN,
        prompt_id="phase3.plan_generation",
        prompt_version=version,
        prompt_schema_version="phase3-response-v1",
        input_hash="abc",
    )


def _request() -> ModelRequest:
    return ModelRequest(
        operation=ModelOperation.PLAN,
        episode_id="episode",
        instruction="Plan the research.",
        context=("E1 | filing | Synthetic evidence",),
    )


def test_request_construction_parsing_and_raw_preservation(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    def transport(
        url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float
    ) -> dict[str, Any]:
        captured.update(url=url, headers=headers, payload=payload, timeout=timeout)
        return {
            "choices": [{"message": {"content": json.dumps(VALID_OUTPUT)}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4},
        }

    config = RealModelConfig(identifier="R0", model="fixture-model", retries=0, seed=7)
    backend = Phase3OpenAICompatibleBackend(
        config,
        cache=ResponseCache(tmp_path),
        transport=transport,
        base_url="https://offline.invalid/v1",
        api_key="sk-fixture-secret",
    )
    result = backend.execute(_spec(config), _request())
    assert captured["url"] == "https://offline.invalid/v1/chat/completions"
    assert captured["payload"]["seed"] == 7
    assert captured["payload"]["temperature"] == 0
    assert result.record.parsed_response == VALID_OUTPUT
    assert result.record.raw_response["usage"]["prompt_tokens"] == 10
    assert "sk-fixture-secret" not in result.record.model_dump_json()


def test_bounded_repair_is_recorded() -> None:
    value, status, repairs = parse_structured_content(
        f"Here is JSON:\n```json\n{json.dumps(VALID_OUTPUT)}\n```"
    )
    assert value == VALID_OUTPUT
    assert status == ParseStatus.REPAIRED
    assert "extracted_json_object" in repairs


def test_malformed_output_fails_explicitly_and_is_not_cached(tmp_path: Path) -> None:
    config = RealModelConfig(identifier="R0", model="fixture", retries=0)

    def transport(*args: Any) -> dict[str, Any]:
        del args
        return {"choices": [{"message": {"content": "not json"}}]}

    backend = Phase3OpenAICompatibleBackend(
        config,
        cache=ResponseCache(tmp_path),
        transport=transport,
        base_url="https://offline.invalid",
        api_key="fixture",
    )
    with pytest.raises(MalformedModelResponse) as error:
        backend.execute(_spec(config), _request())
    assert error.value.kind == ProviderErrorKind.MALFORMED_RESPONSE
    assert error.value.record is not None
    assert error.value.record.parse_status == ParseStatus.FAILED
    assert error.value.record.raw_response["choices"]
    assert not tuple(tmp_path.rglob("*.json"))


def test_retry_is_bounded_and_classified(tmp_path: Path) -> None:
    calls = 0

    def transport(*args: Any) -> dict[str, Any]:
        nonlocal calls
        del args
        calls += 1
        raise TimeoutError("offline timeout")

    config = RealModelConfig(identifier="R0", model="fixture", retries=2)
    backend = Phase3OpenAICompatibleBackend(
        config,
        cache=ResponseCache(tmp_path),
        transport=transport,
        base_url="https://offline.invalid",
        api_key="fixture",
    )
    with pytest.raises(Phase3ProviderError) as error:
        backend.execute(_spec(config), _request())
    assert calls == 3
    assert error.value.attempts == 3
    assert error.value.kind == ProviderErrorKind.TIMEOUT


def test_truncated_provider_output_is_infrastructure_failure(tmp_path: Path) -> None:
    config = RealModelConfig(identifier="R0", model="fixture", retries=0)

    def transport(*args: Any) -> dict[str, Any]:
        del args
        return {
            "choices": [
                {"message": {"content": json.dumps(VALID_OUTPUT)}, "finish_reason": "length"}
            ]
        }

    backend = Phase3OpenAICompatibleBackend(
        config,
        cache=ResponseCache(tmp_path),
        transport=transport,
        base_url="https://offline.invalid",
        api_key="fixture",
    )
    with pytest.raises(Phase3ProviderError) as error:
        backend.execute(_spec(config), _request())
    assert error.value.kind == ProviderErrorKind.TRUNCATED_OUTPUT


def test_successful_call_resumes_from_cache_without_second_request(tmp_path: Path) -> None:
    calls = 0

    def transport(*args: Any) -> dict[str, Any]:
        nonlocal calls
        del args
        calls += 1
        return {"choices": [{"message": {"content": json.dumps(VALID_OUTPUT)}}]}

    config = RealModelConfig(identifier="R0", model="fixture", retries=0)
    backend = Phase3OpenAICompatibleBackend(
        config,
        cache=ResponseCache(tmp_path),
        transport=transport,
        base_url="https://offline.invalid",
        api_key="fixture",
    )
    first = backend.execute(_spec(config), _request())
    second = backend.execute(_spec(config), _request())
    assert calls == 1
    assert not first.cache_hit
    assert second.cache_hit
    assert second.new_api_calls == 0
