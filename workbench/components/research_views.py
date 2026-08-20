"""Inspectable evidence, claims, calculations, specialists, thesis, and controls."""

from __future__ import annotations

import json
from datetime import date

import streamlit as st

from workbench.services import CHALLENGE_STATUSES, set_challenge_status
from workbench.session import WorkbenchSession

TOOL_FORMULAS = {
    "credit_ratios": "gross leverage = debt / EBITDA; net leverage = (debt − cash) / EBITDA; coverage = EBITDA / interest expense",
    "spread_z_score": "z = (current spread − historical mean) / historical standard deviation",
    "portfolio_impact": "P&L = −market value × duration × basis-point change / 10,000",
    "expected_loss": "cumulative PD × (1 − recovery rate)",
    "spread_bps": "(bond yield − benchmark yield) × 10,000",
}


def render_research_workspace(session: WorkbenchSession) -> None:
    if session.run is None:
        st.info("Prepare and approve a plan, then run the workflow to inspect research artifacts.")
        return
    tabs = st.tabs(
        (
            "Thesis",
            "Evidence & claims",
            "Analysis & calculations",
            "Challenge & verification",
            "Audit & export",
        )
    )
    with tabs[0]:
        _thesis(session)
    with tabs[1]:
        _evidence_claims(session)
    with tabs[2]:
        _analysis(session)
    with tabs[3]:
        _controls(session)
    with tabs[4]:
        from workbench.components.review_export import render_review_export

        render_review_export(session)


def _thesis(session: WorkbenchSession) -> None:
    assert session.run is not None
    run = session.run
    thesis = run.memo.thesis
    st.subheader("Investment thesis")
    st.markdown(f"### {thesis.conclusion}")
    columns = st.columns(4)
    columns[0].metric("Confidence", f"{thesis.confidence:.0%}")
    columns[1].metric("Research quality", f"{run.metrics['research_quality_score']:.1f}")
    columns[2].metric("Risk recall", f"{run.metrics['risk_factor_recall']:.0%}")
    columns[3].metric("Claim support", f"{run.verification.claim_support_rate:.0%}")

    st.markdown("#### Bull / base / bear scenarios")
    scenario_columns = st.columns(len(thesis.scenarios))
    for column, scenario in zip(scenario_columns, thesis.scenarios, strict=True):
        with column:
            st.markdown(f"**{scenario.name.title()} · {scenario.probability:.0%}**")
            st.write(scenario.rationale)
            st.caption(
                f"Spread {scenario.spread_change_bps:+.0f}bp · "
                f"Rates {scenario.rate_change_bps:+.0f}bp · PD {scenario.default_probability:.1%}"
            )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Key risks")
        for risk in thesis.risks:
            with st.expander(f"{risk.name.replace('_', ' ').title()} · severity {risk.severity}/5"):
                st.write(risk.description)
                st.caption(f"Trigger: {risk.trigger}")
                st.caption("Evidence: " + (", ".join(risk.evidence_ids) or "No direct citation"))
    with right:
        st.markdown("#### Invalidation conditions")
        for item in thesis.invalidation_conditions:
            st.markdown(f"- {item}")
        st.markdown("#### Unresolved questions")
        if run.state.open_questions:
            for item in run.state.open_questions:
                st.markdown(f"- {item}")
        else:
            st.caption("No unresolved questions were recorded by this deterministic run.")


def _evidence_claims(session: WorkbenchSession) -> None:
    assert session.run is not None
    state = session.run.state
    st.subheader("Evidence browser")
    sources = sorted({item.source for item in state.evidence.values()})
    selected_source = st.selectbox("Source filter", ("All sources", *sources))
    issuer_filter = st.selectbox(
        "Issuer filter", ("All", session.selected_issuer, "Macro / unassigned")
    )
    selected_claim = st.selectbox("Claim filter", ("All claims", *state.claims))
    evidence_types = sorted({tag for item in state.evidence.values() for tag in item.tags})
    selected_type = st.selectbox("Evidence type filter", ("All types", *evidence_types))
    freshness = st.selectbox(
        "Freshness filter", ("All freshness", "Current", "Stale", "Undated")
    )
    dated_items = [
        date.fromisoformat(item.published_date)
        for item in state.evidence.values()
        if item.published_date
    ]
    as_of = max(dated_items, default=None)
    linked_ids = (
        set(state.claims[selected_claim].evidence_ids) if selected_claim != "All claims" else None
    )
    evidence_rows = []
    for item in state.evidence.values():
        if selected_source != "All sources" and item.source != selected_source:
            continue
        if issuer_filter == session.selected_issuer and item.issuer_id != session.selected_issuer:
            continue
        if issuer_filter == "Macro / unassigned" and item.issuer_id is not None:
            continue
        if linked_ids is not None and item.id not in linked_ids:
            continue
        if selected_type != "All types" and selected_type not in item.tags:
            continue
        freshness_status = _freshness_status(item.published_date, as_of)
        if freshness != "All freshness" and freshness != freshness_status:
            continue
        used_by = [claim.id for claim in state.claims.values() if item.id in claim.evidence_ids]
        evidence_rows.append(
            {
                "ID": item.id,
                "Source": item.source,
                "Title": item.title,
                "Date/version": item.published_date or "Undated local input",
                "Freshness": freshness_status,
                "Type": ", ".join(item.tags) or "unclassified",
                "Excerpt": item.text[:220],
                "Used by": ", ".join(used_by) or "—",
            }
        )
    st.dataframe(evidence_rows, hide_index=True, width="stretch")

    st.subheader("Material claims")
    unsupported = set(session.run.verification.unsupported_claim_ids)
    claim_rows = [
        {
            "ID": claim.id,
            "Type": claim.claim_type.value,
            "Claim": claim.text,
            "Confidence": claim.confidence,
            "Evidence": ", ".join(claim.evidence_ids) or "—",
            "Calculations": ", ".join(claim.tool_result_ids) or "—",
            "Assumptions": ", ".join(claim.assumptions) or "—",
            "Verification": "Unsupported" if claim.id in unsupported else "Supported",
        }
        for claim in state.claims.values()
    ]
    st.dataframe(claim_rows, hide_index=True, width="stretch")


def _analysis(session: WorkbenchSession) -> None:
    assert session.run is not None
    state = session.run.state
    st.subheader("Specialist contributions")
    grouped: dict[str, list[dict[str, str]]] = {}
    for observation in state.observations:
        role = observation.actor.value.replace("_", " ").title()
        grouped.setdefault(role, []).append(
            {
                "Task": observation.task_id,
                "Contribution": observation.summary,
                "Evidence": ", ".join(observation.evidence_ids),
                "Claims": ", ".join(observation.claim_ids) or "—",
            }
        )
    for role, rows in grouped.items():
        with st.expander(role, expanded=True):
            st.dataframe(rows, hide_index=True, width="stretch")

    st.subheader("Deterministic financial calculations")
    if not state.tool_results:
        st.info("This workflow profile did not execute financial tools.")
    for result in state.tool_results.values():
        with st.expander(result.tool_name.replace("_", " ").title(), expanded=True):
            st.caption("Formula: " + TOOL_FORMULAS.get(result.tool_name, "Validated tool contract"))
            left, right = st.columns(2)
            left.markdown("**Inputs**")
            left.json(result.inputs)
            right.markdown(f"**Result · {result.units or 'unitless'}**")
            right.json(result.value)


def _controls(session: WorkbenchSession) -> None:
    assert session.run is not None
    run = session.run
    st.subheader("Adversarial challenge")
    if not run.state.challenges:
        st.info("The selected workflow profile did not run a critic.")
    for challenge in run.state.challenges:
        with st.container(border=True):
            st.markdown(
                f"**{challenge.issue_type.replace('_', ' ').title()} · severity {challenge.severity}/5**"
            )
            st.write(challenge.explanation)
            st.caption(
                "Conflicting evidence: "
                + (", ".join(challenge.conflicting_evidence_ids) or "None recorded")
            )
            current = session.challenge_statuses.get(challenge.id, challenge.resolution_status)
            selected = st.selectbox(
                "Resolution",
                CHALLENGE_STATUSES,
                index=CHALLENGE_STATUSES.index(current)
                if current in CHALLENGE_STATUSES
                else 0,
                key=f"challenge-{challenge.id}",
            )
            if st.button("Record challenge status", key=f"save-{challenge.id}"):
                set_challenge_status(session, challenge.id, selected)
                st.success("Challenge status recorded in the audit trace.")

    st.subheader("Verification controls")
    verification = run.verification
    columns = st.columns(5)
    columns[0].metric("Support", f"{verification.claim_support_rate:.0%}")
    columns[1].metric("Evidence coverage", f"{verification.evidence_coverage:.0%}")
    columns[2].metric("Citation validity", f"{verification.citation_validity:.0%}")
    columns[3].metric("Unsupported", len(verification.unsupported_claim_ids))
    columns[4].metric("Contradictions", verification.unresolved_contradictions)
    findings = [
        *(f"Unsupported claim: {item}" for item in verification.unsupported_claim_ids),
        *(f"Missing evidence: {item}" for item in verification.missing_evidence_ids),
        *verification.notes,
    ]
    if findings:
        for finding in findings:
            st.warning(finding)
    else:
        st.success("No verification exceptions were recorded.")
    st.caption(
        "Verification is a provenance and control layer; it is not a substitute for analyst judgment."
    )

    with st.expander("Workflow stage history"):
        st.write(" → ".join(session.stage_history))
    with st.expander("Structured metrics JSON"):
        st.code(json.dumps(run.metrics, indent=2, sort_keys=True), language="json")


def _freshness_status(published_date: str | None, as_of: date | None) -> str:
    """Classify freshness relative to the newest dated item in the research package."""
    if published_date is None or as_of is None:
        return "Undated"
    age_days = (as_of - date.fromisoformat(published_date)).days
    return "Current" if age_days <= 120 else "Stale"
