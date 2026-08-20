"""Tutorial 25: request identity supports cache/resume without provider calls."""

from institutional_investment_agents.phase2_schemas import HarnessLevel, ModelOperation
from institutional_investment_agents.phase3_cache import request_id
from institutional_investment_agents.phase3_schemas import Phase3CallSpec, RealModelConfig

model = RealModelConfig(identifier="R0", model="configured-model")
spec = Phase3CallSpec(model=model, harness=HarnessLevel.H1_STRUCTURED, episode_id="E1", repetition=0, operation=ModelOperation.PLAN, prompt_id="phase3.plan_generation", prompt_version="1.0.0", prompt_schema_version="phase3-response-v1", input_hash="abc")
print(request_id(spec) == request_id(spec), request_id(spec)[:12])
