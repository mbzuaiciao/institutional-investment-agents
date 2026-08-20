# Financial tool use

Models should not silently calculate spreads, leverage, expected loss, or scenario P&L when a small deterministic function can do so. A tool contract validates inputs, returns units, records source arguments, and produces a stable result ID. This improves reproducibility and permits recalculation.

The included calculations are pedagogical: spread to benchmark, gross/net leverage, coverage, normal-distribution spread percentile, expected loss, and first-order duration P&L. They deliberately expose assumptions. They do not replace full cash-flow pricing, OAS models, default simulation, liquidity haircuts, or portfolio risk systems.

