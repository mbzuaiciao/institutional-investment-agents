# Project overview

## What this project is

Institutional Investment Agents is an executable research workbench for studying agent architecture in a demanding decision-support setting: five-year corporate-credit research. It asks whether changes to an agent harness improve the research process, rather than judging a system only by how polished its final memo appears.

The default system is offline and deterministic. It plans a research question, retrieves synthetic documents, invokes validated financial tools, coordinates structured research contributions, forms a conditional thesis, challenges that thesis, verifies claim support, passes through an approval policy, and emits a typed memo plus an ordered audit trace. The implementation is in [`src/institutional_investment_agents/`](../src/institutional_investment_agents/); the integrated entry point is [`prototype/run_research.py`](../prototype/run_research.py).

This is an experimental research workbench. It is not a trading system, an autonomous investment manager, or investment advice. Its data and conclusions are synthetic.

## Why institutional credit research

Institutional investment research is a useful agentic-AI testbed because it is a constrained process, not merely an answer-generation task. A credible workflow must:

- distinguish source facts, calculations, inferences, and judgments;
- preserve evidence and provenance across multiple tasks;
- use deterministic tools for arithmetic;
- compare fundamental risk with market compensation;
- examine downside scenarios and thesis invalidation conditions;
- expose contradictions, uncertainty, and missing information; and
- support review by an accountable human.

Corporate credit makes these requirements concrete. Credit analysis links issuer fundamentals and capital structure to spreads, rates, refinancing conditions, peer value, loss risk, and portfolio sensitivity. A weak issuer can still offer attractive compensation, while a strong issuer can be unattractive at the wrong price. That tension makes the domain better suited to testing research architecture than generic financial summarization.

## What is implemented

The prototype operates on a deterministic universe of ten synthetic issuers and a local document corpus. Typed schemas represent questions, plans, tasks, evidence, claims, calculations, risks, scenarios, challenges, approvals, memos, and audit events. The workbench includes:

- local retrieval with stable evidence IDs and source locators;
- validated spread, leverage, coverage, expected-loss, and portfolio-impact tools;
- rule-based task routing across credit, macro/rates, relative-value, and evidence roles;
- a shared structured research state;
- an adversarial critic and a mechanical evidence verifier;
- a structured approval decision; and
- a configurable evaluation harness.

The twelve scripts in [`tutorials/`](../tutorials/) build these ideas progressively, from a minimal policy/environment/state loop through the complete workbench. They reuse the same package as the prototype rather than forming a separate demonstration project.

## What the experiments test

The experiment scripts in [`experiments/`](../experiments/) isolate or progressively combine specialist ownership, explicit workflow structure, deterministic tools, critique, verification, and persistent state. The capstone evaluates six architectures over three seeds and four issuers, for 72 runs in total. It records evidence, behavior, quality, and cost-proxy metrics; see [experiment design](experiment_design.md) and [evaluation framework](evaluation_framework.md).

## Main finding

> The project found stronger gains from workflow structure and adversarial critique than from nominal multi-agent specialization.

In the controlled single-versus-specialist experiment, changing only role ownership produced no measurable score difference. By contrast, explicit workflow structure raised research quality from about 78.13 to 91.67, eliminated the unsupported claim observed in the free-form configuration, and increased risk recall from about 45.83% to 66.67%. In the capstone, adding the critic raised risk recall from about 66.67% to 93.75%.

Verification and persistent intra-run state are important controls, but neither raised the current benchmark score when preceding claims were already supported and state was already explicit. Those null results are informative: architecture appears to matter when it changes information flow, constraints, or error correction—not simply when it adds role labels or stages. The complete numbers and their interpretation are in [results and findings](results_and_findings.md).
