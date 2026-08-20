# Auditability and controls

## The audit question

The trace is designed to answer:

> Who or what made which claim, based on what evidence or calculation, at which stage of the research process?

An ordered log alone is insufficient if objects have no stable identity. The workbench therefore combines typed objects with sequenced events.

## Identity and lineage

- **Evidence IDs** identify local source records containing a title, text, source, locator, issuer scope, date, and tags. Retrieval does not turn text directly into a claim.
- **Claim IDs** identify atomic assertions and label them factual, calculated, inferred, or judgmental. Claims retain evidence IDs, tool-result IDs, confidence, assumptions, and author role.
- **Tool-call IDs** preserve the requested tool, validated arguments, and actor.
- **Tool-result IDs** preserve the corresponding call, output, units, and inputs. Calculated claims must point to these results.
- **Provenance** is carried by evidence source and locator and surfaced as citations in the final memo.
- **Assumptions** are first-class fields on claims and structured state rather than hidden prompt text.
- **Challenges** identify a target claim where possible, issue type, severity, explanation, conflicting evidence, and resolution status.
- **Verification results** summarize support rate, citation validity, evidence coverage, unsupported IDs, missing objects, and contradictions.
- **Approval decisions** record approve/revise/reject status, reviewer, rationale, and conditions.

`StateManager` in [`state.py`](../src/institutional_investment_agents/state.py) enforces an important ordering rule: support objects must exist in shared state before a dependent claim can be added. [`schemas.py`](../src/institutional_investment_agents/schemas.py) additionally prevents factual claims without evidence pointers and calculated claims without tool-result pointers.

## Event sequence

A full run can emit:

```text
research_started
plan_created
retrieval_performed
evidence_added
tool_called
tool_result
claim_created
task_completed
thesis_created
challenge_created
verification_completed
approval_requested
approval_decision
memo_generated
research_completed
```

Every event has a contiguous sequence number, actor, optional object ID, and structured details. The test suite verifies sequence integrity and that claim-creation events correspond to state claims. Timestamps are optional and omitted from deterministic capstone runs so reproducibility is not broken.

## Why auditability matters

Institutional decisions may be reviewed after market conditions, personnel, or models have changed. Analysts and control functions need to distinguish what was known at the time, which calculation was used, what assumptions were accepted, and who approved the artifact. Auditability supports reproducibility, challenge, incident analysis, model-risk review, and clear accountability.

An audit trail does not guarantee good research. It can faithfully record a poor process. Its value is that errors and dependencies become inspectable rather than being compressed into an opaque final answer.

## Human control modes

**Human-in-the-loop** means a consequential transition requires an explicit human decision. In a production analogue, publication or portfolio use could be blocked until approval.

**Human-on-the-loop** means a person supervises an operating system, receives exceptions, and can intervene, but ordinary transitions may proceed automatically.

**Merely presenting output to a human** provides visibility without a required decision, authority, or recorded response. It is not meaningful oversight by itself.

The prototype represents a human-in-the-loop gate structurally, but its reviewer is a deterministic policy for reproducibility. It demonstrates the contract and trace, not real institutional governance. Production use would require authenticated identities, permissions, escalation, retention, and evidence-access controls.
