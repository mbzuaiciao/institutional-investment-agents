"""Audit filtering, explicit human review, and artifact downloads."""

from __future__ import annotations

import json

import streamlit as st

from workbench.services import build_export_bundle, record_human_review
from workbench.session import ReviewStatus, WorkbenchSession


def render_review_export(session: WorkbenchSession) -> None:
    assert session.run is not None
    run = session.run
    st.subheader("Audit trace")
    event_types = sorted({item.event_type for item in run.state.audit})
    stages = sorted({_event_stage(item.event_type) for item in run.state.audit})
    actors = sorted({item.actor.value for item in run.state.audit})
    selected_stage = st.selectbox("Stage", ("All", *stages))
    selected_type = st.selectbox("Event type", ("All", *event_types))
    selected_actor = st.selectbox("Actor / role", ("All", *actors))
    tools = sorted(
        {
            str(item.details["tool"])
            for item in run.state.audit
            if "tool" in item.details
        }
    )
    selected_tool = st.selectbox("Tool", ("All", *tools))
    object_filter = st.text_input("Claim / evidence / object ID contains")
    rows = []
    for event in run.state.audit:
        stage = _event_stage(event.event_type)
        if selected_stage != "All" and stage != selected_stage:
            continue
        if selected_type != "All" and event.event_type != selected_type:
            continue
        if selected_actor != "All" and event.actor.value != selected_actor:
            continue
        if selected_tool != "All" and event.details.get("tool") != selected_tool:
            continue
        if object_filter and object_filter.lower() not in (event.object_id or "").lower():
            continue
        rows.append(
            {
                "Sequence": event.sequence,
                "Stage": stage,
                "Event": event.event_type,
                "Actor": event.actor.value,
                "Object": event.object_id or "—",
                "Metadata": json.dumps(event.details, sort_keys=True),
            }
        )
    st.dataframe(rows, hide_index=True, width="stretch")
    with st.expander("Raw audit JSON"):
        st.json([item.model_dump(mode="json") for item in run.state.audit])

    st.subheader("Human decision")
    with st.form("human-review"):
        statuses = list(ReviewStatus)
        status = st.selectbox(
            "Decision",
            statuses,
            index=statuses.index(session.review_status),
            format_func=lambda value: value.value,
        )
        reviewer = st.text_input("Reviewer", value=session.reviewer)
        note = st.text_area("Review note", value=session.review_note)
        submitted = st.form_submit_button("Record decision", type="primary")
    if submitted:
        try:
            record_human_review(session, status=status, reviewer=reviewer, note=note)
            st.success("Human decision recorded in the session and audit trace.")
        except ValueError as error:
            session.diagnostics.append(str(error))
            st.error(str(error))

    st.subheader("Export current session")
    try:
        bundle = build_export_bundle(session)
    except (TypeError, ValueError) as error:
        session.diagnostics.append(str(error))
        st.error("Exports could not be generated. See diagnostics.")
        return
    columns = st.columns(3)
    columns[0].download_button(
        "Download research memo",
        bundle.memo_markdown,
        file_name="research_memo.md",
        mime="text/markdown",
        width="stretch",
    )
    columns[1].download_button(
        "Download session JSON",
        bundle.research_session_json,
        file_name="research_session.json",
        mime="application/json",
        width="stretch",
    )
    columns[2].download_button(
        "Download audit JSON",
        bundle.audit_trace_json,
        file_name="audit_trace.json",
        mime="application/json",
        width="stretch",
    )
    columns = st.columns(2)
    columns[0].download_button(
        "Download evidence CSV",
        bundle.evidence_csv,
        file_name="evidence_table.csv",
        mime="text/csv",
        width="stretch",
    )
    columns[1].download_button(
        "Download claims CSV",
        bundle.claims_csv,
        file_name="claims.csv",
        mime="text/csv",
        width="stretch",
    )

    if session.diagnostics:
        with st.expander("Technical diagnostics"):
            for item in session.diagnostics:
                st.code(item)


def _event_stage(event_type: str) -> str:
    """Map reconstruction-friendly audit event types to analyst-facing stages."""
    if event_type.startswith("plan"):
        return "Planning"
    if event_type.startswith("evidence"):
        return "Evidence retrieval"
    if event_type.startswith("tool"):
        return "Financial calculations"
    if event_type.startswith(("claim", "task")):
        return "Specialist analysis"
    if event_type.startswith("challenge"):
        return "Adversarial challenge"
    if event_type.startswith("verification"):
        return "Evidence verification"
    if event_type.startswith(("approval", "workbench_human")):
        return "Human review"
    return "Workflow"
