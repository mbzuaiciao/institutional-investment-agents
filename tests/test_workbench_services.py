from __future__ import annotations

import json

import pytest

from workbench.services import (
    add_upload,
    approve_plan,
    backend_availability,
    build_export_bundle,
    issuer_records,
    issuer_summary,
    parse_upload,
    prepare_plan,
    record_human_review,
    run_research,
    set_challenge_status,
    workflow_config,
)
from workbench.session import ReviewStatus, WorkbenchSession


def _completed_session() -> WorkbenchSession:
    session = WorkbenchSession(
        selected_issuer="NRT",
        question=(
            "Assess Northstar Telecom credit risk, relative value, downside scenarios, and "
            "thesis invalidation conditions."
        ),
        source_mode="Synthetic data + local uploads",
    )
    add_upload(
        session,
        "analyst_note.md",
        b"Management expects refinancing costs to remain elevated through next year.",
    )
    prepare_plan(session)
    approve_plan(session)
    run_research(session)
    return session


def test_backend_availability_is_honest_and_credentials_are_not_exposed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PHASE3_ENABLE_LIVE_RUNS", "YES")
    monkeypatch.setenv("OPENAI_COMPATIBLE_BASE_URL", "https://example.invalid")
    monkeypatch.setenv("OPENAI_COMPATIBLE_API_KEY", "fixture-secret")
    options = backend_availability()
    assert options[0].identifier == "deterministic" and options[0].available
    assert not options[1].available
    assert not options[2].available
    assert "fixture-secret" not in repr(options)


def test_issuer_selection_exposes_bundled_credit_metadata() -> None:
    issuers = issuer_records()
    assert len(issuers) == 10
    summary = issuer_summary("CRH")
    assert summary["Issuer"] == "Cedar Retail Holdings"
    assert summary["Rating"] == "BB+"
    assert float(summary["Gross leverage"]) > 0


def test_upload_parser_supports_text_markdown_and_csv() -> None:
    text = parse_upload("note.txt", b"Issuer liquidity remains adequate.", "NRT")
    markdown = parse_upload("memo.md", b"# Local memo\nRisk is refinancing.", "NRT")
    csv_items = parse_upload("metrics.csv", b"metric,value\nleverage,4.0\ncoverage,3.1\n", "NRT")
    assert text[0].source == "local upload: note.txt"
    assert markdown[0].locator == "document:1"
    assert len(csv_items) == 2
    assert csv_items[0].locator == "row:2"
    assert csv_items[0].id != csv_items[1].id


def test_upload_parser_rejects_unsupported_or_malformed_inputs() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        parse_upload("report.pdf", b"not a supported PDF", "NRT")
    with pytest.raises(ValueError, match="empty"):
        parse_upload("empty.txt", b"", "NRT")
    with pytest.raises(ValueError, match="header"):
        parse_upload("empty.csv", b"\n", "NRT")


def test_plan_construction_uses_user_question_and_selected_profile() -> None:
    session = WorkbenchSession(
        selected_issuer="VTX",
        question="Assess Vertex Software refinancing risk and relative value over five years.",
        workflow_profile="H1_structured",
    )
    plan = prepare_plan(session)
    assert plan.question.text == session.question
    assert plan.question.issuer_id == "VTX"
    assert len(plan.tasks) == 4
    assert {task.assigned_role.value for task in plan.tasks} == {"single_research_agent"}


def test_workflow_requires_approval_and_exposes_full_structured_artifacts() -> None:
    session = WorkbenchSession()
    prepare_plan(session)
    with pytest.raises(ValueError, match="approve"):
        run_research(session)
    approve_plan(session)
    stages: list[str] = []
    run = run_research(session, stages.append)
    assert run.state.question.text == session.question
    assert run.state.evidence
    assert run.state.claims
    assert run.state.tool_results
    assert run.state.observations
    assert run.state.challenges
    assert run.memo.thesis.scenarios
    assert stages[0] == "Planning" and stages[-1] == "Memo generation"


def test_uploaded_evidence_enters_provenance_without_replacing_bundled_sources() -> None:
    session = _completed_session()
    assert session.run is not None
    sources = {item.source for item in session.run.state.evidence.values()}
    assert "local upload: analyst_note.md" in sources
    assert "synthetic issuer filing" in sources


def test_challenge_and_human_approval_are_recorded_in_audit() -> None:
    session = _completed_session()
    assert session.run is not None
    challenge = session.run.state.challenges[0]
    initial_events = len(session.run.state.audit)
    set_challenge_status(session, challenge.id, "unresolved")
    record_human_review(
        session,
        status=ReviewStatus.REVISION_REQUESTED,
        reviewer="A. Analyst",
        note="Resolve refinancing evidence before approval.",
    )
    assert session.challenge_statuses[challenge.id] == "unresolved"
    assert session.review_status == ReviewStatus.REVISION_REQUESTED
    assert len(session.run.state.audit) == initial_events + 2
    assert session.run.state.audit[-1].event_type == "workbench_human_review"


def test_exports_include_memo_session_audit_evidence_and_claims() -> None:
    session = _completed_session()
    record_human_review(
        session,
        status=ReviewStatus.APPROVED,
        reviewer="A. Analyst",
        note="Approved for synthetic demonstration only.",
    )
    bundle = build_export_bundle(session)
    memo = bundle.memo_markdown.decode()
    payload = json.loads(bundle.research_session_json)
    audit = json.loads(bundle.audit_trace_json)
    assert "# Credit Research Memo" in memo
    assert "## Evidence Table" in memo
    assert "## Human Review" in memo
    assert "Approved for synthetic demonstration only." in memo
    assert payload["human_review"]["status"] == "Approved"
    assert payload["state"]["evidence"]
    assert audit[-1]["event_type"] == "workbench_human_review"
    assert bundle.evidence_csv.startswith(b"evidence_id,source")
    assert bundle.claims_csv.startswith(b"claim_id,type")


def test_workflow_profiles_preserve_h0_h1_h2_controls() -> None:
    h0 = workflow_config("H0_minimal")
    h1 = workflow_config("H1_structured")
    h2 = workflow_config("H2_strong")
    assert not h0.tool_access and not h0.critic_enabled
    assert h1.tool_access and h1.explicit_workflow and not h1.critic_enabled
    assert h2.tool_access and h2.critic_enabled and h2.verification_enabled
    with pytest.raises(KeyError):
        workflow_config("unknown")
