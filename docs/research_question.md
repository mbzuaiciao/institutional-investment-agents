# Research question

## Central question

> What agent architecture actually improves institutional investment research rather than merely producing more elaborate-looking answers?

The question separates architectural activity—more roles, steps, messages, and orchestration—from research quality. In this project, quality means completing the required analysis, reaching the synthetic directional target, identifying known risks, grounding claims, and preserving an auditable process.

The current evidence comes from deterministic synthetic cases. “Supported” below means supported within this benchmark, not established for production LLM systems.

## Phase 1 hypotheses and evidence

| Hypothesis | Current status | Evidence and interpretation |
|---|---|---|
| **H1: Specialist decomposition improves research quality.** | Unsupported in the controlled comparison. | [`run_single_vs_multi.py`](../experiments/run_single_vs_multi.py) holds structured workflow, retrieval, tools, cases, and seeds constant while changing only task ownership. Both configurations score about 91.67, with identical risk recall and support. Role labels alone do not improve the deterministic policy. |
| **H2: Explicit workflow constraints improve completeness and grounding.** | Supported in the current benchmark. | [`run_workflow_ablation.py`](../experiments/run_workflow_ablation.py) raises quality from about 78.13 to 91.67, eliminates the observed unsupported claim, raises evidence coverage from 0% to 75%, and raises risk recall from about 45.83% to 66.67%. Structured outputs and explicit tasks are jointly changed in this comparison and should not be interpreted as separately identified effects. |
| **H3: A critic improves risk identification.** | Supported for the synthetic cases. | The capstone comparison from C to D raises mean risk recall from 66.67% to 93.75% and quality from 91.67 to 98.44, while adding one step. This result reflects risks encoded in the deterministic critic policy and synthetic ground truth. |
| **H4: Evidence verification reduces unsupported claims.** | Unresolved as an intervention effect. | D and E both have 100% claim support and zero unsupported claims because upstream structured claims are already supported. Verification adds a visible control event and would flag unsupported state, as tested in the test suite, but the capstone cannot show a reduction from an already-zero error rate. |
| **H5: Persistent state improves research quality.** | Unsupported in the current setting. | E and F have identical reported metrics. The workflow already uses explicit intra-run state, and the benchmark contains no longitudinal episodes where cross-run memory could help. |
| **H6: Architectural sophistication does not necessarily improve performance.** | Supported as a benchmark observation. | Single and specialist ownership tie when only labels change; verification and persistent-state variants add stages without raising quality. Sophistication can still improve control or auditability even when the score is unchanged. |

## What the hypotheses imply

The evidence is consistent with a more precise proposition:

> Architecture matters primarily when it changes information flow, constraints, or error correction—not merely when it changes role labels.

Explicit tasks change required coverage. Tools change how arithmetic enters the process. A critic changes error discovery. A verifier changes what is mechanically visible to reviewers. By contrast, assigning the same work to different nominal roles need not alter the research artifact.

These conclusions are bounded by the implementation. The deterministic policy may understate benefits that emerge when real models have different prompts, context limits, or specialist capabilities. The next research phase should cross model capability with harness strength as described in [future work](future_work.md).

## Phase 2 question and hypotheses

Phase 2 asks: **How much performance comes from the model, and how much from the harness?** It pre-registers eight hypotheses covering compensatory harness effects, residual workflow value for strong models, capability-dependent critique, verification under natural errors, context-changing specialization, longitudinal memory, workflow cost, and model-limited failures.

The current synthetic evidence supports H1, H2, H4, H7, and H8 descriptively; partially supports H3 and H6; and conditionally supports H5. In particular, weak/H2 outperforms medium/H0 but remains below strong/H0. The [Phase 2 report](phase2_model_vs_harness.md) gives exact definitions, results, and limitations rather than folding these findings back into Phase 1.
