"""Explicit, resettable session state for the Streamlit workbench."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from institutional_investment_agents.schemas import EvidenceItem, ResearchPlan
from institutional_investment_agents.workflow import ResearchRun

DEFAULT_QUESTION = (
    "Assess this issuer's 5-year credit risk and relative value. Identify the strongest "
    "evidence for and against the thesis, key downside scenarios, and conditions that would "
    "invalidate the conclusion."
)


class ReviewStatus(StrEnum):
    NOT_REVIEWED = "Not reviewed"
    APPROVED = "Approved"
    REVISION_REQUESTED = "Revision requested"
    REJECTED = "Rejected"


@dataclass
class WorkbenchSession:
    session_id: str = field(default_factory=lambda: uuid4().hex)
    selected_issuer: str = "NRT"
    question: str = DEFAULT_QUESTION
    backend: str = "deterministic"
    workflow_profile: str = "H2_strong"
    source_mode: str = "Bundled synthetic data"
    plan: ResearchPlan | None = None
    plan_approved: bool = False
    run: ResearchRun | None = None
    uploaded_evidence: list[EvidenceItem] = field(default_factory=list)
    uploaded_filenames: list[str] = field(default_factory=list)
    challenge_statuses: dict[str, str] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.NOT_REVIEWED
    reviewer: str = ""
    review_note: str = ""
    stage_history: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def invalidate_run(self) -> None:
        self.plan = None
        self.plan_approved = False
        self.run = None
        self.challenge_statuses.clear()
        self.review_status = ReviewStatus.NOT_REVIEWED
        self.reviewer = ""
        self.review_note = ""
        self.stage_history.clear()


def new_session() -> WorkbenchSession:
    return WorkbenchSession()


def get_or_create_session(
    state: MutableMapping[Any, Any], *, key: str = "research_session"
) -> WorkbenchSession:
    existing = state.get(key)
    if isinstance(existing, WorkbenchSession):
        return existing
    session = new_session()
    state[key] = session
    return session


def reset_session(
    state: MutableMapping[Any, Any], *, key: str = "research_session"
) -> WorkbenchSession:
    session = new_session()
    state[key] = session
    return session
