"""Immutable prompt treatments used by the frozen Phase 3 protocol."""

from __future__ import annotations

import hashlib
import json

from institutional_investment_agents.phase2_schemas import ModelOperation, ModelRequest
from institutional_investment_agents.phase3_schemas import PromptSpec

_BASE = (
    "You are performing a controlled institutional-credit research operation. "
    "Use only the supplied synthetic benchmark context. Do not invent sources. "
    "Return one JSON object with keys output, claims, risks, citations, tool_requests, "
    "thesis_direction, confidence, and uncertainties."
)


def _spec(operation: ModelOperation, instruction: str) -> PromptSpec:
    return PromptSpec(
        prompt_id=f"phase3.{operation.value}",
        prompt_version="1.0.0",
        operation=operation,
        template=f"{_BASE}\nOperation-specific instruction: {instruction}",
    )


PROMPT_REGISTRY: dict[ModelOperation, PromptSpec] = {
    ModelOperation.PLAN: _spec(ModelOperation.PLAN, "Produce a bounded research plan."),
    ModelOperation.EXECUTE_TASK: _spec(
        ModelOperation.EXECUTE_TASK, "Execute exactly the assigned research task."
    ),
    ModelOperation.ROUTE: _spec(ModelOperation.ROUTE, "Select the declared capability or tool."),
    ModelOperation.RETRIEVE: _spec(
        ModelOperation.RETRIEVE, "Select relevant evidence identifiers without rewriting them."
    ),
    ModelOperation.INTERPRET_EVIDENCE: _spec(
        ModelOperation.INTERPRET_EVIDENCE, "Interpret evidence and surface conflicts or ambiguity."
    ),
    ModelOperation.SELECT_TOOL: _spec(
        ModelOperation.SELECT_TOOL, "Request a tool when deterministic calculation is necessary."
    ),
    ModelOperation.GENERATE_CLAIMS: _spec(
        ModelOperation.GENERATE_CLAIMS, "Generate atomic claims with supporting evidence IDs."
    ),
    ModelOperation.SYNTHESIZE: _spec(
        ModelOperation.SYNTHESIZE, "Synthesize a thesis with risks and uncertainty."
    ),
    ModelOperation.CRITIQUE: _spec(
        ModelOperation.CRITIQUE, "Challenge omissions, contradictions, and unsupported inference."
    ),
    ModelOperation.REVISE: _spec(
        ModelOperation.REVISE, "Revise only when the challenge is supported; explain the change."
    ),
    ModelOperation.VERIFY: _spec(
        ModelOperation.VERIFY, "Check evidence, citation, calculation, and confidence traceability."
    ),
}


def get_prompt(operation: ModelOperation) -> PromptSpec:
    return PROMPT_REGISTRY[operation]


def render_prompt(spec: PromptSpec, request: ModelRequest) -> str:
    context = "\n".join(f"- {item}" for item in request.context) or "- none"
    tools = ", ".join(request.available_tools) or "none"
    return (
        f"{spec.template}\nPrompt ID: {spec.prompt_id}\n"
        f"Prompt version: {spec.prompt_version}\nEpisode: {request.episode_id}\n"
        f"Task: {request.instruction}\nAvailable tools: {tools}\nContext:\n{context}"
    )


def prompt_registry_hash() -> str:
    payload = [spec.model_dump(mode="json") for spec in PROMPT_REGISTRY.values()]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
