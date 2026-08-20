# Product workbench

## Purpose

The **Institutional Investment Research Workbench** turns the Phase 1–3 research engine into a usable local analyst workflow. An analyst can select a synthetic issuer, ask a credit question, approve a typed plan, execute the existing workflow, inspect intermediate artifacts, apply human review, and export an audit-ready package without using Python directly.

## Install and launch

```bash
uv sync --all-groups
uv run streamlit run workbench/app.py
```

The mandatory demo path is local, CPU-only, deterministic, and requires no API key.

## Analyst journey

```text
Issuer and source selection
  → research question
  → typed plan review and approval
  → evidence retrieval and local uploads
  → deterministic tools and specialist observations
  → thesis and scenarios
  → adversarial challenge
  → verification controls
  → explicit human decision
  → Markdown / JSON / CSV exports
```

The interface updates progress only when the underlying synchronous engine enters a real stage. It does not simulate streaming or expose private model chain-of-thought.

## Application architecture

| Layer | Responsibility |
|---|---|
| `workbench/app.py` | Page composition and session bootstrap |
| `workbench/session.py` | Session-owned mutable state and reset behavior |
| `workbench/services.py` | Thin facade over `ResearchWorkbench`, uploads, review events, and exports |
| `workbench/components/sidebar.py` | Issuer, backend, workflow, sources, upload, and reset controls |
| `workbench/components/input_plan.py` | Question editing, plan review/approval, and actual stage progress |
| `workbench/components/research_views.py` | Thesis, scenarios, evidence, claims, calculations, specialist work, critic, and verifier |
| `workbench/components/review_export.py` | Audit filtering, human decision, diagnostics, and downloads |

The product reuses [`workflow.py`](../src/institutional_investment_agents/workflow.py), typed [`schemas.py`](../src/institutional_investment_agents/schemas.py), deterministic tools, retrieval, verification, and audit events. The only engine extension allows an explicit typed question, additional evidence, plan preview, and stage callback.

## Data sources and uploads

Ten bundled synthetic issuers are immediately available with sector, rating, leverage, coverage, cash flow, bond spread, CDS, duration, and synthetic documents. Local UTF-8 `.txt`, `.md`, and `.csv` files can augment this corpus. Each receives a deterministic evidence ID, original filename, row/document locator, and issuer association.

Uploads remain local to the in-memory session, never silently replace bundled evidence, and are not sent externally in deterministic mode. PDF and OCR are intentionally excluded from the first prototype.

## Inspectable research artifacts

The app presents:

- plan tasks and owners;
- evidence excerpts, dates, provenance, and claim use;
- factual, calculated, inferred, and judgment claims with confidence and support;
- deterministic tool inputs and results;
- structured specialist observations;
- conclusion, bull/base/bear scenarios, risks, invalidation conditions, and unresolved questions;
- critic challenges with analyst-controlled resolution state;
- claim support, evidence coverage, citation validity, unsupported claims, and contradictions;
- filterable audit events and raw JSON.

## Human control

Research cannot execute until the plan is explicitly approved. The final human state is independent of the engine's deterministic policy gate and supports Not reviewed, Approved, Revision requested, and Rejected. Reviewer identity and note are recorded as an audit event. Challenge statuses support accepted, resolved, unresolved, and dismissed.

## Exports

The current session can produce:

- `research_memo.md`;
- `research_session.json`;
- `audit_trace.json`;
- `evidence_table.csv`; and
- `claims.csv`.

The Markdown memo includes only available session sections and contains the question, issuer overview, fundamentals, capital structure, market pricing, relative value, macro context, scenarios, thesis, opposing evidence, risks, invalidation conditions, calculations, unresolved questions, confidence, evidence table, verification, human review, and audit metadata.

## Backend behavior

The deterministic backend is the only enabled product backend and provides the complete no-API path. The Phase 2 stochastic simulator is correctly described as evaluation-only. The Phase 3 real-model runner remains optional and experiment-focused; the application does not bypass its live gate, resource limits, or credential rules and does not expose credentials.

## Error handling

Expected user errors—empty questions, malformed or unsupported uploads, unavailable backends, missing plan approval, and export problems—are shown as concise messages. Technical details are retained under a diagnostics expander instead of placing stack traces in the primary workspace.

## Limitations

This is a single-user local prototype with in-memory sessions. Synthetic research is not investment advice. Uploaded evidence is available for provenance and inspection, but the deterministic policy is not a general document-understanding model. Verification is partly lexical. There is no authentication, shared persistence, licensed market data, order execution, portfolio management, robust PDF ingestion, or real-model memo flow in the UI.
