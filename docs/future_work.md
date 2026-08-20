# Future work after Phase 2

Phase 1 established a deterministic harness baseline. Phase 2 added controlled stochastic model profiles, hard episodes, model × harness attribution, focused controls, and longitudinal state. The next work should validate those synthetic mechanisms against observed models and real public information without erasing the controlled benchmarks.

## Stage A — Repeated real-model factorials

Use the optional provider-neutral backend to compare multiple real models under identical evidence, tools, prompts, call budgets, and H0/H1/H2 profiles. Record provider/model version, sampling parameters, token use, latency, cost, refusals, malformed outputs, and tool errors.

Runs must be repeated because real backends are stochastic. The central test remains:

> How much performance comes from model capability versus harness capability?

Synthetic profiles should be calibrated against observed failure frequencies rather than retrospectively adjusted to reproduce desired conclusions.

## Stage B — Public real-world data

Add source-specific adapters for legally and practically usable public material:

- SEC filings and exhibits;
- issuer annual reports, earnings releases, and investor presentations;
- Treasury and FRED rates/macro series; and
- public bond or credit proxies where terms and coverage permit.

Every adapter should preserve as-of time, retrieval time, document version, entity identity, and source locator. The project should not imply access to proprietary Bloomberg, FactSet, or Refinitiv data.

## Stage C — Dynamic and adversarial episodes

Expand beyond five-step synthetic sequences. Introduce restatements, conflicting identifiers, document corrections, delayed filings, tool outages, malicious prompt content in retrieved documents, missing prices, and simultaneous macro/issuer shocks. Measure stale-claim invalidation, recovery success, revision accuracy, and time to resolution.

## Stage D — Longitudinal memory governance

Test versioned memory over months of issuer updates. Add expiry policies, source corrections, cross-issuer isolation, user edits, access controls, retention limits, and recovery from corrupted state. Measure both benefit and anchoring: persistence should not receive credit merely for remembering an obsolete thesis.

## Stage E — Human expert evaluation

Recruit experienced credit analysts, portfolio managers, and risk professionals to review blinded artifacts. Measure evidence relevance, calculation correctness, risk coverage, calibration, decision usefulness, and review effort. Record expert disagreement rather than forcing a single gold answer.

Tests should ask whether audit traces and verification reduce review time or improve error detection, and whether approval interfaces create automation bias or rubber-stamping.

## Stage F — Model/harness interaction under matched budgets

Repeat the full matrix with actual models:

```text
                         Weak harness      Strong harness
Weaker model             weak / weak       weak / strong
Stronger model           strong / weak     strong / strong
```

Match evidence, tools, context allowance, and total model calls where feasible. Report quality per cost and failure-specific effects. Test whether a stronger harness compensates for model weaknesses, whether capable models are wasted inside weak processes, and where interaction effects emerge.

## Cross-cutting priorities

Increase seeds and episode diversity; use bootstrap or hierarchical intervals where appropriate; instrument semantic duplicate work; evaluate verifier false positives and negatives; calibrate confidence components; measure false and harmful critiques; add security boundaries; and publish machine-readable preregistrations before expensive real-model runs.

The [Phase 2 report](phase2_model_vs_harness.md) and [failure taxonomy](failure_taxonomy.md) define the baseline that future studies should preserve and challenge.
