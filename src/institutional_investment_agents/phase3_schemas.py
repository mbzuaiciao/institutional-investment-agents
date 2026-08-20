"""Typed contracts for Phase 3 real-model validation infrastructure."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from institutional_investment_agents.phase2_schemas import HarnessLevel, ModelOperation


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ResultStatus(StrEnum):
    SIMULATED = "SIMULATED"
    PILOT_REAL_MODEL = "PILOT REAL-MODEL"
    CONFIRMATORY_REAL_MODEL = "CONFIRMATORY REAL-MODEL"
    NOT_YET_RUN = "NOT YET RUN"


class ParseStatus(StrEnum):
    VALID = "valid"
    REPAIRED = "repaired"
    FAILED = "failed"


class ProviderErrorKind(StrEnum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    TRANSIENT_SERVER = "transient_server_error"
    MALFORMED_RESPONSE = "malformed_response"
    TRUNCATED_OUTPUT = "truncated_output"
    AUTHENTICATION = "authentication_error"
    PERMANENT = "permanent_provider_error"


class PricingMetadata(FrozenModel):
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(ge=0)
    currency: str = "USD"


class RealModelConfig(FrozenModel):
    identifier: str
    backend: str = "openai_compatible"
    model: str
    declared_tier: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_output_tokens: int = Field(default=1200, ge=1)
    timeout_seconds: float = Field(default=60.0, gt=0)
    retries: int = Field(default=2, ge=0, le=10)
    seed: int | None = None
    base_url_env: str = "OPENAI_COMPATIBLE_BASE_URL"
    api_key_env: str = "OPENAI_COMPATIBLE_API_KEY"
    pricing: PricingMetadata | None = None


class ResourceLimits(FrozenModel):
    max_model_calls: int = Field(default=1000, ge=1)
    max_calls_per_episode: int = Field(default=12, ge=1)
    max_total_tokens: int = Field(default=2_000_000, ge=1)
    max_estimated_cost: float | None = Field(default=None, ge=0)
    max_retries: int = Field(default=2, ge=0, le=10)


class ExperimentPreset(FrozenModel):
    name: str
    families: tuple[str, ...]
    repetitions: int = Field(ge=1)


class PromptSpec(FrozenModel):
    prompt_id: str
    prompt_version: str
    operation: ModelOperation
    template: str
    response_schema_version: str = "phase3-response-v1"


class Phase3CallSpec(FrozenModel):
    model: RealModelConfig
    harness: HarnessLevel
    episode_id: str
    repetition: int = Field(ge=0)
    operation: ModelOperation
    prompt_id: str
    prompt_version: str
    prompt_schema_version: str
    input_hash: str
    experimental_condition: str = "main"


class RawCallRecord(FrozenModel):
    cache_version: str
    request_id: str
    provider: str
    model: str
    timestamp: str
    operation: ModelOperation
    episode_id: str
    harness: HarnessLevel
    repetition: int = Field(ge=0)
    experimental_condition: str
    input_hash: str
    prompt_id: str
    prompt_version: str
    raw_response: Any
    parsed_response: dict[str, Any] | None = None
    parse_status: ParseStatus
    repair_attempts: tuple[str, ...] = ()
    usage_metadata: dict[str, int | float] = Field(default_factory=dict)
    latency_seconds: float = Field(ge=0)
    error_metadata: dict[str, str | int | float | bool] = Field(default_factory=dict)


class Phase3CallResult(FrozenModel):
    record: RawCallRecord
    cache_hit: bool
    new_api_calls: int = Field(ge=0, le=1)


class ExperimentPlan(FrozenModel):
    preset: str
    study: str
    model_ids: tuple[str, ...]
    harnesses: tuple[HarnessLevel, ...]
    conditions: tuple[str, ...]
    families: tuple[str, ...]
    repetitions: int
    planned_cells: int
    planned_episode_runs: int
    approximate_model_calls: int
    approximate_total_tokens: int
    max_calls_per_episode: int
    configured_cost_limit: float | None
    estimated_upper_cost: float | None


class ClaimCalibrationRecord(FrozenModel):
    confidence: float = Field(ge=0, le=1)
    correct_or_supported: bool
    source: str = "self_reported"


class StabilityRecord(FrozenModel):
    thesis: str
    score: float = Field(ge=0, le=100)
    risk_recall: float = Field(ge=0, le=1)
    citation_validity: float = Field(ge=0, le=1)
    tool_calls: int = Field(ge=0)
    route: str


class Phase3ScoredRun(FrozenModel):
    model_id: str
    harness: HarnessLevel
    condition: str
    episode_id: str
    repetition: int = Field(ge=0)
    research_quality: float = Field(ge=0, le=100)
    control_quality: float = Field(ge=0, le=100)
    risk_recall: float = Field(ge=0, le=1)
    citation_validity: float = Field(ge=0, le=1)
    unsupported_claims: int = Field(ge=0)
    model_calls: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    latency_seconds: float = Field(ge=0)
    monetary_cost: float | None = Field(default=None, ge=0)


class Phase3RunMetadata(FrozenModel):
    result_status: ResultStatus
    provider: str
    model_identifier: str
    provider_model_version: str | None = None
    run_date: str
    temperature: float
    seed: int | None = None
    prompt_registry_hash: str
    harness_version: str
    benchmark_hash: str
    code_commit: str
    request_ids: tuple[str, ...]
    usage_metadata: dict[str, int | float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def real_status_requires_requests(self) -> Phase3RunMetadata:
        if self.result_status != ResultStatus.NOT_YET_RUN and not self.request_ids:
            raise ValueError("executed Phase 3 results require request IDs")
        return self
