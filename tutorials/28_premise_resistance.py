"""Tutorial 28: score resistance to a false research premise."""

from institutional_investment_agents.phase3_evaluator import premise_resistance_score

score = premise_resistance_score(accepted_false_premise=False, corrected_premise=True, sought_evidence=True, hedged=True, unsupported_rationalization=False)
print("premise resistance", score)
