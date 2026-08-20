"""Factorial attribution, focused ablations, reports, and plots for Phase 2."""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev
from typing import Any

from institutional_investment_agents.hard_episodes import (
    generate_hard_episode,
    generate_hard_suite,
)
from institutional_investment_agents.harness import HARNESS_PROFILES
from institutional_investment_agents.longitudinal import run_longitudinal_research
from institutional_investment_agents.phase2_runner import run_phase2_episode
from institutional_investment_agents.phase2_schemas import HardEpisodeFamily
from institutional_investment_agents.stochastic_model import (
    MODEL_PROFILES,
    StochasticSyntheticModel,
)

DEFAULT_PHASE2_SEEDS = (11, 23, 37, 53)
PRIMARY_METRICS = (
    "research_quality_score",
    "risk_factor_recall",
    "claim_support_rate",
    "citation_validity",
    "contradiction_detection",
    "calculation_accuracy",
    "stale_evidence_usage_rate",
    "control_quality_score",
)


def run_factorial(
    *,
    seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS,
    model_names: tuple[str, ...] = ("weak", "medium", "strong"),
    harness_names: tuple[str, ...] = ("weak", "structured", "strong"),
    families: tuple[HardEpisodeFamily, ...] = tuple(HardEpisodeFamily),
) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for seed in seeds:
        episodes = {family: generate_hard_episode(family, seed=seed) for family in families}
        for model_name in model_names:
            for harness_name in harness_names:
                for family, episode in episodes.items():
                    model_seed = _stable_seed(seed, model_name, harness_name, family.value)
                    model = StochasticSyntheticModel(model_name, seed=model_seed)
                    run = run_phase2_episode(
                        model,
                        HARNESS_PROFILES[harness_name],
                        episode,
                        seed=seed,
                    )
                    runs.append(run.model_dump(mode="json"))
    cell_summary = _summarize_factorial_cells(runs)
    attribution = {
        metric: factorial_attribution(runs, metric)
        for metric in (
            "research_quality_score",
            "risk_factor_recall",
            "claim_support_rate",
            "citation_validity",
            "control_quality_score",
        )
    }
    return {
        "seeds": list(seeds),
        "models": list(model_names),
        "harnesses": list(harness_names),
        "families": [family.value for family in families],
        "run_count": len(runs),
        "runs": runs,
        "cell_summary": cell_summary,
        "attribution": attribution,
    }


def factorial_attribution(runs: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    """Balanced two-factor ANOVA-style sum-of-squares decomposition."""
    values = [_metric_value(run, metric) for run in runs]
    grand = mean(values)
    by_model: dict[str, list[float]] = defaultdict(list)
    by_harness: dict[str, list[float]] = defaultdict(list)
    by_cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for run, value in zip(runs, values, strict=True):
        model_name = str(run["model_profile"])
        harness_name = str(run["harness_profile"])
        by_model[model_name].append(value)
        by_harness[harness_name].append(value)
        by_cell[(model_name, harness_name)].append(value)
    model_means = {key: mean(items) for key, items in by_model.items()}
    harness_means = {key: mean(items) for key, items in by_harness.items()}
    cell_means = {key: mean(items) for key, items in by_cell.items()}
    models = len(model_means)
    harnesses = len(harness_means)
    n_cell = len(next(iter(by_cell.values())))
    ss_model = harnesses * n_cell * sum((value - grand) ** 2 for value in model_means.values())
    ss_harness = models * n_cell * sum((value - grand) ** 2 for value in harness_means.values())
    interactions = {
        f"{model}|{harness}": cell_mean - model_means[model] - harness_means[harness] + grand
        for (model, harness), cell_mean in cell_means.items()
    }
    ss_interaction = n_cell * sum(value**2 for value in interactions.values())
    ss_residual = sum(
        (value - cell_means[(str(run["model_profile"]), str(run["harness_profile"]))]) ** 2
        for run, value in zip(runs, values, strict=True)
    )
    ss_total = sum((value - grand) ** 2 for value in values)
    denominator = ss_total or 1.0
    return {
        "grand_mean": round(grand, 4),
        "model_means": {key: round(value, 4) for key, value in model_means.items()},
        "harness_means": {key: round(value, 4) for key, value in harness_means.items()},
        "interaction_deviation": {key: round(value, 4) for key, value in interactions.items()},
        "sum_squares": {
            "model": round(ss_model, 4),
            "harness": round(ss_harness, 4),
            "interaction": round(ss_interaction, 4),
            "residual": round(ss_residual, 4),
            "total": round(ss_total, 4),
        },
        "variance_share": {
            "model": round(ss_model / denominator, 4),
            "harness": round(ss_harness / denominator, 4),
            "interaction": round(ss_interaction / denominator, 4),
            "residual": round(ss_residual / denominator, 4),
        },
        "note": "Descriptive balanced decomposition; no significance claim is made.",
    }


def run_critic_study(*, seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    families = (
        HardEpisodeFamily.CONTRADICTORY_EVIDENCE,
        HardEpisodeFamily.MISLEADING_CHEAPNESS,
        HardEpisodeFamily.FALSE_CORRELATION,
        HardEpisodeFamily.MULTI_HOP_EVIDENCE,
    )
    base = HARNESS_PROFILES["structured"]
    for seed in seeds:
        for model_name in MODEL_PROFILES:
            for enabled in (False, True):
                harness = base.model_copy(
                    update={
                        "critic": enabled,
                        "contradiction_handling": enabled,
                    }
                )
                for family in families:
                    episode = generate_hard_episode(family, seed=seed)
                    model = StochasticSyntheticModel(
                        model_name,
                        seed=_stable_seed(seed, model_name, "critic", family.value),
                    )
                    run = run_phase2_episode(model, harness, episode, seed=seed)
                    runs.append(
                        {
                            "model_profile": model_name,
                            "critic_enabled": enabled,
                            "family": family.value,
                            "seed": seed,
                            "metrics": run.metrics.model_dump(mode="json"),
                            "cost": run.cost.model_dump(mode="json"),
                        }
                    )
    return {
        "run_count": len(runs),
        "runs": runs,
        "summary": _condition_summary(runs, "critic_enabled"),
    }


def run_verification_study(*, seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    base = HARNESS_PROFILES["structured"]
    for seed in seeds:
        for model_name in MODEL_PROFILES:
            for enabled in (False, True):
                harness = base.model_copy(
                    update={
                        "verifier": enabled,
                        "revision_loop": enabled,
                        "approval_gate": enabled,
                    }
                )
                for episode in generate_hard_suite(seed):
                    model = StochasticSyntheticModel(
                        model_name,
                        seed=_stable_seed(
                            seed,
                            model_name,
                            "verifier",
                            episode.family.value,
                        ),
                    )
                    run = run_phase2_episode(model, harness, episode, seed=seed)
                    runs.append(
                        {
                            "model_profile": model_name,
                            "verification_enabled": enabled,
                            "family": episode.family.value,
                            "seed": seed,
                            "metrics": run.metrics.model_dump(mode="json"),
                            "cost": run.cost.model_dump(mode="json"),
                        }
                    )
    return {
        "run_count": len(runs),
        "runs": runs,
        "summary": _condition_summary(runs, "verification_enabled"),
    }


def run_specialization_study(*, seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    families = (
        HardEpisodeFamily.CONTRADICTORY_EVIDENCE,
        HardEpisodeFamily.MISLEADING_CHEAPNESS,
        HardEpisodeFamily.SCENARIO_SENSITIVITY,
        HardEpisodeFamily.MULTI_HOP_EVIDENCE,
    )
    base = HARNESS_PROFILES["structured"]
    for seed in seeds:
        for model_name in MODEL_PROFILES:
            for enabled in (False, True):
                harness = base.model_copy(update={"specialist_partitioning": enabled})
                for family in families:
                    episode = generate_hard_episode(family, seed=seed)
                    model = StochasticSyntheticModel(
                        model_name,
                        seed=_stable_seed(
                            seed,
                            model_name,
                            "specialists",
                            family.value,
                        ),
                    )
                    run = run_phase2_episode(model, harness, episode, seed=seed)
                    runs.append(
                        {
                            "model_profile": model_name,
                            "specialists_enabled": enabled,
                            "family": family.value,
                            "seed": seed,
                            "metrics": run.metrics.model_dump(mode="json"),
                            "cost": run.cost.model_dump(mode="json"),
                        }
                    )
    return {
        "run_count": len(runs),
        "runs": runs,
        "summary": _condition_summary(runs, "specialists_enabled"),
        "control": "Operations and model-call budget are identical; only context partitioning changes.",
    }


def run_memory_study(*, seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS) -> dict[str, Any]:
    runs: list[dict[str, Any]] = []
    for seed in seeds:
        for model_name in MODEL_PROFILES:
            for persistent in (False, True):
                run = run_longitudinal_research(model_name, persistent=persistent, seed=seed)
                runs.append(run.model_dump(mode="json"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[f"{run['model_profile']}|{run['persistent']}"].append(run)
    summary: dict[str, dict[str, float | str | bool]] = {}
    for key, items in grouped.items():
        metrics = items[0]["metrics"].keys()
        summary[key] = {
            "model_profile": str(items[0]["model_profile"]),
            "persistent": bool(items[0]["persistent"]),
            **{
                metric: round(mean(float(item["metrics"][metric]) for item in items), 4)
                for metric in metrics
                if metric != "quality_by_episode"
            },
        }
        count = len(items[0]["metrics"]["quality_by_episode"])
        for index in range(count):
            summary[key][f"episode_{index + 1}_quality"] = round(
                mean(float(item["metrics"]["quality_by_episode"][index]) for item in items), 4
            )
    return {"run_count": len(runs), "runs": runs, "summary": summary}


def run_phase2_capstone(*, seeds: tuple[int, ...] = DEFAULT_PHASE2_SEEDS) -> dict[str, Any]:
    factorial = run_factorial(seeds=seeds)
    critic = run_critic_study(seeds=seeds)
    verification = run_verification_study(seeds=seeds)
    specialization = run_specialization_study(seeds=seeds)
    memory = run_memory_study(seeds=seeds)
    return {
        "schema_version": 2,
        "phase": "model_vs_harness",
        "seeds": list(seeds),
        "primary_run_count": factorial["run_count"],
        "total_run_count": factorial["run_count"]
        + critic["run_count"]
        + verification["run_count"]
        + specialization["run_count"]
        + memory["run_count"],
        "factorial": factorial,
        "critic_study": critic,
        "verification_study": verification,
        "specialization_study": specialization,
        "memory_study": memory,
    }


def write_phase2_json(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def write_phase2_csv(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = result["factorial"]["cell_summary"]
    fieldnames = list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_phase2_markdown(result: dict[str, Any], path: Path) -> None:
    factorial = result["factorial"]
    rows = factorial["cell_summary"]
    attribution = factorial["attribution"]["research_quality_score"]
    lines = [
        "# Phase 2 model × harness capstone",
        "",
        f"Primary factorial runs: **{result['primary_run_count']}**. Total including focused studies: **{result['total_run_count']}**.",
        "",
        "| Model | Harness | Quality mean | SD | 95% CI | Risk recall | Support | Cost units |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['model_profile']} | {row['harness_profile']} | {row['research_quality_score_mean']:.2f} | {row['research_quality_score_sd']:.2f} | ±{row['research_quality_score_ci95']:.2f} | {row['risk_factor_recall_mean']:.2%} | {row['claim_support_rate_mean']:.2%} | {row['simulated_cost_units_mean']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Descriptive attribution",
            "",
            f"Model variance share: **{attribution['variance_share']['model']:.1%}**; harness: **{attribution['variance_share']['harness']:.1%}**; interaction: **{attribution['variance_share']['interaction']:.1%}**; residual: **{attribution['variance_share']['residual']:.1%}**.",
            "",
            "These are descriptive balanced sum-of-squares shares, not claims of statistical significance or real-LLM generalization.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_phase2_plots(result: dict[str, Any], figures_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    rows = result["factorial"]["cell_summary"]
    model_names = ["weak", "medium", "strong"]
    harness_labels = ["H0_minimal", "H1_structured", "H2_strong"]
    matrix = [
        [
            _cell(rows, model_name, harness_name)["research_quality_score_mean"]
            for harness_name in harness_labels
        ]
        for model_name in model_names
    ]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    image = ax.imshow(matrix, cmap="Blues", vmin=50, vmax=100)
    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            ax.text(column_index, row_index, f"{value:.1f}", ha="center", va="center")
    ax.set_xticks(range(3), ("H0 weak", "H1 structured", "H2 strong"))
    ax.set_yticks(range(3), model_names)
    ax.set_xlabel("harness profile")
    ax.set_ylabel("model profile")
    ax.set_title("Phase 2 research quality: model × harness")
    fig.colorbar(image, ax=ax, label="quality score")
    outputs.append(_save(fig, figures_dir / "phase2_model_harness_heatmap.png"))

    benefits = []
    for model_name in model_names:
        weak = _cell(rows, model_name, "H0_minimal")["research_quality_score_mean"]
        strong = _cell(rows, model_name, "H2_strong")["research_quality_score_mean"]
        benefits.append(strong - weak)
    outputs.append(
        _bar_plot(
            model_names,
            benefits,
            "Strong-harness benefit by model profile",
            "H2 - H0 quality points",
            figures_dir / "phase2_harness_benefit.png",
        )
    )
    critic_summary = result["critic_study"]["summary"]
    critic_benefit = [
        critic_summary[f"{name}|True"]["risk_factor_recall_mean"]
        - critic_summary[f"{name}|False"]["risk_factor_recall_mean"]
        for name in model_names
    ]
    outputs.append(
        _bar_plot(
            model_names,
            critic_benefit,
            "Critic benefit by model profile",
            "risk-recall change",
            figures_dir / "phase2_critic_benefit.png",
        )
    )
    verifier_summary = result["verification_study"]["summary"]
    labels = [f"{name}\noff" for name in model_names] + [f"{name}\non" for name in model_names]
    unsupported = [
        verifier_summary[f"{name}|False"]["unsupported_claims_mean"] for name in model_names
    ] + [verifier_summary[f"{name}|True"]["unsupported_claims_mean"] for name in model_names]
    outputs.append(
        _bar_plot(
            labels,
            unsupported,
            "Unsupported claims under verification",
            "mean unsupported claims",
            figures_dir / "phase2_verification_errors.png",
        )
    )
    risk_values = [row["risk_factor_recall_mean"] for row in rows]
    risk_labels = [
        f"{row['model_profile'][0].upper()}-{row['harness_profile'][:2]}" for row in rows
    ]
    outputs.append(
        _bar_plot(
            risk_labels,
            risk_values,
            "Risk recall by model and harness",
            "risk recall",
            figures_dir / "phase2_risk_recall.png",
        )
    )
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for row in rows:
        ax.scatter(
            row["simulated_cost_units_mean"],
            row["research_quality_score_mean"],
            s=65,
            label=f"{row['model_profile']}/{row['harness_profile']}",
        )
    ax.set_title("Quality versus abstract workflow cost")
    ax.set_xlabel("simulated cost units")
    ax.set_ylabel("quality score")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    outputs.append(_save(fig, figures_dir / "phase2_quality_vs_cost.png"))

    memory_summary = result["memory_study"]["summary"]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for model_name in model_names:
        for persistent in (False, True):
            row = memory_summary[f"{model_name}|{persistent}"]
            values = [row[f"episode_{index}_quality"] for index in range(1, 6)]
            ax.plot(
                range(1, 6),
                values,
                marker="o",
                label=f"{model_name} / {'persistent' if persistent else 'stateless'}",
            )
    ax.set_title("Longitudinal quality across research updates")
    ax.set_xlabel("episode")
    ax.set_ylabel("quality score")
    ax.set_xticks(range(1, 6))
    ax.grid(alpha=0.25)
    ax.legend(fontsize=7, ncol=2)
    outputs.append(_save(fig, figures_dir / "phase2_persistent_state.png"))
    return outputs


def _summarize_factorial_cells(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[(str(run["model_profile"]), str(run["harness_profile"]))].append(run)
    rows: list[dict[str, Any]] = []
    model_order = {"weak": 0, "medium": 1, "strong": 2}
    harness_order = {"H0_minimal": 0, "H1_structured": 1, "H2_strong": 2}
    for (model_name, harness_name), items in sorted(
        grouped.items(), key=lambda pair: (model_order[pair[0][0]], harness_order[pair[0][1]])
    ):
        row: dict[str, Any] = {
            "model_profile": model_name,
            "harness_profile": harness_name,
            "n": len(items),
        }
        for metric in PRIMARY_METRICS:
            values = [_metric_value(item, metric) for item in items]
            deviation = stdev(values) if len(values) > 1 else 0.0
            row[f"{metric}_mean"] = round(mean(values), 4)
            row[f"{metric}_sd"] = round(deviation, 4)
            row[f"{metric}_ci95"] = round(1.96 * deviation / math.sqrt(len(values)), 4)
        for cost_metric in ("model_calls", "tool_calls", "workflow_steps", "simulated_cost_units"):
            row[f"{cost_metric}_mean"] = round(
                mean(float(item["cost"][cost_metric]) for item in items), 4
            )
        rows.append(row)
    return rows


def _condition_summary(
    runs: list[dict[str, Any]], condition_name: str
) -> dict[str, dict[str, Any]]:
    grouped: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[(str(run["model_profile"]), bool(run[condition_name]))].append(run)
    summary: dict[str, dict[str, Any]] = {}
    metrics = (
        "research_quality_score",
        "risk_factor_recall",
        "contradiction_detection",
        "claim_support_rate",
        "citation_validity",
        "unsupported_claims",
        "invalid_citations",
        "revisions",
        "correct_revisions",
        "unnecessary_revisions",
        "false_challenges",
        "control_quality_score",
    )
    for (model_name, condition), items in grouped.items():
        summary[f"{model_name}|{condition}"] = {
            "model_profile": model_name,
            condition_name: condition,
            **{
                f"{metric}_mean": round(mean(float(item["metrics"][metric]) for item in items), 4)
                for metric in metrics
            },
            "model_calls_mean": round(
                mean(float(item["cost"]["model_calls"]) for item in items), 4
            ),
            "workflow_steps_mean": round(
                mean(float(item["cost"]["workflow_steps"]) for item in items), 4
            ),
            "simulated_cost_units_mean": round(
                mean(float(item["cost"]["simulated_cost_units"]) for item in items), 4
            ),
        }
    return summary


def _metric_value(run: dict[str, Any], metric: str) -> float:
    return float(run["metrics"][metric])


def _stable_seed(seed: int, *parts: str) -> int:
    value = seed * 1_000_003
    for part in parts:
        for character in part:
            value = (value * 33 + ord(character)) % 2_147_483_647
    return value


def _cell(rows: list[dict[str, Any]], model_name: str, harness_name: str) -> dict[str, Any]:
    return next(
        row
        for row in rows
        if row["model_profile"] == model_name and row["harness_profile"] == harness_name
    )


def _save(fig: Any, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    import matplotlib.pyplot as plt

    plt.close(fig)
    return path


def _bar_plot(
    labels: list[str],
    values: list[float],
    title: str,
    ylabel: str,
    path: Path,
) -> Path:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    ax.bar(labels, values, color="#315b7d")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, path)
