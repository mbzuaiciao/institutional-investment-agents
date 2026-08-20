"""Tutorial 29: materially reversed evidence should reverse the conclusion."""

from institutional_investment_agents.phase3_evaluator import counterfactual_consistency

print(counterfactual_consistency("unattractive", "attractive", evidence_reversed=True))
