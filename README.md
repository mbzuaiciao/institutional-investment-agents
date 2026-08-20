# Institutional Investment Agents

An executable, from-first-principles research project for asking a deliberately uncomfortable question:

> What agent architecture actually improves institutional investment research rather than merely producing more elaborate-looking answers?

The concrete laboratory is synthetic five-year corporate credit research. The system gathers evidence, performs deterministic calculations, maintains claims and assumptions, challenges a thesis, verifies provenance, passes through an approval gate, and emits both a research memo and an audit trace. It is a research-engineering prototype—not investment advice, a trading system, or a substitute for licensed market data.

The repository has three cumulative research phases. **Phase 1** isolates harness architecture with a deterministic model. **Phase 2** crosses seeded stochastic model profiles with minimal, structured, and strong harnesses. **Phase 3** provides a frozen, budget-guarded protocol for validating those conclusions with configured real models; no real-model findings are claimed yet.

## Try the Research Workbench

Launch the analyst-facing local application without API credentials:

```bash
uv sync --all-groups
uv run streamlit run workbench/app.py
```

Choose a bundled synthetic issuer, edit the research question, approve the proposed plan, run the structured workflow, inspect evidence and deterministic calculations, review the thesis and critic, record a human decision, and download an auditable memo/session bundle. Local `.txt`, `.md`, and `.csv` research packages can be added as separately identified evidence. See the [product guide](docs/product_workbench.md).

## Why institutional credit research?

Institutional research is not just question answering. A professional workflow must distinguish source facts from calculations, inferences, and judgments; compare issuer fundamentals with market pricing; expose uncertainty and downside; preserve provenance; and support accountable review. That makes credit research a useful test of whether an agent harness improves the epistemic process, rather than merely the prose.

The project therefore scores architectures on task completion, directional accuracy against synthetic ground truth, risk recall, claim support, citation validity, unsupported claims, tool use, and workflow steps. More agents can score worse if they create unsupported or duplicate work.

## Three-phase research program

- **Phase 1 — Harness architecture and deterministic evaluation.** Workflow structure and adversarial critique mattered more than nominal role labels.
- **Phase 2 — Model capability vs harness capability in a stochastic simulator.** A 324-run factorial found that both axes matter; see the [Phase 2 report](docs/phase2_model_vs_harness.md).
- **Phase 3 — Real-model validation.** Frozen prompts, benchmark manifests, blind evaluation, caching, resume, raw-response preservation, and hard cost limits make controlled real-model studies possible. Its empirical status is **NOT YET RUN**; see the [Phase 3 protocol](docs/phase3_real_model_validation.md).

## Architecture

```text
Research question
      │
      ▼
Typed plan ──► deterministic router
      │
      ├── Credit analyst ─────────┐
      ├── Macro/rates analyst ────┤
      ├── Relative-value analyst ─┼──► shared evidence + research state
      └── Evidence researcher ────┘                  │
                                                    ▼
                                      Thesis synthesizer
                                                    │
                                      Critic / challenge agent
                                                    │
                                      Mechanical verifier
                                                    │
                                      Human approval gate
                                                    │
                                                    ▼
                                         Memo + audit trace
```

The core uses no orchestration framework. State transitions, tool contracts, evidence IDs, routing, challenges, verification, and audit events are ordinary typed Python code.

## Documentation

- [Project Overview](docs/project_overview.md)
- [Architecture](docs/architecture.md)
- [Research Question](docs/research_question.md)
- [Experiment Design](docs/experiment_design.md)
- [Results and Findings](docs/results_and_findings.md)
- [Evaluation Framework](docs/evaluation_framework.md)
- [Institutional Workflow](docs/institutional_workflow.md)
- [Auditability and Controls](docs/auditability_and_controls.md)
- [Limitations](docs/limitations.md)
- [Future Work](docs/future_work.md)
- [Phase 2: Model vs Harness](docs/phase2_model_vs_harness.md)
- [Phase 3: Real-Model Validation](docs/phase3_real_model_validation.md)
- [Product Workbench](docs/product_workbench.md)
- [Failure Taxonomy](docs/failure_taxonomy.md)

## Curriculum

| Tutorial | Concept | Implementation | Research lesson |
|---|---|---|---|
| 01 | Minimal agent loop | Policy, environment, transition, trace | An agent is more than one model call. |
| 02 | Structured research | Typed question, plan, tasks | Decomposition improves inspectability, not truth by itself. |
| 03 | Retrieval and evidence | Local lexical corpus with stable IDs | Retrieved text is not automatically supporting evidence. |
| 04 | Financial tools | Validated ratios, spreads, expected loss, scenario P&L | Deterministic arithmetic belongs in tools. |
| 05 | Routing | Rule and naive policies | Task ownership can be measured. |
| 06 | Shared state | Claims, evidence, calculations, audit | Research state is not chat history. |
| 07 | Specialists | Role-specific structured contributions | Specialization must improve measured work, not word count. |
| 08 | Critic | Explicit challenges and risk additions | Critique should attack assumptions, not polish prose. |
| 09 | Verification | Support and provenance checks | Unsupported claims must be mechanically visible. |
| 10 | Human oversight | Approve/revise/reject decision | Showing output is not meaningful oversight. |
| 11 | Evaluation harness | Repeated controlled configurations | Compare the whole process, including cost proxies. |
| 12 | Workbench | Integrated institutional workflow | The harness is part of the epistemic system. |
| 13–15 | Phase 2 foundations | Stochastic failures, model profiles, harness strength | “Weak” and “strong” must be operational definitions. |
| 16–19 | Controlled attribution | Factorial, critic, verifier, specialization | Benefits depend on model capability and information flow. |
| 20–22 | Dynamic controls | Longitudinal memory, freshness, failure attribution | State can help, anchor, or preserve stale evidence. |
| 23–26 | Phase 3 infrastructure | Real backend, prompts, cache, blind evaluation | Provider calls are experimental observations, not plumbing details. |
| 27–32 | Real-model protocol | Stability, premise resistance, counterfactuals, calibration, cost | Generalization requires repeated, bounded, preregistered tests. |

Run any lesson with, for example, `uv run python tutorials/04_financial_tools.py`.

## Synthetic universe

`generate_universe(seed)` creates ten issuers across telecom, utilities, retail, industrials, technology, energy, healthcare, consumer, and real estate. It contains ratings, debt, cash, EBITDA, margins, free cash flow, earnings trends, yields, spreads, CDS, duration, historical spread distributions, macro assumptions, issuer documents, and synthetic news. Fixed seeds make every default experiment reproducible. The values are invented and must never be treated as current market data.

## Experiments

- `run_single_vs_multi.py` holds cases and tools constant while changing task ownership.
- `run_workflow_ablation.py` compares free-form specialist research with an explicit institutional workflow while holding retrieval and tools constant.
- `run_critic_ablation.py` measures marginal risk recall and added steps.
- `run_evidence_ablation.py` compares otherwise identical workflows with and without an explicit verifier.
- `run_capstone.py` compares six variants across multiple seeds and issuers, then writes JSON, Markdown, and four plots.
- `run_phase2_capstone.py` runs the 3×3 model/harness matrix plus focused critic, verification, specialization, and memory studies.
- `run_real_model.py` is an optional OpenAI-compatible adapter smoke runner; it is never called by tests or default experiments.
- `run_phase3_capstone.py` plans smoke, pilot, or full frozen studies and requires an explicit `--execute` gate for live work. The critic, verification, specialization, longitudinal, premise, and counterfactual entry points default to offline dry runs.

The capstone variants are: A context-only baseline; B single agent with tools; C specialist workflow; D specialists plus critic; E specialists, critic, and verifier; F the full persistent-state configuration. No result is hard-coded or cherry-picked.

## Run the prototype

```bash
uv sync --all-groups
uv run python prototype/run_research.py NRT
uv run python prototype/run_research.py CRH --seed 23 --output results/crh_memo.json
```

The output separates the research conclusion from executable investment recommendations and includes evidence locators, invalidation conditions, approval status, metrics, and the event trace.

## Reproduce and validate

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run pyright

for tutorial in tutorials/*.py; do uv run python "$tutorial" >/dev/null; done
uv run python experiments/run_capstone.py
uv run python experiments/run_phase2_capstone.py
uv run python experiments/run_phase3_capstone.py --preset smoke --dry-run
```

Source-controlled capstone outputs live in `results/`. Runs record the seed, configuration, architecture, and dataset version. Timestamps are omitted from deterministic comparison artifacts.

## Package map

- `schemas.py`: research questions, tasks, evidence, claims, risks, challenges, memos, and events.
- `dataset.py`: deterministic synthetic issuer and document generator.
- `retrieval.py`: local evidence retrieval with stable provenance.
- `tools.py`: validated financial and portfolio-impact calculations.
- `state.py`: controlled state transitions and audit logging.
- `routing.py`: inspectable specialist routing.
- `verification.py`: mechanical evidence and claim checks.
- `workflow.py`: configurable end-to-end workbench.
- `evaluation.py`: architecture experiments, reports, and plots.
- `stochastic_model.py`, `harness.py`: operational Phase 2 model and harness profiles.
- `hard_episodes.py`, `longitudinal.py`: difficult and multi-episode research benchmarks.
- `phase2_runner.py`, `phase2_evaluation.py`: error attribution, factorial analysis, reports, and plots.
- `adapters.py`: optional provider-neutral OpenAI-compatible backend.
- `phase3_backend.py`, `phase3_cache.py`, `prompts/`: validated real calls, redacted raw records, resume, and versioned prompts.
- `phase3_benchmark.py`, `phase3_runtime.py`, `phase3_evaluator.py`: observable/hidden boundary and controlled operations.
- `phase3_config.py`, `phase3_metrics.py`, `phase3_analysis.py`: frozen configuration, resource limits, stability, calibration, and paired analysis.

## Limitations

The data, model profiles, error rates, and ground truth are synthetic and simplified. Phase 2 profiles are causal simulators, not calibrated representations of commercial LLMs. Phase 3 is infrastructure-ready but empirically pending: mocked adapters and dry runs are not real-model evidence. Spread and portfolio calculations remain pedagogical, verification is partly lexical/rule-based, and human approval is simulated. There is no licensed data, live pricing, execution, portfolio optimization, or investment-advice claim. See [limitations](docs/limitations.md).
