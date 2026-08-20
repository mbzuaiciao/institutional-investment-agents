# Limitations

## Data and market representation

All issuer, market, macro, document, news, expected-direction, and risk-label data are synthetic. The universe has ten issuers and the capstone evaluates four of them. Synthetic consistency makes controlled tests possible, but it cannot reproduce the distribution shifts, missing fields, reporting choices, liquidity effects, or adversarial ambiguity of real credit research.

The spread calculation is a simple yield-to-benchmark difference, not a full option-adjusted spread or fitted-curve analysis. Historical spread position uses a normal-distribution z-score. Expected loss uses simplified default and recovery assumptions. These tools teach traceable calculation contracts, not production valuation.

Portfolio impact is a first-order spread-duration and rate-duration approximation for a hypothetical position. It does not model convexity, optionality, default jump risk, liquidity, hedges, correlation, concentration, or mandate-specific constraints.

## Model and verification

The default backend is deterministic/mock behavior. It does not reproduce the variability, knowledge, prompt sensitivity, context limits, tool-selection errors, or hallucination patterns of real LLMs. Many integrated decisions are explicit policies, so current results measure this harness implementation more directly than general model-agent capability.

Evidence verification uses object-existence checks and a lexical token-overlap heuristic. It is not semantic entailment, source-quality assessment, numerical reconciliation, or temporal validity checking. It may accept related but non-supporting text and reject valid paraphrases.

The human approval gate is simulated by deterministic policy. No expert actually reviews the evidence or accepts accountability. The project therefore demonstrates a control interface, not validated human oversight.

## Information and time

The project uses no Bloomberg, FactSet, Refinitiv, or other licensed market data. It has no live research ingestion, SEC filing feed, pricing service, or macro-data adapter. Documents are static within a run.

Temporal reasoning is limited. The system does not reconcile as-of dates, restatements, stale estimates, evolving guidance, or information that arrives after thesis formation. It does not test whether a prior claim should be revised when newer evidence conflicts with it.

Shared state persists within a research run, but there is no durable multi-episode research memory. Consequently, the persistent-state capstone variant does not test longitudinal memory in the setting where it is most likely to matter.

## Evaluation validity

The benchmark is small, deterministic, and designed by the same project that implements the policies. Synthetic ground truth encodes expected thesis direction and known risk labels; it is not an independent expert consensus. The composite score uses explicit but subjective weights. Directional accuracy is perfect across current variants because the deterministic synthesis has direct access to the synthetic direction rule, limiting the metric’s discriminating power.

Some desired metrics are not yet fully instrumented, including duplicate work, revision quality, false challenges, semantic contradiction resolution, scenario completeness, latency, and real model cost. Capstone comparisons are progressive architecture packages; standalone scripts provide narrower ablations, but not every switch has an independent factorial estimate.

No claim is made that the current numerical findings generalize directly to production LLM systems, live institutional workflows, or investment performance.

## Why these limits are acceptable in phase one

The first objective is to validate abstractions and experimental plumbing: typed state, stable provenance, deterministic tools, reproducible configurations, auditable events, and component metrics. Synthetic data and deterministic policies isolate software and harness effects before model sampling, data licensing, and market drift are introduced. This creates a falsifiable baseline. The limits define the next experiments rather than being hidden behind claims of production readiness.
