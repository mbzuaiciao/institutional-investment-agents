# Agentic investment research

An investment-research agent is a policy operating inside a constrained research environment. It observes a question and research state, selects actions such as retrieval or calculation, receives results, updates explicit state, and stops under a termination rule. The model is only one component. Tool permissions, evidence representation, task routing, review gates, and trace retention collectively determine what the system can know and what reviewers can audit.

Institutional research differs from generic financial question answering because the deliverable is a decision artifact with lineage. Facts, calculations, assumptions, inferences, and judgments have different epistemic status. A fluent memo can still be poor research if it lacks downside cases, uses stale evidence, performs silent arithmetic, or conceals contradictions. The repository therefore treats the harness as part of the epistemic system and evaluates process behavior alongside conclusions.

Failure modes include automation bias, unsupported synthesis, duplicated specialist work, false precision, lost provenance, tool misuse, confirmation bias, and premature termination. More agents and more steps are hypotheses to test, not definitions of progress.

