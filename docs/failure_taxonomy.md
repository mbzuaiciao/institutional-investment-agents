# Phase 2 failure taxonomy

Phase 2 records failures before and after harness controls. An **injected failure** is produced by the stochastic model profile. An **unresolved failure** remains in the research artifact after workflow constraints, critique, verification, or revision. A detected failure may be visible to the harness even when the model does not repair it.

“Model,” “harness,” and “both” below identify the primary causal surface, not exclusive blame. For example, a model may emit an unsupported claim, while a weak harness permits it to pass silently.

| Failure | Meaning | Detection | Primary surface | Relevant metrics |
|---|---|---|---|---|
| Retrieval miss | Relevant evidence was not retrieved. | Compare retrieved IDs with episode-relevant evidence. | Both | evidence coverage |
| Evidence omission | Available relevant evidence was omitted from reasoning. | Compare claim lineage with required evidence. | Model | risk recall, claim support |
| Planning failure / premature synthesis | A thesis was formed before required work completed. | Inspect plan completion at synthesis. | Both | task completion, workflow steps |
| Routing error | A task was assigned to the wrong capability or role. | Compare route with deterministic task requirements. | Both | routing accuracy |
| Incorrect tool selection | The chosen tool cannot answer the required calculation. | Validate the tool contract against the episode. | Model | calculation accuracy, tool calls |
| Missed tool | A necessary deterministic calculation was attempted without its tool. | Compare `requires_tool` with recorded calls. | Both | calculation accuracy |
| Duplicate tool call | A tool repeats without new normalized inputs. | Compare tool names and arguments. | Model | tool calls, cost units |
| Calculation error | A quantitative result disagrees with deterministic ground truth. | Recompute with the validated tool. | Model | calculation accuracy |
| Evidence-interpretation failure | Relevant evidence is present but misunderstood or ignored. | Compare required episode signals with claims and risks. | Model | risk recall, directional accuracy |
| Ignored contradiction | Conflicting evidence is neither surfaced nor reconciled. | Compare contradiction labels with state and thesis. | Both | contradiction detection, unresolved contradictions |
| Unsupported claim | A claim has no valid evidence or calculation lineage. | Run deterministic claim-support checks. | Both | unsupported claims, support rate |
| Citation mismatch | A citation exists but does not support its claim. | Compare cited evidence with required support. | Both | invalid citations, citation validity |
| Synthesis failure | The conclusion is premature, directionally wrong, or omits material risk. | Compare thesis direction and risk set with ground truth. | Model | directional accuracy, risk recall |
| Missed risk | A labeled risk factor is absent from the thesis. | Compare thesis risks with episode labels. | Model | risk-factor recall |
| Malformed structured output | Output violates the requested schema. | Apply Pydantic/schema validation. | Both | structured-output validity |
| Stale-evidence failure | Expired or superseded evidence affects the current conclusion. | Apply freshness classification and inspect lineage. | Both | stale-evidence usage rate |
| Failed revision | A detected issue remains after revision was requested. | Compare pre- and post-revision failures. | Model | correct revisions, revision cycles |
| Critique failure | Critique misses a real issue or introduces a false challenge. | Compare challenges with episode risk/contradiction labels. | Both | risk recall, false challenges, unnecessary revisions |
| Verification failure | A mechanical or assisted check misses an existing support problem. | Compare verifier output with known injected failures. | Both | detection rate, unsupported claims, invalid citations |
| Incorrect confidence | Heuristic confidence is inconsistent with unresolved errors. | Join confidence components with verification results. | Model | inappropriate-confidence rate |
| Overconfident unsupported claim | An unsupported claim is expressed with excessive confidence. | Join support status with claim confidence. | Model | inappropriate confidence, unsupported claims |
| Memory failure | Prior state is forgotten, stale, or incorrectly anchors an update. | Compare current state with the longitudinal episode history. | Both | forgetting, anchoring, revision quality |

The executable mapping is [`failure_taxonomy.py`](../src/institutional_investment_agents/failure_taxonomy.py). It allows analyses to move beyond “architecture A scored higher” toward “architecture A prevented, detected, or repaired these failure types.”
