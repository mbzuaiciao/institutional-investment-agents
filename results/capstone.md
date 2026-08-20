# Capstone architecture comparison

All values are means across the recorded synthetic cases.

| Variant | Quality | Support | Risk recall | Unsupported | Tool calls | Steps |
|---|---|---|---|---|---|---|
| A. Observation/context-only baseline | 61.46 | 0.00% | 45.83% | 1.00 | 0.00 | 15.00 |
| B. Single research agent with tools | 86.46 | 100.00% | 45.83% | 0.00 | 3.00 | 24.00 |
| C. Structured specialist workflow | 91.67 | 100.00% | 66.67% | 0.00 | 3.00 | 27.00 |
| D. Specialists plus critic | 98.44 | 100.00% | 93.75% | 0.00 | 3.00 | 28.00 |
| E. Specialists, critic and verifier | 98.44 | 100.00% | 93.75% | 0.00 | 3.00 | 29.00 |
| F. Full workflow with persistent state | 98.44 | 100.00% | 93.75% | 0.00 | 3.00 | 29.00 |

## Interpretation

The controlled synthetic benchmark rewards correct direction, risk recall, claim support, and workflow completion. More orchestration also consumes more steps, so a more elaborate harness is not automatically better. The verifier exposes unsupported claims; it does not retroactively make them true. Variant F is intentionally close to E in this deterministic prototype because explicit state is already used internally—the distinction is preserved for future cross-run memory experiments.
