"""Model policy abstraction; default backend is deterministic and offline."""

from __future__ import annotations

from typing import Protocol


class ModelBackend(Protocol):
    def generate(self, prompt: str, *, context: tuple[str, ...] = ()) -> str: ...


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
