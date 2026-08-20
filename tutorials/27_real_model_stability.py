"""Tutorial 27: repeated-run variation is decomposed rather than called noise."""

from institutional_investment_agents.phase3_metrics import stability_metrics
from institutional_investment_agents.phase3_schemas import StabilityRecord

runs = (
    StabilityRecord(thesis="avoid", score=80, risk_recall=.8, citation_validity=1, tool_calls=1, route="credit"),
    StabilityRecord(thesis="avoid", score=84, risk_recall=1, citation_validity=.8, tool_calls=1, route="credit"),
    StabilityRecord(thesis="watch", score=72, risk_recall=.6, citation_validity=1, tool_calls=0, route="general"),
)
print(stability_metrics(runs))
