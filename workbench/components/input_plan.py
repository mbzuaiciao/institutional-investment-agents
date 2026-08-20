"""Research question, issuer overview, and plan approval controls."""

from __future__ import annotations

import streamlit as st

from workbench.services import (
    QUESTION_EXAMPLES,
    approve_plan,
    issuer_summary,
    prepare_plan,
    run_research,
)
from workbench.session import WorkbenchSession


def render_research_setup(session: WorkbenchSession) -> None:
    st.subheader("Research question")
    metadata = issuer_summary(session.selected_issuer)
    columns = st.columns(4)
    for column, key in zip(
        columns,
        ("Issuer", "Rating", "Gross leverage", "5Y spread (bp)"),
        strict=True,
    ):
        column.metric(key, metadata[key])
    with st.expander("Issuer snapshot"):
        st.dataframe([metadata], hide_index=True, width="stretch")

    question = st.text_area(
        "Question",
        value=session.question,
        height=110,
        help="Edit freely before preparing the plan.",
    )
    if question != session.question:
        session.question = question
        session.invalidate_run()

    st.caption("Example questions")
    example_columns = st.columns(len(QUESTION_EXAMPLES))
    for index, (column, example) in enumerate(
        zip(example_columns, QUESTION_EXAMPLES, strict=True), start=1
    ):
        if column.button(f"Example {index}", help=example, width="stretch"):
            session.question = example
            session.invalidate_run()
            st.rerun()

    left, right = st.columns((1, 2))
    if left.button("Prepare research plan", type="primary", width="stretch"):
        try:
            prepare_plan(session)
        except ValueError as error:
            session.diagnostics.append(str(error))
            st.error(str(error))
    right.caption(
        "Preparing a plan does not run analysis. Review and explicitly approve it first."
    )

    if session.plan is not None:
        st.subheader("Proposed research plan")
        rows = [
            {
                "Section": item.title,
                "Objective": item.objective,
                "Owner": item.assigned_role.value.replace("_", " ").title(),
                "Status": item.status.value,
            }
            for item in session.plan.tasks
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
        if not session.plan_approved:
            if st.button("Approve plan", type="primary"):
                approve_plan(session)
                st.rerun()
        else:
            st.success("Plan approved. The structured workflow is ready to run.")
            if st.button("Run research workflow", type="primary", width="stretch"):
                _run_with_progress(session)


def _run_with_progress(session: WorkbenchSession) -> None:
    stages = (
        "Planning",
        "Evidence retrieval",
        "Financial calculations",
        "Specialist analysis",
        "Thesis synthesis",
        "Adversarial challenge",
        "Evidence verification",
        "Approval gate",
        "Memo generation",
    )
    status = st.status("Running structured research workflow…", expanded=True)
    progress = st.progress(0)

    def update(stage: str) -> None:
        position = stages.index(stage) + 1 if stage in stages else len(stages)
        status.write(f"{position}. {stage}")
        progress.progress(position / len(stages))

    try:
        run_research(session, update)
    except Exception as error:
        session.diagnostics.append(f"{type(error).__name__}: {error}")
        status.update(label="Research workflow failed", state="error")
        st.error("The workflow could not complete. See diagnostics for technical details.")
        return
    status.update(label="Research workflow complete", state="complete", expanded=False)
    st.rerun()
