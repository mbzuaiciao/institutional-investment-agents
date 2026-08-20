from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from institutional_investment_agents.phase2_schemas import HarnessLevel, ModelOperation
from institutional_investment_agents.phase3_cache import redact, request_id
from institutional_investment_agents.phase3_config import file_hash, load_json_yaml
from institutional_investment_agents.phase3_schemas import Phase3CallSpec, RealModelConfig
from institutional_investment_agents.prompts import PROMPT_REGISTRY, prompt_registry_hash

ROOT = Path(__file__).resolve().parents[1]


def _spec(version: str = "1.0.0") -> Phase3CallSpec:
    return Phase3CallSpec(
        model=RealModelConfig(identifier="R0", model="fixture"),
        harness=HarnessLevel.H2_STRONG,
        episode_id="E1",
        repetition=0,
        operation=ModelOperation.CRITIQUE,
        prompt_id="phase3.critique",
        prompt_version=version,
        prompt_schema_version="phase3-response-v1",
        input_hash="input",
    )


def test_cache_identity_is_stable_and_prompt_sensitive() -> None:
    assert request_id(_spec()) == request_id(_spec())
    assert request_id(_spec()) != request_id(_spec("1.0.1"))


def test_prompt_registry_covers_all_operations_and_is_versioned() -> None:
    assert set(PROMPT_REGISTRY) == set(ModelOperation)
    assert all(item.prompt_version == "1.0.0" for item in PROMPT_REGISTRY.values())
    assert len(prompt_registry_hash()) == 64


def test_redaction_removes_sensitive_keys_and_bearer_values() -> None:
    value = redact(
        {
            "Authorization": "Bearer secret-token",
            "api_key": "sk-fixture-123",
            "nested": ["sk-fixture-456"],
        }
    )
    encoded = json.dumps(value)
    assert "secret-token" not in encoded
    assert "sk-this" not in encoded
    assert encoded.count("[REDACTED]") >= 3


def test_frozen_benchmark_checksums_match() -> None:
    freeze = load_json_yaml(ROOT / "configs/phase3_freeze_manifest.json")
    for relative, expected in freeze["frozen_files"].items():
        assert file_hash(ROOT / relative) == expected


def test_research_runtime_does_not_import_hidden_evaluator() -> None:
    paths = (
        ROOT / "src/institutional_investment_agents/phase3_benchmark.py",
        ROOT / "src/institutional_investment_agents/phase3_runtime.py",
    )
    for path in paths:
        tree = ast.parse(path.read_text())
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        assert not any("phase3_evaluator" in name for name in imports)


def test_prediction_registry_is_locked_and_unrun() -> None:
    registry: dict[str, Any] = load_json_yaml(ROOT / "configs/phase3_predictions.yaml")
    assert registry["result_status"] == "NOT YET RUN"
    assert len(registry["predictions"]) == 7
    assert all(item["direction_locked"] for item in registry["predictions"].values())
