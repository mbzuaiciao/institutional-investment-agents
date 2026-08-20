"""Tutorial 23: exercise the real-model adapter with an offline transport."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from institutional_investment_agents.phase2_schemas import (
    HarnessLevel,
    ModelOperation,
    ModelRequest,
)
from institutional_investment_agents.phase3_backend import Phase3OpenAICompatibleBackend
from institutional_investment_agents.phase3_benchmark import ObservableEpisode
from institutional_investment_agents.phase3_cache import ResponseCache
from institutional_investment_agents.phase3_runtime import prepare_calls
from institutional_investment_agents.phase3_schemas import RealModelConfig

episode = ObservableEpisode(
    episode_id="tutorial", family="premise_error", difficulty=3,
    task_instruction="Check the premise.",
    evidence=({"evidence_id": "E1", "source": "filing", "text": "Leverage worsened."},),
    split="development",
)
model = RealModelConfig(identifier="R-demo", model="offline-fixture", retries=0)
prepared = prepare_calls(model=model, harness=HarnessLevel.H0_MINIMAL, episode=episode, repetition=0)[0]

def transport(url: str, headers: dict[str, str], payload: dict[str, object], timeout: float) -> dict[str, object]:
    del url, headers, payload, timeout
    content = {
        "output": "Premise contradicted.", "claims": [], "risks": [], "citations": [],
        "tool_requests": [], "thesis_direction": "uncertain", "confidence": .6,
        "uncertainties": [],
    }
    return {"choices": [{"message": {"content": json.dumps(content)}}], "usage": {"total_tokens": 12}}

with TemporaryDirectory() as directory:
    backend = Phase3OpenAICompatibleBackend(model, cache=ResponseCache(Path(directory)), transport=transport, base_url="https://offline.invalid", api_key="fixture")
    request = ModelRequest(operation=ModelOperation.RETRIEVE, episode_id="tutorial", instruction="Check", context=("E1",))
    result = backend.execute(prepared.spec, request)
    print(result.record.parse_status, result.new_api_calls)
