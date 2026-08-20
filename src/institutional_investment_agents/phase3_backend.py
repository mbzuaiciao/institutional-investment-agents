"""Robust provider-neutral real-model backend for controlled Phase 3 calls."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from institutional_investment_agents.phase2_schemas import ModelRequest
from institutional_investment_agents.phase3_cache import (
    CACHE_VERSION,
    ResponseCache,
    redact,
    request_id,
)
from institutional_investment_agents.phase3_schemas import (
    ParseStatus,
    Phase3CallResult,
    Phase3CallSpec,
    ProviderErrorKind,
    RawCallRecord,
    RealModelConfig,
)
from institutional_investment_agents.prompts import get_prompt, render_prompt

Transport = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]
Clock = Callable[[], float]


class Phase3ProviderError(RuntimeError):
    def __init__(
        self,
        kind: ProviderErrorKind,
        message: str,
        *,
        attempts: int,
        record: RawCallRecord | None = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.attempts = attempts
        self.record = record


class MalformedModelResponse(Phase3ProviderError):
    pass


class Phase3OpenAICompatibleBackend:
    """OpenAI-compatible chat backend with parsing, bounded repair, retry, and cache."""

    def __init__(
        self,
        config: RealModelConfig,
        *,
        cache: ResponseCache,
        transport: Transport | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        clock: Clock = time.perf_counter,
    ) -> None:
        self.config = config
        self.cache = cache
        self.transport = transport or _urllib_transport
        self.base_url = (base_url or os.getenv(config.base_url_env, "")).rstrip("/")
        self.api_key = api_key or os.getenv(config.api_key_env, "")
        self.clock = clock
        if not self.base_url:
            raise ValueError(f"base URL required via {config.base_url_env}")
        if not self.api_key:
            raise ValueError(f"API key required via {config.api_key_env}")

    def execute(self, spec: Phase3CallSpec, request: ModelRequest) -> Phase3CallResult:
        identifier = request_id(spec)
        cached = self.cache.load(identifier)
        if cached is not None:
            return Phase3CallResult(record=cached, cache_hit=True, new_api_calls=0)

        prompt = render_prompt(get_prompt(request.operation), request)
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
        }
        if self.config.seed is not None:
            payload["seed"] = self.config.seed
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        started = self.clock()
        raw, attempts = self._request_with_retry(headers, payload)
        latency = max(0.0, self.clock() - started)
        content, finish_reason = _extract_content(raw, attempts)
        parsed, parse_status, repairs = parse_structured_content(content)
        if parsed is None:
            failed_record = RawCallRecord(
                cache_version=CACHE_VERSION,
                request_id=identifier,
                provider=self.config.backend,
                model=self.config.model,
                timestamp=datetime.now(UTC).isoformat(),
                operation=request.operation,
                episode_id=spec.episode_id,
                harness=spec.harness,
                repetition=spec.repetition,
                experimental_condition=spec.experimental_condition,
                input_hash=spec.input_hash,
                prompt_id=spec.prompt_id,
                prompt_version=spec.prompt_version,
                raw_response=redact(raw),
                parsed_response=None,
                parse_status=ParseStatus.FAILED,
                repair_attempts=repairs,
                usage_metadata=_usage_metadata(raw),
                latency_seconds=latency,
                error_metadata={"attempts": attempts, "error": "structured_parse_failed"},
            )
            raise MalformedModelResponse(
                ProviderErrorKind.MALFORMED_RESPONSE,
                "model output was not a valid Phase 3 JSON object after bounded repair",
                attempts=attempts,
                record=failed_record,
            )
        if finish_reason == "length":
            raise Phase3ProviderError(
                ProviderErrorKind.TRUNCATED_OUTPUT,
                "provider reported a length-truncated response",
                attempts=attempts,
            )
        record = RawCallRecord(
            cache_version=CACHE_VERSION,
            request_id=identifier,
            provider=self.config.backend,
            model=self.config.model,
            timestamp=datetime.now(UTC).isoformat(),
            operation=request.operation,
            episode_id=spec.episode_id,
            harness=spec.harness,
            repetition=spec.repetition,
            experimental_condition=spec.experimental_condition,
            input_hash=spec.input_hash,
            prompt_id=spec.prompt_id,
            prompt_version=spec.prompt_version,
            raw_response=redact(raw),
            parsed_response=parsed,
            parse_status=parse_status,
            repair_attempts=repairs,
            usage_metadata=_usage_metadata(raw),
            latency_seconds=latency,
            error_metadata={"attempts": attempts},
        )
        self.cache.save(record)
        return Phase3CallResult(record=record, cache_hit=False, new_api_calls=1)

    def _request_with_retry(
        self, headers: dict[str, str], payload: dict[str, Any]
    ) -> tuple[dict[str, Any], int]:
        maximum_attempts = self.config.retries + 1
        for attempt in range(1, maximum_attempts + 1):
            try:
                response = self.transport(
                    f"{self.base_url}/chat/completions",
                    headers,
                    payload,
                    self.config.timeout_seconds,
                )
                if not isinstance(response, dict):
                    raise TypeError("provider response must be a JSON object")
                return response, attempt
            except Exception as error:
                kind, retryable = classify_provider_error(error)
                if not retryable or attempt == maximum_attempts:
                    raise Phase3ProviderError(kind, str(error), attempts=attempt) from error
        raise AssertionError("retry loop exhausted unexpectedly")


def parse_structured_content(
    content: str,
) -> tuple[dict[str, Any] | None, ParseStatus, tuple[str, ...]]:
    """Parse once, then perform only bounded fence/object extraction repair."""
    try:
        value = json.loads(content)
        return _validate_payload(value), ParseStatus.VALID, ()
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    candidate = content.strip()
    repairs: list[str] = []
    if candidate.startswith("```") and candidate.endswith("```"):
        lines = candidate.splitlines()
        candidate = "\n".join(lines[1:-1]).strip()
        repairs.append("removed_markdown_fence")
    first = candidate.find("{")
    last = candidate.rfind("}")
    if first >= 0 and last > first and (first != 0 or last != len(candidate) - 1):
        candidate = candidate[first : last + 1]
        repairs.append("extracted_json_object")
    try:
        value = json.loads(candidate)
        return _validate_payload(value), ParseStatus.REPAIRED, tuple(repairs or ["json_retry"])
    except (json.JSONDecodeError, TypeError, ValueError):
        return None, ParseStatus.FAILED, tuple(repairs or ["repair_failed"])


def _validate_payload(value: Any) -> dict[str, Any]:
    try:
        return StructuredResearchOutput.model_validate(value).model_dump(mode="json")
    except ValidationError as error:
        raise ValueError("structured response violates phase3-response-v1") from error


class StructuredResearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    output: str
    claims: list[dict[str, Any]]
    risks: list[str]
    citations: list[str]
    tool_requests: list[dict[str, Any]]
    thesis_direction: str
    confidence: float = Field(ge=0, le=1)
    uncertainties: list[str]


def _usage_metadata(raw: dict[str, Any]) -> dict[str, int | float]:
    usage = raw.get("usage", {})
    if not isinstance(usage, dict):
        return {}
    return {str(key): value for key, value in usage.items() if isinstance(value, int | float)}


def _extract_content(raw: dict[str, Any], attempts: int) -> tuple[str, str | None]:
    try:
        choice = raw["choices"][0]
        content = choice["message"]["content"]
        finish_reason = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as error:
        raise MalformedModelResponse(
            ProviderErrorKind.MALFORMED_RESPONSE,
            "provider response lacks choices[0].message.content",
            attempts=attempts,
        ) from error
    if not isinstance(content, str):
        raise MalformedModelResponse(
            ProviderErrorKind.MALFORMED_RESPONSE,
            "provider content must be text",
            attempts=attempts,
        )
    return content, str(finish_reason) if finish_reason is not None else None


def classify_provider_error(error: Exception) -> tuple[ProviderErrorKind, bool]:
    if isinstance(error, (TimeoutError, urllib.error.URLError)):
        return ProviderErrorKind.TIMEOUT, True
    if isinstance(error, urllib.error.HTTPError):
        if error.code == 429:
            return ProviderErrorKind.RATE_LIMIT, True
        if 500 <= error.code < 600:
            return ProviderErrorKind.TRANSIENT_SERVER, True
        if error.code in {401, 403}:
            return ProviderErrorKind.AUTHENTICATION, False
    if isinstance(error, (TypeError, json.JSONDecodeError)):
        return ProviderErrorKind.MALFORMED_RESPONSE, False
    return ProviderErrorKind.PERMANENT, False


def _urllib_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        value = json.loads(response.read().decode())
    if not isinstance(value, dict):
        raise TypeError("provider response must be an object")
    return value
