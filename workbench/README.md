# Institutional Investment Research Workbench

The workbench is a local Streamlit interface over the repository's existing typed research engine. It is not a separate chatbot or orchestration implementation.

## Launch

```bash
uv sync --all-groups
uv run streamlit run workbench/app.py
```

Open the local URL printed by Streamlit. No API credentials or GPU are required for the deterministic demo.

## Demo workflow

1. Choose one of ten synthetic issuers.
2. Use or edit the five-year credit research question.
3. Select H0, H1, or H2 workflow controls.
4. Prepare and inspect the structured plan.
5. Approve the plan and run research.
6. Inspect the thesis, scenarios, evidence, claims, specialist observations, calculations, challenge, verification, and audit trace.
7. Record challenge resolutions and an explicit human decision.
8. Download Markdown, JSON, audit JSON, evidence CSV, and claims CSV artifacts.
9. Start a new session from the sidebar.

## Local research material

The optional upload mode accepts UTF-8 `.txt`, `.md`, and `.csv` files up to 5 MiB. CSV inputs require a header and are limited to 200 rows. Each document or row receives a stable evidence ID, filename-based provenance, and locator. Uploaded evidence augments bundled evidence and does not overwrite it.

Files remain in the Streamlit session and are not persisted by the workbench. The deterministic demo sends no data to an external service.

## Backend status

- **Deterministic demo backend:** available and used for the complete product flow.
- **Stochastic research backend:** retained for Phase 2 evaluation, not presented as a memo backend.
- **Real model backend:** Phase 3 remains a guarded experimental runner. The UI does not weaken the `--execute` and `PHASE3_ENABLE_LIVE_RUNS=YES` gates or claim that a configured experiment runner is a production memo backend.

## Architecture

`app.py` composes focused components. `session.py` owns all mutable session state. `services.py` is the only facade between the UI and the existing package APIs. Components render typed plans, evidence, claims, tool results, observations, theses, challenges, verification results, and audit events.

## Human oversight

Plan approval is required before execution. Challenge resolution and the final human state—Not reviewed, Approved, Revision requested, or Rejected—are explicit. Decisions and notes become audit events and appear in exports. The deterministic engine's internal approval gate is not presented as a substitute for the user's decision.

## Limitations

The demo data and conclusions are synthetic and are not investment advice. Uploaded text is added to provenance but the deterministic policy does not semantically learn from arbitrary prose. Verification is rule/lexical based. Sessions are in-memory and reset on server/browser-session loss. PDF/OCR, authentication, collaboration, persistent storage, and real-model memo execution are outside this prototype.
