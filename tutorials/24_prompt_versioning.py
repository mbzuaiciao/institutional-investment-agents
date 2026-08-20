"""Tutorial 24: prompts are registered, versioned experimental treatments."""

from institutional_investment_agents.phase2_schemas import ModelOperation
from institutional_investment_agents.prompts import get_prompt, prompt_registry_hash

prompt = get_prompt(ModelOperation.CRITIQUE)
print(prompt.prompt_id, prompt.prompt_version)
print("registry", prompt_registry_hash()[:12])
