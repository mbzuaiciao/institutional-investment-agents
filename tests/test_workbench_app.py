from __future__ import annotations

import importlib
from datetime import date

from workbench.components.research_views import _freshness_status
from workbench.components.review_export import _event_stage


def test_streamlit_app_imports_without_starting_server() -> None:
    module = importlib.import_module("workbench.app")
    assert callable(module.main)


def test_evidence_freshness_is_relative_to_research_package() -> None:
    assert _freshness_status("2026-07-15", date(2026, 7, 15)) == "Current"
    assert _freshness_status("2026-03-01", date(2026, 7, 15)) == "Stale"
    assert _freshness_status(None, date(2026, 7, 15)) == "Undated"


def test_audit_events_map_to_visible_workflow_stages() -> None:
    assert _event_stage("plan_created") == "Planning"
    assert _event_stage("tool_result") == "Financial calculations"
    assert _event_stage("workbench_human_review") == "Human review"
