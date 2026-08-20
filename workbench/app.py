"""Institutional Investment Research Workbench Streamlit entry point."""

from __future__ import annotations

import streamlit as st

from workbench.components.input_plan import render_research_setup
from workbench.components.research_views import render_research_workspace
from workbench.components.sidebar import render_sidebar
from workbench.session import get_or_create_session


def main() -> None:
    st.set_page_config(
        page_title="Institutional Investment Research Workbench",
        page_icon="📑",
        layout="wide",
    )
    st.title("Institutional Investment Research Workbench")
    st.caption(
        "Structured fixed-income research with inspectable evidence, calculations, challenge, "
        "verification, human review, and audit-ready exports. Synthetic demo data only."
    )
    session = get_or_create_session(st.session_state)
    render_sidebar(session)
    render_research_setup(session)
    st.divider()
    render_research_workspace(session)


if __name__ == "__main__":
    main()
