"""Tutorial 32: validate the frozen protocol and prediction registry offline."""

from pathlib import Path

from institutional_investment_agents.phase3_config import file_hash, load_json_yaml

root = Path(__file__).resolve().parents[1]
freeze = load_json_yaml(root / "configs/phase3_freeze_manifest.json")
predictions = load_json_yaml(root / "configs/phase3_predictions.yaml")
for relative, expected in freeze["frozen_files"].items():
    assert file_hash(root / relative) == expected
print(len(predictions["predictions"]), predictions["result_status"])
