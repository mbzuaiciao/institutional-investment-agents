"""Tutorial 26: runtime episodes exclude hidden evaluator labels."""

from pathlib import Path

from institutional_investment_agents.phase3_benchmark import load_observable_episodes

root = Path(__file__).resolve().parents[1]
episode = load_observable_episodes(root / "configs/phase3_benchmark.yaml")[0]
print(sorted(episode.model_dump()), "ground_truth" in episode.model_dump())
