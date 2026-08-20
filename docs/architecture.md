# Architecture

## Phase 1 end-to-end system

The implementation makes orchestration explicit in ordinary Python. No agent framework is required to understand the control flow.

```text
Research Question
       │
       ▼
Research Planner ──────────────► deterministic router
       │
       ├──────── Local retrieval + evidence IDs
       ├──────── Typed financial / portfolio tools
       │
       ▼
┌─────────────────────────────┐
│ Credit Analyst              │
│ Macro / Rates Analyst       │
│ Relative-Value Analyst      │
│ Evidence Researcher         │
└─────────────────────────────┘
       │
       ▼
Shared Research State
       │
       ▼
Thesis Synthesizer
       │
       ▼
Critic / Challenge Agent
       │
       ▼
Evidence Verifier
       │
       ▼
Human Approval Gate
       │
       ▼
Research Memo + Audit Trace
```

Tools execute during research so calculations are available to claims and synthesis. The verifier then checks that calculated claims retain their tool-result pointers. The orchestration is implemented in [`workflow.py`](../src/institutional_investment_agents/workflow.py), with state transitions in [`state.py`](../src/institutional_investment_agents/state.py).

## Components and boundaries

### Model/backend

A backend maps a prompt and context to generated text. [`ModelBackend`](../src/institutional_investment_agents/model.py) is a protocol, while `DeterministicResearchModel` supplies an offline, repeatable policy for tutorials and tests. A backend is not itself an agent: it has no task state, tool environment, transition policy, or termination rule.

### Agent

An agent combines a policy with observations, actions, state transitions, and termination. [Tutorial 01](../tutorials/01_research_agent.py) exposes those elements directly. In the integrated workbench, agent behavior is deliberately constrained by typed state and deterministic policies rather than hidden inside a long prompt.

### Specialist role

`AgentRole` identifies responsibility for a contribution: credit, macro/rates, relative value, evidence, synthesis, critique, verification, or human review. A role changes task ownership and audit attribution. It does not automatically confer a different model, private memory, or greater capability. This distinction is central to the controlled null result for nominal specialization.

### Workflow

The workflow defines ordering and gates: start, plan, retrieve, calculate, research, synthesize, challenge, verify, approve, memo, finish. [`WorkflowConfig`](../src/institutional_investment_agents/workflow.py) enables architecture ablations without replacing the underlying data or evaluator. A workflow can improve research by requiring missing tasks or checks even when the model policy is unchanged.

### Shared state

`ResearchState` is a typed workspace containing the question, plan, completed tasks, evidence, claims, tool results, observations, risks, challenges, open questions, contradictions, assumptions, and audit events. It is not chat history. Objects are referenced by stable IDs, and support must enter state before a dependent claim can be added. The schemas are defined in [`schemas.py`](../src/institutional_investment_agents/schemas.py).

### Tools

[`ToolRegistry`](../src/institutional_investment_agents/tools.py) validates arguments and executes deterministic arithmetic for spreads, credit ratios, spread position, expected loss, and first-order portfolio impact. Each call and result is logged. Tools remove avoidable arithmetic variability and expose units and inputs; they do not decide whether a bond is attractive.

### Critic

The critic is an adversarial research role, not a prose editor. It records a `Challenge` against a claim or assumption, identifies fragile reasoning or alternative explanations, and can add omitted risk factors. Challenges remain inspectable objects with severity, conflicting evidence, and resolution status.

### Verifier

[`verify_state`](../src/institutional_investment_agents/verification.py) checks claim support pointers, missing objects, a lexical evidence-support heuristic, calculated-result lineage, and unresolved contradictions. It is a mechanical control, not a truth oracle. Verification can reveal an unsupported claim; it cannot make the claim correct.

### Audit layer

Every important transition emits a sequenced `AuditEvent` with an actor, object ID, and structured details. Evidence, tool results, and claims have separate identities, allowing the trace to reconstruct dependencies. See [auditability and controls](auditability_and_controls.md).

### Evaluation harness

[`evaluation.py`](../src/institutional_investment_agents/evaluation.py) runs the same issuer cases under different `WorkflowConfig` settings, aggregates component metrics, and writes deterministic JSON, Markdown, and figures. The harness evaluates both outcomes and process behavior; it is separate from the research workflow it measures.

## Why more agents do not imply better research

Adding role labels can leave information, tools, constraints, and error-correction behavior unchanged. It may also add duplicate work, inconsistent assumptions, or operational cost. The controlled experiment therefore holds workflow structure, retrieval, tools, cases, and seeds constant while changing only single-agent versus specialist ownership. The resulting scores are equal. Improvements appear when architecture changes what information must be gathered, how claims are grounded, or how the thesis is challenged. That is a narrower and more testable claim than “multi-agent systems are better.”

## Phase 2 extension

Phase 2 adds a typed operation layer above the preserved Phase 1 backend:

```text
Model profile                    Harness profile
weak / medium / strong    ×      H0 / H1 / H2
         │                              │
         └────── typed ModelRequest ────┘
                        │
              hard research episode
                        │
            injected model failures
                        │
        harness prevent / detect / repair
                        │
      quality + control + failure + cost trace
```

`ModelOperation` covers planning, task execution, routing, retrieval, evidence interpretation, tool selection, claim generation, synthesis, critique, revision, and verification assistance. [`StochasticSyntheticModel`](../src/institutional_investment_agents/stochastic_model.py) maps profile capabilities to seeded failures. [`phase2_runner.py`](../src/institutional_investment_agents/phase2_runner.py) records failures before and after harness controls, keeping model-side error generation distinct from prevention, detection, and repair.

H0/H1/H2 are operational feature bundles in [`harness.py`](../src/institutional_investment_agents/harness.py), not adjectives. Hard episodes, evidence versions, longitudinal state, confidence components, and cost accounts are typed objects. The optional real-model adapter satisfies the same backend interface but is outside default/CI execution.
