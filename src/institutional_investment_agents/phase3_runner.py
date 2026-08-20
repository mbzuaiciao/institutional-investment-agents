"""Planning and guarded execution surface for Phase 3 experiments."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from institutional_investment_agents.phase3_backend import (
    Phase3OpenAICompatibleBackend,
    Phase3ProviderError,
)
from institutional_investment_agents.phase3_benchmark import load_observable_episodes
from institutional_investment_agents.phase3_cache import ResponseCache
from institutional_investment_agents.phase3_config import (
    build_plan,
    file_hash,
    format_plan,
    load_json_yaml,
    load_models,
    load_presets,
)
from institutional_investment_agents.phase3_longitudinal import observable_longitudinal_sequence
from institutional_investment_agents.phase3_runtime import prepare_calls
from institutional_investment_agents.phase3_schemas import (
    RealModelConfig,
    ResourceLimits,
    ResultStatus,
)
from institutional_investment_agents.phase3_studies import get_study
from institutional_investment_agents.prompts import prompt_registry_hash

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = REPOSITORY_ROOT / "configs" / "phase3_protocol.yaml"
DEFAULT_BENCHMARK = REPOSITORY_ROOT / "configs" / "phase3_benchmark.yaml"
DEFAULT_MODELS = REPOSITORY_ROOT / "configs" / "phase3_models.example.yaml"


def build_parser(study: str = "factorial") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Phase 3 {study} real-model protocol")
    parser.add_argument("--preset", choices=("smoke", "pilot", "full"), default="smoke")
    parser.add_argument("--models", nargs="+", default=("R0", "R1", "R2"))
    parser.add_argument("--model-config", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--max-total-tokens", type=int)
    parser.add_argument("--max-estimated-cost", type=float)
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "results/phase3")
    parser.add_argument("--cache-dir", type=Path, default=REPOSITORY_ROOT / ".phase3_cache")
    return parser


def plan_from_args(args: argparse.Namespace, *, study: str) -> tuple[Any, dict[str, Any]]:
    protocol = load_json_yaml(args.protocol)
    presets = load_presets(args.protocol)
    models = load_models(args.model_config, tuple(args.models))
    limit_values = dict(protocol["limits"])
    for key in ("max_model_calls", "max_total_tokens", "max_estimated_cost"):
        override = getattr(args, key)
        if override is not None:
            limit_values[key] = override
    limits = ResourceLimits.model_validate(limit_values)
    definition = get_study(study)
    harnesses = tuple(condition.base_harness for condition in definition.conditions)
    preset = presets[args.preset]
    if study == "longitudinal":
        preset = preset.model_copy(
            update={"families": tuple(f"longitudinal_update_{index}" for index in range(1, 6))}
        )
    plan = build_plan(
        preset=preset,
        study=study,
        models=models,
        harnesses=harnesses,
        limits=limits,
        conditions=tuple(condition.name for condition in definition.conditions),
        calls_per_condition=tuple(len(condition.operations) for condition in definition.conditions),
    )
    metadata = {
        "result_status": ResultStatus.NOT_YET_RUN.value,
        "benchmark_hash": file_hash(args.benchmark),
        "protocol_hash": file_hash(args.protocol),
        "models": [model.model_dump(mode="json") for model in models],
        "limits": limits.model_dump(mode="json"),
    }
    return plan, metadata


def run_cli(study: str = "factorial", argv: list[str] | None = None) -> int:
    parser = build_parser(study)
    args = parser.parse_args(argv)
    if args.dry_run and args.execute:
        parser.error("--dry-run and --execute are mutually exclusive")
    if not args.dry_run and not args.execute:
        parser.error("choose --dry-run or --execute explicitly")
    plan, metadata = plan_from_args(args, study=study)
    print(format_plan(plan))
    print(f"Benchmark SHA-256: {metadata['benchmark_hash']}")
    episodes = (
        observable_longitudinal_sequence()
        if study == "longitudinal"
        else load_observable_episodes(args.benchmark)
    )
    selected = [episode for episode in episodes if episode.family in plan.families]
    if len({episode.family for episode in selected}) != len(plan.families):
        raise ValueError("preset references a family absent from the frozen benchmark")
    if args.dry_run:
        print("Result status: NOT YET RUN")
        print("Dry run complete; no provider request was sent and no cache was read.")
        return 0
    if os.getenv("PHASE3_ENABLE_LIVE_RUNS") != "YES":
        raise RuntimeError("live execution requires PHASE3_ENABLE_LIVE_RUNS=YES")
    models = load_models(args.model_config, tuple(args.models))
    limits = ResourceLimits.model_validate(metadata["limits"])
    if any(model.retries > limits.max_retries for model in models):
        raise ValueError("model retry setting exceeds protocol max_retries")
    if any(model.model.startswith("configure-") for model in models):
        raise ValueError("replace placeholder model names before live execution")
    execute_live_protocol(
        plan=plan,
        metadata=metadata,
        models=models,
        episodes=tuple(selected),
        limits=limits,
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        study=plan.study,
    )
    return 0


def write_dry_run_manifest(path: Path, *, plan: Any, metadata: dict[str, Any]) -> None:
    value = {**metadata, "plan": plan.model_dump(mode="json")}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def execute_live_protocol(
    *,
    plan: Any,
    metadata: dict[str, Any],
    models: tuple[RealModelConfig, ...],
    episodes: tuple[Any, ...],
    limits: ResourceLimits,
    output_dir: Path,
    cache_dir: Path,
    study: str,
) -> None:
    """Execute only after CLI planning, hard-limit checks, and the live environment gate."""
    records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    new_calls = 0
    total_tokens = 0
    actual_cost: float | None = 0.0 if all(model.pricing for model in models) else None
    definition = get_study(study)
    for model in models:
        backend = Phase3OpenAICompatibleBackend(model, cache=ResponseCache(cache_dir))
        for condition in definition.conditions:
            harness = condition.base_harness
            state_by_repetition: dict[int, tuple[str, ...]] = {}
            for episode in episodes:
                for repetition in range(plan.repetitions):
                    last_output: str | None = None
                    for prepared in prepare_calls(
                        model=model,
                        harness=harness,
                        episode=episode,
                        repetition=repetition,
                        condition=condition.name,
                        operations=condition.operations,
                        context_mode=condition.context_mode,
                        state_context=(
                            state_by_repetition.get(repetition, ())
                            if condition.persistent_state
                            else ()
                        ),
                    ):
                        try:
                            result = backend.execute(prepared.spec, prepared.request)
                        except Phase3ProviderError as error:
                            failures.append(
                                {
                                    "episode_id": episode.episode_id,
                                    "model_id": model.identifier,
                                    "harness": harness.value,
                                    "operation": prepared.spec.operation.value,
                                    "error_kind": error.kind.value,
                                    "attempts": error.attempts,
                                    "message": str(error),
                                }
                            )
                            continue
                        records.append(result.record.model_dump(mode="json"))
                        if result.record.parsed_response is not None:
                            last_output = str(result.record.parsed_response["output"])
                        new_calls += result.new_api_calls
                        total_tokens += int(result.record.usage_metadata.get("total_tokens", 0))
                        if actual_cost is not None and result.new_api_calls:
                            assert model.pricing is not None
                            actual_cost += (
                                float(result.record.usage_metadata.get("prompt_tokens", 0))
                                * model.pricing.input_per_million
                                + float(result.record.usage_metadata.get("completion_tokens", 0))
                                * model.pricing.output_per_million
                            ) / 1_000_000
                        if new_calls > limits.max_model_calls:
                            raise RuntimeError("actual model calls exceeded max_model_calls")
                        if total_tokens > limits.max_total_tokens:
                            raise RuntimeError("actual token usage exceeded max_total_tokens")
                    if condition.persistent_state and last_output is not None:
                        prior = state_by_repetition.get(repetition, ())
                        state_by_repetition[repetition] = (*prior[-3:], f"Prior thesis: {last_output}")
    status = (
        ResultStatus.CONFIRMATORY_REAL_MODEL
        if plan.preset == "full"
        else ResultStatus.PILOT_REAL_MODEL
    )
    _write_live_outputs(
        output_dir=output_dir,
        plan=plan,
        metadata=metadata,
        status=status,
        records=records,
        failures=failures,
        new_calls=new_calls,
        total_tokens=total_tokens,
        actual_cost=actual_cost,
    )


def _write_live_outputs(
    *,
    output_dir: Path,
    plan: Any,
    metadata: dict[str, Any],
    status: ResultStatus,
    records: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    new_calls: int,
    total_tokens: int,
    actual_cost: float | None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        **metadata,
        "result_status": status.value,
        "run_date": datetime.now(UTC).isoformat(),
        "prompt_registry_hash": prompt_registry_hash(),
        "code_commit": _code_commit(),
        "plan": plan.model_dump(mode="json"),
        "real_model_calls": new_calls,
        "total_tokens": total_tokens,
        "actual_monetary_cost": actual_cost,
        "completed_records": len(records),
        "provider_failures": len(failures),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    (output_dir / "runs.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    )
    (output_dir / "failures.json").write_text(
        json.dumps(
            {"result_status": status.value, "observed_failures": failures},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    with (output_dir / "summary.csv").open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ("result_status", "real_model_calls", "completed_records", "provider_failures")
        )
        writer.writerow((status.value, new_calls, len(records), len(failures)))
    (output_dir / "report.md").write_text(
        f"# Phase 3 results\n\n**Result status: {status.value}**\n\n"
        f"Completed call records: {len(records)}. Provider failures: {len(failures)}.\n\n"
        "Research-quality conclusions require the separate blind evaluator and are not inferred "
        "from call completion alone.\n"
    )
    figures = output_dir / "figures"
    figures.mkdir(exist_ok=True)
    (figures / "README.md").write_text(
        "# Phase 3 figures\n\nNo figure is generated until blind evaluation completes.\n"
    )


def _code_commit() -> str:
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unavailable"
