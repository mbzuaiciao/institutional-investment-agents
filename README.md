# Institutional Investment Agents

An executable, from-first-principles research project for asking a deliberately uncomfortable question:

> What agent architecture actually improves institutional investment research rather than merely producing more elaborate-looking answers?

The concrete laboratory is synthetic five-year corporate credit research. The system gathers evidence, performs deterministic calculations, maintains claims and assumptions, challenges a thesis, verifies provenance, passes through an approval gate, and emits both a research memo and an audit trace. It is a research-engineering prototype—not investment advice, a trading system, or a substitute for licensed market data.

## Why institutional credit research?

Institutional research is not just question answering. A professional workflow must distinguish source facts from calculations, inferences, and judgments; compare issuer fundamentals with market pricing; expose uncertainty and downside; preserve provenance; and support accountable review. That makes credit research a useful test of whether an agent harness improves the epistemic process, rather than merely the prose.

The project therefore scores architectures on task completion, directional accuracy against synthetic ground truth, risk recall, claim support, citation validity, unsupported claims, tool use, and workflow steps. More agents can score worse if they create unsupported or duplicate work.

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

Run any lesson with, for example, `uv run python tutorials/04_financial_tools.py`.

## Synthetic universe

`generate_universe(seed)` creates ten issuers across telecom, utilities, retail, industrials, technology, energy, healthcare, consumer, and real estate. It contains ratings, debt, cash, EBITDA, margins, free cash flow, earnings trends, yields, spreads, CDS, duration, historical spread distributions, macro assumptions, issuer documents, and synthetic news. Fixed seeds make every default experiment reproducible. The values are invented and must never be treated as current market data.

## Experiments

- `run_single_vs_multi.py` holds cases and tools constant while changing task ownership.
- `run_workflow_ablation.py` compares a context-only/free-form baseline with explicit tasks.
- `run_critic_ablation.py` measures marginal risk recall and added steps.
- `run_evidence_ablation.py` compares otherwise identical workflows with and without an explicit verifier.
- `run_capstone.py` compares six variants across multiple seeds and issuers, then writes JSON, Markdown, and four plots.

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
for experiment in experiments/run_*.py; do uv run python "$experiment"; done
uv run python experiments/run_capstone.py
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

## Limitations

The data and ground truth are synthetic and simplified. Spread-to-benchmark is not a full option-adjusted-spread calculation; scenario P&L is a transparent duration approximation; default and recovery assumptions are pedagogical. The deterministic model policy does not reproduce the linguistic variability or failure modes of a production LLM. Lexical support checks are not semantic entailment, and the benchmark partially reflects choices made by its authors. Persistent state is intra-run in this prototype, not a production cross-case memory service. There is no licensed data, live pricing, order execution, portfolio optimization, or claim of investment advice. Human approval is represented structurally but simulated by policy for reproducible runs.

