"""Versioned Phase 3 prompt registry."""

from institutional_investment_agents.prompts.registry import (
    PROMPT_REGISTRY,
    get_prompt,
    prompt_registry_hash,
    render_prompt,
)

__all__ = ["PROMPT_REGISTRY", "get_prompt", "prompt_registry_hash", "render_prompt"]
