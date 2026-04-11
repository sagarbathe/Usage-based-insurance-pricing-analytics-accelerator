"""
📊 Portfolio Manager Persona Page

Purpose: "Is UBI improving the book of business?"

Power BI Report: UBI Portfolio Health
Data Agent: Portfolio Risk Copilot
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, process_pending_queries


def render() -> None:
    """Render the Portfolio Manager persona page."""

    st.header("📊 Portfolio Manager")
    st.caption("Is UBI improving the book of business?")
    st.divider()

    # ── Tabs for view navigation (preserves component state) ─────────────────────
    tab1, tab2, tab3 = st.tabs([
        "◻️ Split View",
        "📊 Expand Report",
        "💬 Expand Agent"
    ])

    # ── Helper: render report content ─────────────────────
    def _render_report():
        report = POWERBI_REPORTS["portfolio"]
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
- **Risk Distribution Over Time** — monthly trend of high / medium / low risk drivers
- **Premium Change vs Loss Outcome** — are UBI adjustments correlating with better outcomes?
- **High-Risk Driver Trend** — is the share of high-risk drivers shrinking?
- **Coverage Level Profitability** — which coverage types are profitable under UBI?
            """
        )
        st.markdown("#### 🗂️ Gold Tables Powering This View")
        st.markdown(
            """
| Table | Purpose |
|-------|---------|
| `gold_driver_monthly_features` | Monthly driver behavior rollup for trend analysis |
| `gold_policy_premium_recommendation` | Premium changes and UBI adjustments |
| `gold_policy_period_loss` | Actual claims & payouts for loss tracking |
            """
        )

    # ── Helper: render agent content ──────────────────────
    def _render_agent():
        agent = DATA_AGENTS["portfolio"]
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
    
    # Process any pending queries after all agents have rendered
    process_pending_queries()
