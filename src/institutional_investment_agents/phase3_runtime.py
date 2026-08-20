"""Research-side Phase 3 runtime with no access to hidden evaluator labels."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from institutional_investment_agents.phase2_schemas import (
    HarnessLevel,
    ModelOperation,
    ModelRequest,
)
from institutional_investment_agents.phase3_benchmark import ObservableEpisode, research_context
from institutional_investment_agents.phase3_schemas import Phase3CallSpec, RealModelConfig
from institutional_investment_agents.prompts import get_prompt

HARNESS_OPERATIONS: dict[HarnessLevel, tuple[ModelOperation, ...]] = {
    HarnessLevel.H0_MINIMAL: (
        ModelOperation.RETRIEVE,
        ModelOperation.INTERPRET_EVIDENCE,
        ModelOperation.SYNTHESIZE,
    ),
    HarnessLevel.H1_STRUCTURED: (
        ModelOperation.PLAN,
        ModelOperation.ROUTE,
        ModelOperation.RETRIEVE,
        ModelOperation.INTERPRET_EVIDENCE,
        ModelOperation.SELECT_TOOL,
        ModelOperation.GENERATE_CLAIMS,
        ModelOperation.SYNTHESIZE,
    ),
    HarnessLevel.H2_STRONG: (
        ModelOperation.PLAN,
        ModelOperation.ROUTE,
        ModelOperation.RETRIEVE,
        ModelOperation.INTERPRET_EVIDENCE,
        ModelOperation.SELECT_TOOL,
        ModelOperation.GENERATE_CLAIMS,
        ModelOperation.SYNTHESIZE,
        ModelOperation.CRITIQUE,
        ModelOperation.REVISE,
        ModelOperation.VERIFY,
    ),
}


@dataclass(frozen=True)
class PreparedCall:
    spec: Phase3CallSpec
    request: ModelRequest


def prepare_calls(
    *,
    model: RealModelConfig,
    harness: HarnessLevel,
    episode: ObservableEpisode,
    repetition: int,
    condition: str = "main",
    operations: tuple[ModelOperation, ...] | None = None,
    context_mode: str = "shared",
    state_context: tuple[str, ...] = (),
) -> tuple[PreparedCall, ...]:
    full_context = (*research_context(episode), *state_context)
    prepared: list[PreparedCall] = []
    selected_operations = operations or HARNESS_OPERATIONS[harness]
    for index, operation in enumerate(selected_operations):
        context = _operation_context(full_context, index=index, mode=context_mode)
        prompt = get_prompt(operation)
        request = ModelRequest(
            operation=operation,
            episode_id=episode.episode_id,
            instruction=episode.task_instruction,
            context=context,
            available_tools=episode.available_tools,
            required_schema=prompt.response_schema_version,
        )
        input_hash = hashlib.sha256(
            "\n".join((episode.episode_id, operation.value, *context)).encode()
        ).hexdigest()
        spec = Phase3CallSpec(
            model=model,
            harness=harness,
            episode_id=episode.episode_id,
            repetition=repetition,
            operation=operation,
            prompt_id=prompt.prompt_id,
            prompt_version=prompt.prompt_version,
            prompt_schema_version=prompt.response_schema_version,
            input_hash=input_hash,
            experimental_condition=condition,
        )
        prepared.append(PreparedCall(spec=spec, request=request))
    return tuple(prepared)


def _operation_context(context: tuple[str, ...], *, index: int, mode: str) -> tuple[str, ...]:
    if mode == "shared" or len(context) < 2:
        return context
    if mode != "partitioned":
        raise ValueError(f"unknown context mode: {mode}")
    partition = tuple(item for position, item in enumerate(context) if position % 2 == index % 2)
    return partition or context
