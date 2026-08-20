"""Optional provider-neutral adapter for OpenAI-compatible chat completion APIs."""

from __future__ import annotations

import json
import os
import urllib.request
from collections.abc import Callable
from typing import Any

from institutional_investment_agents.phase2_schemas import (
    ConfidenceComponents,
    ModelRequest,
    ModelResponse,
)

Transport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


class OpenAICompatibleAdapter:
    """An optional adapter; no request is made until execute/generate is called."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str | None = None,
        api_key: str | None = None,
        transport: Transport | None = None,
    ) -> None:
        self.model = model
        self.base_url = (base_url or os.getenv("OPENAI_COMPATIBLE_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY", "")
        self.transport = transport or _urllib_transport
        if not self.base_url:
            raise ValueError("base URL is required via argument or OPENAI_COMPATIBLE_BASE_URL")
        if not self.api_key:
            raise ValueError("API key is required via argument or OPENAI_COMPATIBLE_API_KEY")

    def generate(self, prompt: str, *, context: tuple[str, ...] = ()) -> str:
        response = self._request(prompt, context)
        return str(response["choices"][0]["message"]["content"])

    def execute(self, request: ModelRequest) -> ModelResponse:
        prompt = (
            f"Operation: {request.operation.value}\nInstruction: {request.instruction}\n"
            "Return a concise structured research contribution."
        )
        payload = self._request(prompt, request.context)
        content = str(payload["choices"][0]["message"]["content"])
        usage = payload.get("usage", {})
        total_tokens = int(usage.get("total_tokens", 0)) if isinstance(usage, dict) else 0
        confidence = ConfidenceComponents(
            evidence=0.5,
            calculation=0.5,
            retrieval=0.5,
            consistency=0.5,
            model_judgment=0.5,
            overall=0.5,
        )
        return ModelResponse(
            operation=request.operation,
            structured_output={"text": content},
            confidence=confidence,
            usage={"actual_total_tokens": total_tokens, "model_calls": 1},
        )

    def _request(self, prompt: str, context: tuple[str, ...]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": f"{prompt}\n\nContext:\n" + "\n".join(context),
                }
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        return self.transport(f"{self.base_url}/chat/completions", headers, payload)


def _urllib_transport(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise TypeError("OpenAI-compatible response must be a JSON object")
    return value
