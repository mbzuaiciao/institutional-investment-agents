"""Sidebar configuration and local-source controls."""

from __future__ import annotations

import streamlit as st

from workbench.services import add_upload, backend_availability, issuer_records
from workbench.session import WorkbenchSession, reset_session

WORKFLOW_LABELS = {
    "H2_strong": "H2 · Full auditable workflow",
    "H1_structured": "H1 · Structured workflow",
    "H0_minimal": "H0 · Minimal workflow",
}


def render_sidebar(session: WorkbenchSession) -> None:
    with st.sidebar:
        st.header("Configuration")
        issuers = issuer_records()
        issuer_ids = [item.issuer_id for item in issuers]
        labels = {item.issuer_id: f"{item.name} · {item.rating}" for item in issuers}
        selected = st.selectbox(
            "Issuer",
            issuer_ids,
            index=issuer_ids.index(session.selected_issuer),
            format_func=lambda value: labels[value],
        )
        if selected != session.selected_issuer:
            session.selected_issuer = selected
            session.uploaded_evidence.clear()
            session.uploaded_filenames.clear()
            session.invalidate_run()

        backends = backend_availability()
        available = [item for item in backends if item.available]
        backend_ids = [item.identifier for item in available]
        session.backend = st.selectbox(
            "Research backend",
            backend_ids,
            index=backend_ids.index(session.backend) if session.backend in backend_ids else 0,
            format_func=lambda value: next(item.label for item in available if item.identifier == value),
        )
        with st.expander("Backend status"):
            for item in backends:
                icon = "✅" if item.available else "⏸️"
                st.caption(f"{icon} **{item.label}** — {item.reason}")

        profiles = list(WORKFLOW_LABELS)
        profile = st.selectbox(
            "Workflow profile",
            profiles,
            index=profiles.index(session.workflow_profile),
            format_func=lambda value: WORKFLOW_LABELS[value],
        )
        if profile != session.workflow_profile:
            session.workflow_profile = profile
            session.invalidate_run()

        source_mode = st.radio(
            "Research sources",
            ("Bundled synthetic data", "Synthetic data + local uploads"),
            index=0 if session.source_mode == "Bundled synthetic data" else 1,
        )
        if source_mode != session.source_mode:
            session.source_mode = source_mode
            session.invalidate_run()

        if source_mode == "Synthetic data + local uploads":
            uploads = st.file_uploader(
                "Add local research material",
                type=("txt", "md", "csv"),
                accept_multiple_files=True,
                help="Files remain in this browser session and are not uploaded to an external API.",
            )
            if st.button("Add files to evidence", disabled=not uploads, width="stretch"):
                try:
                    count = 0
                    for upload in uploads:
                        count += len(add_upload(session, upload.name, upload.getvalue()))
                    st.success(f"Added {count} evidence item(s).")
                except ValueError as error:
                    session.diagnostics.append(str(error))
                    st.error(str(error))
            if session.uploaded_filenames:
                st.caption("Local sources: " + ", ".join(session.uploaded_filenames))

        st.divider()
        if st.button("New research session", type="secondary", width="stretch"):
            reset_session(st.session_state)
            st.rerun()
        st.caption(f"Session `{session.session_id[:10]}`")
