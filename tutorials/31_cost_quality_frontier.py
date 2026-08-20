"""Tutorial 31: inspect a bounded smoke plan before any API request."""

from pathlib import Path

from institutional_investment_agents.phase2_schemas import HarnessLevel
from institutional_investment_agents.phase3_config import build_plan, load_models, load_presets
from institutional_investment_agents.phase3_schemas import ResourceLimits

root = Path(__file__).resolve().parents[1]
models = load_models(root / "configs/phase3_models.example.yaml", ("R0", "R1", "R2"))
preset = load_presets(root / "configs/phase3_protocol.yaml")["smoke"]
plan = build_plan(preset=preset, study="tutorial", models=models, harnesses=tuple(HarnessLevel), limits=ResourceLimits(max_model_calls=500, max_total_tokens=1_000_000))
print(plan.approximate_model_calls, plan.estimated_upper_cost)
