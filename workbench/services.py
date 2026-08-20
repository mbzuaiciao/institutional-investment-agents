"""Thin, testable facade from the analyst UI to the existing research engine."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from institutional_investment_agents.dataset import IssuerRecord, generate_universe
from institutional_investment_agents.schemas import (
    AgentRole,
    AuditEvent,
    EvidenceItem,
    ResearchQuestion,
)
from institutional_investment_agents.workflow import (
    ResearchWorkbench,
    WorkflowConfig,
)
from workbench.session import ReviewStatus, WorkbenchSession

QUESTION_EXAMPLES = (
    "Is this issuer cheap relative to peers?",
    "What is the primary refinancing risk?",
    "What would cause the credit thesis to fail?",
    "How sensitive is the position to rates and spread widening?",
    "Reassess the thesis under a recession scenario.",
)

CHALLENGE_STATUSES = ("accepted", "resolved", "unresolved", "dismissed")
SUPPORTED_UPLOADS = {".txt", ".md", ".csv"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class BackendAvailability:
    identifier: str
    label: str
    available: bool
    reason: str


@dataclass(frozen=True)
class ExportBundle:
    memo_markdown: bytes
    research_session_json: bytes
    audit_trace_json: bytes
    evidence_csv: bytes
    claims_csv: bytes


def backend_availability() -> tuple[BackendAvailability, ...]:
    live_configured = all(
        (
            os.getenv("PHASE3_ENABLE_LIVE_RUNS") == "YES",
            bool(os.getenv("OPENAI_COMPATIBLE_BASE_URL")),
            bool(os.getenv("OPENAI_COMPATIBLE_API_KEY")),
        )
    )
    real_reason = (
        "Phase 3 credentials are present, but real-model memo execution is not enabled in this "
        "prototype UI; use the guarded experiment runner."
        if live_configured
        else "Requires the Phase 3 live gate, endpoint, API key, model configuration, and budget."
    )
    return (
        BackendAvailability(
            "deterministic",
            "Deterministic demo backend",
            True,
            "Local, reproducible, and API-key free.",
        ),
        BackendAvailability(
            "stochastic",
            "Stochastic research backend",
            False,
            "Available for Phase 2 evaluation, not analyst memo generation.",
        ),
        BackendAvailability("real", "Real model backend", False, real_reason),
    )


def issuer_records(seed: int = 17) -> tuple[IssuerRecord, ...]:
    return generate_universe(seed).issuers


def issuer_summary(issuer_id: str, seed: int = 17) -> dict[str, str | float]:
    issuer = generate_universe(seed).issuer(issuer_id)
    return {
        "Issuer": issuer.name,
        "Sector": issuer.sector.replace("_", " ").title(),
        "Rating": issuer.rating,
        "Gross leverage": issuer.leverage,
        "Interest coverage": issuer.interest_coverage,
        "5Y spread (bp)": issuer.spread_bps,
        "5Y CDS (bp)": issuer.cds_bps,
        "Free cash flow ($bn)": issuer.free_cash_flow_bn,
    }


def workflow_config(profile: str, *, seed: int = 17) -> WorkflowConfig:
    if profile == "H0_minimal":
        return WorkflowConfig(
            architecture=profile,
            specialists_enabled=False,
            critic_enabled=False,
            verification_enabled=False,
            persistent_state=False,
            structured_outputs=False,
            tool_access=False,
            retrieval_enabled=True,
            explicit_workflow=False,
            seed=seed,
        )
    if profile == "H1_structured":
        return WorkflowConfig(
            architecture=profile,
            specialists_enabled=False,
            critic_enabled=False,
            verification_enabled=False,
            persistent_state=True,
            structured_outputs=True,
            tool_access=True,
            retrieval_enabled=True,
            explicit_workflow=True,
            seed=seed,
        )
    if profile == "H2_strong":
        return WorkflowConfig(architecture=profile, seed=seed)
    raise KeyError(f"unknown workflow profile: {profile}")


def prepare_plan(session: WorkbenchSession):
    question = _question(session)
    engine = ResearchWorkbench(workflow_config(session.workflow_profile))
    session.plan = engine.create_plan(question)
    session.plan_approved = False
    session.run = None
    session.stage_history = ["Planning"]
    return session.plan


def approve_plan(session: WorkbenchSession) -> None:
    if session.plan is None:
        raise ValueError("prepare a research plan before approval")
    session.plan_approved = True


def run_research(session: WorkbenchSession, progress_callback: Any | None = None):
    if session.backend != "deterministic":
        raise ValueError("the selected backend is not available for analyst memo generation")
    if not session.plan_approved:
        raise ValueError("approve the research plan before execution")
    engine = ResearchWorkbench(workflow_config(session.workflow_profile))
    session.stage_history = []

    def record(stage: str) -> None:
        session.stage_history.append(stage)
        if progress_callback is not None:
            progress_callback(stage)

    session.run = engine.run(
        session.selected_issuer,
        question=_question(session),
        additional_evidence=(
            tuple(session.uploaded_evidence)
            if session.source_mode == "Synthetic data + local uploads"
            else ()
        ),
        progress_callback=record,
    )
    session.challenge_statuses = {
        challenge.id: challenge.resolution_status for challenge in session.run.state.challenges
    }
    session.review_status = ReviewStatus.NOT_REVIEWED
    return session.run


def parse_upload(filename: str, content: bytes, issuer_id: str) -> tuple[EvidenceItem, ...]:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_UPLOADS:
        raise ValueError(f"unsupported upload type: {suffix or 'none'}")
    if not content:
        raise ValueError("uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("uploaded file exceeds the 5 MiB local prototype limit")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("uploaded file must be UTF-8 text") from error
    digest = hashlib.sha256(filename.encode() + b"\0" + content).hexdigest()[:12]
    if suffix in {".txt", ".md"}:
        return (
            _uploaded_evidence(
                identifier=f"upload-{digest}-1",
                filename=filename,
                text=text.strip(),
                issuer_id=issuer_id,
                locator="document:1",
                tags=("uploaded", suffix[1:]),
            ),
        )
    return _parse_csv(filename, text, issuer_id, digest)


def add_upload(
    session: WorkbenchSession, filename: str, content: bytes
) -> tuple[EvidenceItem, ...]:
    items = parse_upload(filename, content, session.selected_issuer)
    existing = {item.id for item in session.uploaded_evidence}
    session.uploaded_evidence.extend(item for item in items if item.id not in existing)
    if filename not in session.uploaded_filenames:
        session.uploaded_filenames.append(filename)
    session.invalidate_run()
    return items


def set_challenge_status(session: WorkbenchSession, challenge_id: str, status: str) -> None:
    if session.run is None:
        raise ValueError("run research before reviewing challenges")
    if status not in CHALLENGE_STATUSES:
        raise ValueError(f"unknown challenge status: {status}")
    if challenge_id not in {item.id for item in session.run.state.challenges}:
        raise KeyError(f"unknown challenge: {challenge_id}")
    session.challenge_statuses[challenge_id] = status
    _append_audit(
        session,
        "challenge_status_changed",
        challenge_id,
        status=status,
        reviewer=session.reviewer or "workbench user",
    )


def record_human_review(
    session: WorkbenchSession,
    *,
    status: ReviewStatus,
    reviewer: str,
    note: str,
) -> None:
    if session.run is None:
        raise ValueError("run research before recording human review")
    if status != ReviewStatus.NOT_REVIEWED and not reviewer.strip():
        raise ValueError("reviewer name is required for a human decision")
    session.review_status = status
    session.reviewer = reviewer.strip()
    session.review_note = note.strip()
    _append_audit(
        session,
        "workbench_human_review",
        session.selected_issuer,
        status=status.value,
        reviewer=session.reviewer,
        note=session.review_note,
    )


def build_export_bundle(session: WorkbenchSession) -> ExportBundle:
    if session.run is None:
        raise ValueError("run research before exporting")
    memo = render_memo_markdown(session).encode()
    payload = _session_payload(session)
    audit = [item.model_dump(mode="json") for item in session.run.state.audit]
    return ExportBundle(
        memo_markdown=memo,
        research_session_json=_json_bytes(payload),
        audit_trace_json=_json_bytes(audit),
        evidence_csv=_evidence_csv(session).encode(),
        claims_csv=_claims_csv(session).encode(),
    )


def render_memo_markdown(session: WorkbenchSession) -> str:
    if session.run is None:
        raise ValueError("run research before rendering a memo")
    run = session.run
    memo = run.memo
    issuer = generate_universe(run.config.seed).issuer(session.selected_issuer)
    opposing = "\n".join(
        f"- {challenge.explanation}" for challenge in run.state.challenges
    ) or "- No separate challenge was produced under this workflow profile."
    risks = "\n".join(
        f"- **{risk.name.replace('_', ' ').title()} (severity {risk.severity}/5):** "
        f"{risk.description} Trigger: {risk.trigger}"
        for risk in memo.key_risks
    ) or "- No structured risks recorded."
    scenarios = "\n".join(
        f"- **{item.name.title()} ({item.probability:.0%}):** {item.rationale} "
        f"(spread {item.spread_change_bps:+.0f}bp, rates {item.rate_change_bps:+.0f}bp)"
        for item in memo.scenarios
    )
    evidence = "\n".join(
        f"| {item.id} | {item.source} | {item.title} | {item.locator} |"
        for item in run.state.evidence.values()
    )
    verification_notes = "\n".join(f"- {note}" for note in run.verification.notes) or "- None."
    calculations = "\n".join(
        f"- **{item.tool_name}:** inputs `{json.dumps(item.inputs, sort_keys=True)}` → "
        f"`{json.dumps(item.value, sort_keys=True)}` {item.units or ''}"
        for item in run.state.tool_results.values()
    ) or "- No deterministic calculations were run."
    unresolved = "\n".join(f"- {item}" for item in memo.unresolved_questions) or "- None recorded."
    invalidation = "\n".join(f"- {item}" for item in memo.invalidation_conditions)
    review = (
        f"- Status: **{session.review_status.value}**\n"
        f"- Reviewer: {session.reviewer or 'Not recorded'}\n"
        f"- Note: {session.review_note or 'None'}"
    )
    return f"""# Credit Research Memo

## Executive Summary
{memo.executive_summary}

## Research Question
{run.state.question.text}

## Issuer Overview
{memo.issuer_overview} Revenue is ${issuer.revenue_bn:.1f}bn and rating is {issuer.rating}.

## Fundamental Credit Analysis
{memo.fundamental_credit_analysis}

## Capital Structure
Debt is ${issuer.debt_bn:.1f}bn, cash is ${issuer.cash_bn:.1f}bn, and the evaluated bond maturity is {issuer.bond_maturity_years:.1f} years.

## Market Pricing
{memo.market_pricing}

## Peer Relative Value
{memo.peer_relative_value}

## Macro / Rates Context
{memo.macro_rates_context}

## Scenario Analysis
{scenarios}

## Investment Thesis
{memo.thesis.conclusion}

## Evidence Against the Thesis
{opposing}

## Key Risks
{risks}

## Thesis Invalidation Conditions
{invalidation}

## Portfolio / Risk Impact
{calculations}

## Unresolved Questions
{unresolved}

## Confidence
{memo.confidence_assessment}

## Evidence Table
| Evidence ID | Source | Title | Locator |
|---|---|---|---|
{evidence}

## Verification Summary
- Valid: {run.verification.valid}
- Claim support rate: {run.verification.claim_support_rate:.0%}
- Citation validity: {run.verification.citation_validity:.0%}
- Evidence coverage: {run.verification.evidence_coverage:.0%}
- Unsupported claims: {len(run.verification.unsupported_claim_ids)}
{verification_notes}

## Human Review
{review}

## Audit Metadata
- Session ID: `{session.session_id}`
- Dataset version: `{memo.audit_metadata['dataset_version']}`
- Workflow: `{session.workflow_profile}`
- Backend: `{session.backend}`
- Audit events: {len(run.state.audit)}
- Uploaded local sources: {len(session.uploaded_evidence)}
"""


def _question(session: WorkbenchSession) -> ResearchQuestion:
    text = session.question.strip()
    if len(text) < 10:
        raise ValueError("research question must contain at least 10 characters")
    return ResearchQuestion(issuer_id=session.selected_issuer, text=text)


def _uploaded_evidence(
    *,
    identifier: str,
    filename: str,
    text: str,
    issuer_id: str,
    locator: str,
    tags: tuple[str, ...],
) -> EvidenceItem:
    if not text:
        raise ValueError("uploaded document contains no readable text")
    return EvidenceItem(
        id=identifier,
        source=f"local upload: {filename}",
        title=filename,
        text=text,
        locator=locator,
        issuer_id=issuer_id,
        tags=tags,
    )


def _parse_csv(
    filename: str, text: str, issuer_id: str, digest: str
) -> tuple[EvidenceItem, ...]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV upload requires a header row")
    rows = list(reader)
    if not rows:
        raise ValueError("CSV upload contains no data rows")
    if len(rows) > 200:
        raise ValueError("CSV upload exceeds the 200-row prototype limit")
    return tuple(
        _uploaded_evidence(
            identifier=f"upload-{digest}-{index}",
            filename=filename,
            text="; ".join(f"{key}: {value}" for key, value in row.items()),
            issuer_id=issuer_id,
            locator=f"row:{index + 1}",
            tags=("uploaded", "csv"),
        )
        for index, row in enumerate(rows, start=1)
    )


def _append_audit(
    session: WorkbenchSession, event_type: str, object_id: str, **details: Any
) -> None:
    assert session.run is not None
    session.run.state.audit.append(
        AuditEvent(
            sequence=len(session.run.state.audit) + 1,
            event_type=event_type,
            actor=AgentRole.HUMAN,
            object_id=object_id,
            details=details,
        )
    )


def _session_payload(session: WorkbenchSession) -> dict[str, Any]:
    assert session.run is not None
    return {
        "session_id": session.session_id,
        "selected_issuer": session.selected_issuer,
        "question": session.question,
        "backend": session.backend,
        "workflow_profile": session.workflow_profile,
        "source_mode": session.source_mode,
        "uploaded_filenames": session.uploaded_filenames,
        "challenge_statuses": session.challenge_statuses,
        "human_review": {
            "status": session.review_status.value,
            "reviewer": session.reviewer,
            "note": session.review_note,
        },
        "config": session.run.config.model_dump(mode="json"),
        "state": session.run.state.model_dump(mode="json"),
        "memo": session.run.memo.model_dump(mode="json"),
        "verification": session.run.verification.model_dump(mode="json"),
        "metrics": session.run.metrics,
    }


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _evidence_csv(session: WorkbenchSession) -> str:
    assert session.run is not None
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("evidence_id", "source", "title", "locator", "issuer_id", "published_date"))
    for item in session.run.state.evidence.values():
        writer.writerow((item.id, item.source, item.title, item.locator, item.issuer_id, item.published_date))
    return output.getvalue()


def _claims_csv(session: WorkbenchSession) -> str:
    assert session.run is not None
    unsupported = set(session.run.verification.unsupported_claim_ids)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("claim_id", "type", "text", "confidence", "evidence_ids", "tool_result_ids", "verification_status"))
    for item in session.run.state.claims.values():
        writer.writerow((item.id, item.claim_type.value, item.text, item.confidence, "|".join(item.evidence_ids), "|".join(item.tool_result_ids), "unsupported" if item.id in unsupported else "supported"))
    return output.getvalue()
