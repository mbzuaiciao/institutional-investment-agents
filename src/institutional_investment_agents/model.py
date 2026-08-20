"""Model policy abstraction; default backend is deterministic and offline."""

from __future__ import annotations

from typing import Protocol

from institutional_investment_agents.phase2_schemas import (
    ConfidenceComponents,
    ModelRequest,
    ModelResponse,
)


class ModelBackend(Protocol):
    def generate(self, prompt: str, *, context: tuple[str, ...] = ()) -> str: ...

    def execute(self, request: ModelRequest) -> ModelResponse: ...


class DeterministicResearchModel:
    """A transparent policy used to make tests and tutorials API-key free."""

    def __init__(self, profile: str = "standard") -> None:
        self.profile = profile

    def generate(self, prompt: str, *, context: tuple[str, ...] = ()) -> str:
        material = " ".join(context)
        if not material:
            return f"Insufficient evidence for: {prompt}"
        prefix = "Research observation" if self.profile == "standard" else "Tentative observation"
        return f"{prefix}: {material[:360]}"

    def execute(self, request: ModelRequest) -> ModelResponse:
        """Return a typed, error-free response for the Phase 1 deterministic backend."""
        output = self.generate(request.instruction, context=request.context)
        confidence = ConfidenceComponents(
            evidence=1.0,
            calculation=1.0,
            retrieval=1.0,
            consistency=1.0,
            model_judgment=1.0,
            overall=1.0,
        )
        return ModelResponse(
            operation=request.operation,
            structured_output={"text": output},
            confidence=confidence,
            usage={"simulated_token_units": 1},
        )
