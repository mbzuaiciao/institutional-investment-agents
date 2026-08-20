"""Controlled architecture comparisons and machine-readable research metrics."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from institutional_investment_agents.workflow import ResearchWorkbench, WorkflowConfig


@dataclass(frozen=True)
class ArchitectureVariant:
    key: str
    label: str
    overrides: dict[str, Any]


CAPSTONE_VARIANTS = (
    ArchitectureVariant(
        "A",
        "Observation/context-only baseline",
        {
            "architecture": "context_only",
            "specialists_enabled": False,
            "critic_enabled": False,
            "verification_enabled": False,
            "persistent_state": False,
            "structured_outputs": False,
            "tool_access": False,
            "explicit_workflow": False,
        },
    ),
    ArchitectureVariant(
        "B",
        "Single research agent with tools",
        {
            "architecture": "single_tools",
            "specialists_enabled": False,
            "critic_enabled": False,
            "verification_enabled": False,
            "structured_outputs": True,
            "tool_access": True,
            "explicit_workflow": False,
        },
    ),
    ArchitectureVariant(
        "C",
        "Structured specialist workflow",
        {
            "architecture": "specialists",
            "specialists_enabled": True,
            "critic_enabled": False,
            "verification_enabled": False,
            "structured_outputs": True,
            "tool_access": True,
            "explicit_workflow": True,
        },
    ),
    ArchitectureVariant(
        "D",
        "Specialists plus critic",
        {
            "architecture": "specialists_critic",
            "specialists_enabled": True,
            "critic_enabled": True,
            "verification_enabled": False,
            "structured_outputs": True,
            "tool_access": True,
            "explicit_workflow": True,
        },
    ),
    ArchitectureVariant(
        "E",
        "Specialists, critic and verifier",
        {
            "architecture": "full_verified",
            "specialists_enabled": True,
            "critic_enabled": True,
            "verification_enabled": True,
            "structured_outputs": True,
            "tool_access": True,
            "explicit_workflow": True,
        },
    ),
    ArchitectureVariant(
        "F",
        "Full workflow with persistent state",
        {
            "architecture": "full_persistent",
            "specialists_enabled": True,
            "critic_enabled": True,
            "verification_enabled": True,
            "persistent_state": True,
            "structured_outputs": True,
            "tool_access": True,
            "explicit_workflow": True,
        },
    ),
)


def run_evaluation(
    variants: tuple[ArchitectureVariant, ...] = CAPSTONE_VARIANTS,
    *,
    seeds: tuple[int, ...] = (17, 23, 41),
    issuer_ids: tuple[str, ...] = ("NRT", "CRH", "BAY", "VTX"),
) -> dict[str, Any]:
    runs: list[dict[str, object]] = []
    for variant in variants:
        for seed in seeds:
            config = WorkflowConfig(seed=seed, **variant.overrides)
            workbench = ResearchWorkbench(config)
            for issuer_id in issuer_ids:
                result = workbench.run(issuer_id)
                runs.append(
                    {
                        "variant": variant.key,
                        "label": variant.label,
                        "seed": seed,
                        "issuer_id": issuer_id,
                        "dataset_version": workbench.universe.version,
                        "metrics": result.metrics,
                    }
                )
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    labels = {variant.key: variant.label for variant in variants}
    for run in runs:
        metrics = run["metrics"]
        assert isinstance(metrics, dict)
        for metric, value in metrics.items():
            grouped[str(run["variant"])][metric].append(float(value))
    summary = {
        key: {
            "label": labels[key],
            **{metric: round(mean(values), 4) for metric, values in metrics.items()},
        }
        for key, metrics in grouped.items()
    }
    return {
        "schema_version": 1,
        "seeds": list(seeds),
        "issuer_ids": list(issuer_ids),
        "variants": [variant.__dict__ for variant in variants],
        "runs": runs,
        "summary": summary,
    }


def write_json(result: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


def write_markdown(result: dict[str, Any], path: Path) -> None:
    summary = result["summary"]
    assert isinstance(summary, dict)
    headers = ["Variant", "Quality", "Support", "Risk recall", "Unsupported", "Tool calls", "Steps"]
    lines = [
        "# Capstone architecture comparison",
        "",
        "All values are means across the recorded synthetic cases.",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for key in sorted(summary):
        row = summary[key]
        assert isinstance(row, dict)
        lines.append(
            f"| {key}. {row['label']} | {row['research_quality_score']:.2f} | {row['claim_support_rate']:.2%} | {row['risk_factor_recall']:.2%} | {row['unsupported_claims']:.2f} | {row['tool_calls']:.2f} | {row['steps']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The controlled synthetic benchmark rewards correct direction, risk recall, claim support, and workflow completion. More orchestration also consumes more steps, so a more elaborate harness is not automatically better. The verifier exposes unsupported claims; it does not retroactively make them true. Variant F is intentionally close to E in this deterministic prototype because explicit state is already used internally—the distinction is preserved for future cross-run memory experiments.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_plots(result: dict[str, Any], figures_dir: Path) -> list[Path]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = result["summary"]
    assert isinstance(summary, dict)
    keys = sorted(summary)
    figures_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for metric, title, ylabel in (
        ("research_quality_score", "Research quality by architecture", "score (0–100)"),
        ("claim_support_rate", "Claim support by architecture", "supported claims"),
        ("risk_factor_recall", "Risk-factor recall by architecture", "recall"),
        ("tool_calls", "Tool use by architecture", "mean calls per run"),
    ):
        values = [float(summary[key][metric]) for key in keys]
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ax.bar(keys, values, color="#315b7d")
        ax.set_title(title)
        ax.set_xlabel("architecture variant")
        ax.set_ylabel(ylabel)
        if metric in {"claim_support_rate", "risk_factor_recall"}:
            ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        output = figures_dir / f"{metric}.png"
        fig.savefig(output, dpi=150)
        plt.close(fig)
        outputs.append(output)
    return outputs
