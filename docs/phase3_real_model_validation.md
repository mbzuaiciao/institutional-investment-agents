# Phase 3: Real-Model Validation

> **Result status: NOT YET RUN**

> **Phase 3 infrastructure is complete, but the central real-model hypotheses remain empirically untested.**

Phase 3 is an infrastructure and research-protocol release. No real-model API experiment was executed, and mocked transports, fixtures, tutorials, caches, or dry runs are not empirical results.

## 1. Motivation

Phase 3 asks whether the controlled simulator findings survive actual LLM behavior. The target is causal attribution across model capability, harness capability, their interaction, workflow budget, provider effects, prompt effects, repeated-run variation, and episode difficulty—not maximum benchmark score.

## 2. Phase 1 recap

The deterministic phase found that explicit workflow and critique improved the benchmark more than nominal role labels. Its code and artifacts remain unchanged.

## 3. Phase 2 recap

The stochastic simulator crossed three operational model profiles with H0/H1/H2. Stronger harnesses helped all profiles, particularly the weakest; critique mostly improved risk recall, verification mostly improved controls, specialization was heterogeneous, and memory could help or anchor. See [Phase 2](phase2_model_vs_harness.md).

## 4. Hypotheses

Seven directions are locked in [`phase3_predictions.yaml`](../configs/phase3_predictions.yaml) before real results: differential harness benefit, critic risk effects, verifier control effects, modest specialization, memory/anchoring trade-offs, workflow cost, and residual model limitations.

## 5. Benchmark freeze

The observable [benchmark](../configs/phase3_benchmark.yaml), evaluator-only [labels](../evals/phase3_hidden_manifest.json), [protocol](../configs/phase3_protocol.yaml), predictions, and counterfactuals have SHA-256 entries in the [freeze manifest](../configs/phase3_freeze_manifest.json). A changed treatment requires a new version and separately named study.

## 6. Model configurations

The [example model configuration](../configs/phase3_models.example.yaml) uses neutral identifiers R0/R1/R2. Declared tiers are hypotheses; observed benchmark performance is reported separately. Endpoint and key values come from environment variables listed in [`.env.example`](../.env.example). No credential is logged.

## 7. Harness conditions

The main matrix reuses frozen `H0_minimal`, `H1_structured`, and `H2_strong` semantics from Phase 2. Prompt or harness improvements after inspection belong in exploratory conditions, not the primary comparison.

## 8. Experimental design

The unit is `model × harness × episode × repetition`. Smoke, pilot, and full presets change family coverage and repetitions without changing cell semantics. The plan prints cells, episode runs, call/token upper bounds, and configured cost limits before execution. Same-episode comparisons are paired.

## 9. Evaluation metrics

Answer metrics include research score, thesis direction, risk recall, scenario coverage, and counterfactual response. Control metrics include unsupported claims, invalid citations, evidence mismatch, unresolved contradictions, untraceable calculations, stale evidence, and unsupported confidence. Operations record calls, tokens, retries, latency, cache hits, and user-supplied monetary pricing.

## 10. Results

**NOT YET RUN.** The checked-in [`results/phase3/`](../results/phase3/) files are labeled placeholders with zero real calls and zero empirical runs.

## 11. Critic replication

The paired study holds other features constant and records risk recall, contradiction detection, beneficial/harmful revisions, false challenges, calls, tokens, latency, and cost. The claim that lower/mid-capability systems benefit more remains untested.

## 12. Verification replication

Verification off/on separates answer quality from control quality. Unsupported claims, invalid citations, mismatches, contradictions, calculation traceability, and unsupported confidence are evaluated independently of headline score.

## 13. Specialization replication

Single workflow and context-partitioned specialists use matched model-call budgets where practical. Role labels, context partitioning, parallel search, independent perspectives, and evidence allocation are recorded as distinct mechanisms.

## 14. Longitudinal memory

The preserved five-episode sequence compares stateless and persistent structured state. It tracks thesis history, evidence versions, invalidation conditions, confidence, unresolved questions, redundant research, forgetting, anchoring, and stale reuse.

## 15. Stability

Repeated runs report thesis and routing consistency plus score, risk-recall, citation, and tool-use variation. Provider seeds are recorded when available but never treated as a guarantee of determinism.

## 16. Calibration

Reliability bins, expected calibration error, and Brier score compare claim confidence with empirical correctness/support. Self-reported, heuristic, and empirically assessed confidence remain separate.

## 17. Premise resistance

The false-premise episode measures acceptance, correction, evidence seeking, appropriate hedging, and unsupported rationalization. Hidden truth is inaccessible to the research runtime.

## 18. Counterfactual consistency

Frozen pairs reverse leverage, cash flow, and spread evidence while holding wording and task stable. A materially reversed evidence state should change the conclusion.

## 19. Cost/quality trade-off

Hard limits cover total calls, calls per episode, tokens, retries, and optional estimated cost. Prices are never fabricated: monetary estimates exist only when the user supplies model pricing metadata.

## 20. Failure taxonomy

Raw calls preserve redacted provider output, parsed output, parse status, bounded repairs, usage, latency, and infrastructure errors. The [failure taxonomy](failure_taxonomy.md) labels real-model categories as hypothetical until an auditable call observes them.

## 21. Comparison with Phase 2 predictions

| Phase 2 finding | Phase 3 result | Replicated? |
|---|---|---|
| Strong harness benefit is larger for lower-capability profiles. | Not run. | not tested |
| Critique mainly improves risk discovery. | Not run. | not tested |
| Verification mainly improves control quality. | Not run. | not tested |
| Context partitioning gives modest heterogeneous gains. | Not run. | not tested |
| Memory reduces redundancy but can anchor. | Not run. | not tested |
| Strong harnesses impose substantial cost. | Protocol instruments cost; no observed values. | not tested |
| Harnesses do not eliminate model limitations. | Not run. | not tested |

Valid future labels are `yes`, `partially`, `no`, `inconclusive`, and `not tested`; directions must not be rewritten after results.

## 22. Limitations

Provider models can change without notice; some expose neither fixed versions nor seeds. Pricing, rate limits, response schemas, and token accounting vary. The benchmark is synthetic and small, evaluation rules are authored, model tiers are unverified, and call-budget matching cannot equalize latency or internal compute. No production, investment-performance, or general model-ranking claim follows from this protocol.

## 23. Next research questions

An approved pilot should preregister concrete provider/model identifiers, pricing, dates, budgets, and exclusions; run development episodes before frozen evaluation; distinguish provider failures from research failures; and publish all completed request IDs. Public-data extensions should remain separate from the synthetic confirmatory matrix.

## Reproducibility and privacy

Each executed run must record provider, model identifier/version when exposed, date, temperature, seed, prompt and harness versions, benchmark hash, code commit, request IDs, usage, latency, and result status. Cache keys include treatment identity and repetition. Successful calls resume from a versioned local cache; raw and normalized outputs are separate. Provider-side updates can still prevent exact reproduction.

Only repository synthetic/public benchmark inputs may be sent by default. Proprietary, confidential, or user data must not be transmitted. API keys and authorization headers are redacted and raw caches are ignored by Git.
