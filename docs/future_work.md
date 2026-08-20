# Future work

The next research stages should preserve the current controlled baseline and add complexity one source at a time. Each phase should retain run-level traces, fixed comparison sets, and component metrics rather than relying on memo preference alone.

## Phase 1 — Real LLM backends

Implement optional adapters behind `ModelBackend` and compare several real models under identical questions, evidence, tools, prompts, budgets, and workflow configurations. Record sampling parameters, model versions, token use, latency, failures, and cost.

The core question is:

> How much performance comes from model capability versus harness capability?

Repeated runs are necessary because real backends are stochastic. Evaluation should include unsupported synthesis, incorrect tool selection, recovery from tool errors, and variance across seeds—not only mean quality.

## Phase 2 — Public real-world data

Add source-specific adapters for legally and practically usable public material:

- SEC filings and exhibits;
- issuer annual reports, earnings releases, and investor presentations;
- Treasury and FRED rates/macro series; and
- public bond or credit proxies where availability and terms permit.

Every adapter should preserve as-of time, retrieval timestamp, document identity, and source locator. Public inputs should complement, not silently replace, the synthetic benchmark. The project should not imply access to proprietary Bloomberg, FactSet, or Refinitiv data.

## Phase 3 — Dynamic research episodes

Move from static cases to event sequences. Introduce new information mid-analysis, contradictory documents, stale data, missing fields, tool failures, and partially completed tasks. Measure whether the workflow detects the change, invalidates dependent claims, reruns calculations, revises the thesis, and records why.

Useful episode types include earnings surprises, refinancing announcements, rating actions, restatements, abrupt rate moves, and corrections to an earlier source. This phase should add revision accuracy, stale-claim rate, recovery success, and time-to-resolution metrics.

## Phase 4 — Longitudinal memory

Test persistent state across multiple research dates for the same issuer. Compare fresh-start retrieval with versioned memory under controlled updates. Memory experiments need expiry rules, source versioning, issuer isolation, correction semantics, and safeguards against stale claims contaminating new work.

This phase can properly test the current unresolved question: whether persistence improves research when a case spans multiple episodes rather than one deterministic run.

## Phase 5 — Human expert evaluation

Recruit experienced credit analysts, portfolio managers, or risk professionals to review blinded artifacts. Compare agent outputs with expert judgments on evidence relevance, calculation correctness, risk coverage, thesis usefulness, calibration, and review effort.

Expert disagreement should be recorded rather than collapsed into a single “gold” label. Evaluation should measure whether traces reduce review time or improve error detection, and whether approval interfaces create automation bias.

## Phase 6 — Harness versus model capability

Run a controlled matrix:

```text
                         Weak harness      Strong harness
Weaker model             weak / weak       weak / strong
Stronger model           strong / weak     strong / strong
```

The weak and strong harnesses must differ through declared mechanisms—structured state, required evidence, tools, critique, verification, and approval—not through hidden access to different data. Model budgets and evidence sets should be matched where possible.

This matrix should become a major follow-on direction. It can test whether a strong harness compensates for specific model weaknesses, whether a capable model is wasted inside a weak process, and where model and harness improvements interact rather than add independently.

## Cross-cutting priorities

Future work should also expand the benchmark, add factorial experiments, instrument duplicate work and revisions, calibrate confidence, test verifier false-positive and false-negative rates, model security boundaries, and assess reproducibility across operating environments. The existing [literature map](../notes/literature_map.md) provides an initial research index and should be updated only with verified primary sources.
