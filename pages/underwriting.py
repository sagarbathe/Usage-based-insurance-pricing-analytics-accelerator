"""
⚖️ Underwriting Persona Page

Purpose: "Why did this premium change, and is it defensible?"

Power BI Report: UBI Underwriting Workbench
Data Agent: Underwriting Copilot
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Underwriting persona page."""

    st.header("⚖️ Underwriting")
    st.caption("Why did this premium change, and is it defensible?")
    st.divider()

    # ── View selector (preserves state without st.rerun) ─────────────────────────
    if "underwriting_view" not in st.session_state:
        st.session_state.underwriting_view = "both"
    
    cols = st.columns([1, 1, 1, 4])
    with cols[0]:
        if st.button("◻️ Split", use_container_width=True,
                     type="primary" if st.session_state.underwriting_view == "both" else "secondary"):
            st.session_state.underwriting_view = "both"
    with cols[1]:
        if st.button("📊 Report", use_container_width=True,
                     type="primary" if st.session_state.underwriting_view == "report" else "secondary"):
            st.session_state.underwriting_view = "report"
    with cols[2]:
        if st.button("💬 Agent", use_container_width=True,
                     type="primary" if st.session_state.underwriting_view == "agent" else "secondary"):
            st.session_state.underwriting_view = "agent"
    
    st.divider()
    current_view = st.session_state.underwriting_view

    # ── Helper: render report content ─────────────────────
    def _render_report():
        report = POWERBI_REPORTS["underwriting"]
        render_powerbi_report(
            embed_url=report["embed_url"],
            title=report["title"],
            description=report["description"],
            report_id=report.get("report_id", ""),
            group_id=report.get("group_id", ""),
        )
        st.divider()
        st.markdown("#### 📋 Report Contents")
        st.markdown(
            """
- **Driver Behavior Summary** — speeding, harsh braking, rapid acceleration, night driving
- **Risk Score Trend** — how has this driver's risk evolved over time?
- **Comparison vs Similar Drivers** — percentile view against peer cohort
- **Reason Codes Driving Premium Change** — explainable factor breakdown
            """
        )
        st.markdown("#### 🗂️ Gold Tables Powering This View")
        st.markdown(
            """
| Table | Purpose |
|-------|---------|
| `gold_policy_period_features` | Pricing-ready features per policy term |
| `gold_premium_reason_codes` | Top factors behind each premium recommendation |
| `gold_trip_features` | Trip-level behavior data for deep dives |
            """
        )

    # ── Helper: render agent content ──────────────────────
    def _render_agent():
        agent = DATA_AGENTS["underwriting"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )

    # ── Layout with tabs ─────────────────────────
    with tab1:  # Split View
        col_report, col_agent = st.columns([3, 2])
        with col_report:
            _render_report()
        with col_agent:
            _render_agent()
    
    with tab2:  # Report Only
        _render_report()
    
    with tab3:  # Agent Only
        _render_agent()
