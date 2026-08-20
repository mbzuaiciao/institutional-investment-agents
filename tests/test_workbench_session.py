from __future__ import annotations

from workbench.session import (
    DEFAULT_QUESTION,
    ReviewStatus,
    WorkbenchSession,
    get_or_create_session,
    reset_session,
)


def test_session_initialization_is_explicit_and_isolated() -> None:
    state: dict[str, object] = {}
    session = get_or_create_session(state)
    assert isinstance(session, WorkbenchSession)
    assert session.question == DEFAULT_QUESTION
    assert session.workflow_profile == "H2_strong"
    assert session.review_status == ReviewStatus.NOT_REVIEWED
    assert get_or_create_session(state) is session


def test_reset_replaces_only_workbench_session() -> None:
    old = WorkbenchSession(selected_issuer="CRH", question="A sufficiently long question")
    state: dict[str, object] = {"research_session": old, "unrelated": "preserve"}
    new = reset_session(state)
    assert new is not old
    assert new.selected_issuer == "NRT"
    assert state["unrelated"] == "preserve"


def test_invalidate_run_preserves_local_evidence_but_clears_review() -> None:
    session = WorkbenchSession()
    session.plan_approved = True
    session.review_status = ReviewStatus.APPROVED
    session.reviewer = "Analyst"
    session.invalidate_run()
    assert session.plan is None
    assert not session.plan_approved
    assert session.review_status == ReviewStatus.NOT_REVIEWED
    assert session.reviewer == ""
