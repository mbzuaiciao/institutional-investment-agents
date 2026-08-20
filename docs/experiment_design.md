# Experiment design

## Controlled first phase

The first phase prioritizes causal clarity and reproducibility over live-market realism. All default runs use [`generate_universe(seed)`](../src/institutional_investment_agents/dataset.py), local retrieval, deterministic tools, and deterministic workflow policies. No network, API key, or licensed dataset is required.

The universe contains ten synthetic issuers across multiple sectors, issuer fundamentals, ratings, five-year bond and CDS pricing, benchmark rates, spread history, duration, macro assumptions, issuer documents, news events, expected thesis direction, and known risk labels. Accounting and market relationships are generated coherently and tested, but they remain author-designed synthetic ground truth.

`DeterministicResearchModel` provides a model-backend abstraction without paid calls. Most integrated decisions are explicit policies in [`workflow.py`](../src/institutional_investment_agents/workflow.py), which makes the effect of harness settings inspectable. Determinism was used first to:

- eliminate sampling noise while validating metrics and state transitions;
- make failures exactly reproducible;
- avoid confounding model changes with workflow changes;
- permit offline tests and tutorials; and
- create a stable baseline for later real-model comparisons.

## Cases, seeds, and run count

The capstone uses seeds `17`, `23`, and `41` and issuer IDs `NRT`, `CRH`, `BAY`, and `VTX`. Six variants × three seeds × four issuers produce **72 runs**. Every run records the seed, dataset version, issuer, variant, configuration, and metrics in [`results/capstone.json`](../results/capstone.json). Timestamps are omitted so deterministic artifacts compare byte-for-byte.

## Capstone variants

The exact implemented labels are:

| Variant | Implemented name | Principal capability added |
|---|---|---|
| A | Observation/context-only baseline | Retrieval context without structured output, tools, critic, or verifier |
| B | Single research agent with tools | Structured claims and deterministic financial tools |
| C | Structured specialist workflow | Explicit institutional tasks and specialist ownership |
| D | Specialists plus critic | Adversarial challenge and additional risk discovery |
| E | Specialists, critic and verifier | Mechanical verification event and result |
| F | Full workflow with persistent state | Persistent-state flag in the full configuration |

The capstone is a progressive architecture comparison, not a sequence of pure one-variable causal estimates. For example, B to C changes both task structure and specialist ownership. The standalone ablations address narrower questions.

## Held-constant comparisons

[`run_single_vs_multi.py`](../experiments/run_single_vs_multi.py) is the strict test of specialization. It holds issuer cases, seeds, evidence corpus, retrieval, tools, structured output, explicit workflow, critic setting, and verifier setting constant. Only `specialists_enabled` and the corresponding architecture/actor labels change. The measured tie therefore means nominal ownership alone did not help this policy.

[`run_workflow_ablation.py`](../experiments/run_workflow_ablation.py) holds specialists, retrieval, tools, critic, verifier, data, and cases constant. It jointly changes free-form versus structured outputs and implicit versus explicit task workflow. The result identifies the combined workflow-constraint package, not the separate contribution of each switch.

[`run_critic_ablation.py`](../experiments/run_critic_ablation.py) compares C with D, changing the critic setting. [`run_evidence_ablation.py`](../experiments/run_evidence_ablation.py) compares D with E, changing the verification setting. The latter tests the incremental verifier when upstream claims are already supported.

## Metrics

The capstone currently emits task completion, directional accuracy, risk-factor recall, claim support rate, citation validity, evidence coverage, unsupported-claim count, unresolved contradictions, tool-call count, audit steps, and a transparent composite research-quality score. The score weights direction at 30%, risk recall at 25%, claim support at 25%, and task completion at 20%. Component metrics should be inspected rather than treating the composite as an objective truth.

Tests separately validate financial calculations, routing, schemas, support enforcement, audit sequencing, and reproducibility. Other desired measures—duplicate work, scenario coverage, revisions, latency, and model cost—are part of the evaluation design but are not all emitted by the current deterministic capstone. See [evaluation framework](evaluation_framework.md).
