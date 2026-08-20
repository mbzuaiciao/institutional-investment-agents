# Synthetic data

The default universe is generated in memory by `institutional_investment_agents.dataset.generate_universe`. Every number, filing excerpt, pricing observation, news item, and macro assumption is synthetic. Fixed seeds change small market perturbations while preserving coherent identities and accounting relationships. Tests and experiments require no network or proprietary data.

To export an inspectable snapshot, call `export_universe(Path("data/synthetic/universe.json"), seed=17)`. Generated ad-hoc snapshots are not required for execution; the generator is the source of truth.

