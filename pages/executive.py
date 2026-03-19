"""
🧠 Executive / Strategy Persona Page

Purpose: "Is UBI worth the investment?"

Power BI Report: UBI Business Impact
Data Agent: Executive Copilot
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Executive / Strategy persona page."""

    st.header("🧠 Executive / Strategy")
    st.caption("Is UBI worth the investment?")
    st.divider()

    # ── View mode management ──────────────────────────────
    view_key = "executive_view_mode"
    if view_key not in st.session_state:
        st.session_state[view_key] = "both"

    view_mode = st.session_state[view_key]

    # ── View toggle toolbar ───────────────────────────────
    tb = st.columns([1, 1, 1, 4])
    with tb[0]:
        if st.button("◻️ Split View", key="executive_split",
                     disabled=(view_mode == "both"),
                     use_container_width=True):
            st.session_state[view_key] = "both"
            st.rerun()
    with tb[1]:
        if st.button("📊 Expand Report", key="executive_expand_report",
                     disabled=(view_mode == "report"),
                     use_container_width=True):
            st.session_state[view_key] = "report"
            st.rerun()
    with tb[2]:
        if st.button("💬 Expand Agent", key="executive_expand_agent",
                     disabled=(view_mode == "agent"),
                     use_container_width=True):
            st.session_state[view_key] = "agent"
            st.rerun()

    # ── Helper: render report content ─────────────────────
    def _render_report():
        report = POWERBI_REPORTS["executive"]
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
- **Loss Ratio: Before vs After UBI** — quantifiable business impact
- **Retention Proxy (Premium Fairness)** — % of policies with moderate changes (±15%)
- **Risk Reduction Trends** — safety score and harsh events over time
- **Strategic KPIs** — executive summary table with key metrics
            """
        )
        st.markdown("#### 🗂️ Gold Tables Powering This View")
        st.markdown(
            """
| Table | Purpose |
|-------|---------|
| `gold_policy_premium_recommendation` | Premium changes, UBI impact |
| `gold_expected_loss_scores` | Risk scores, expected loss cost |
| `gold_policy_period_loss` | Actual claims & payouts |
| `gold_driver_monthly_features` | Behavior trends over time |
| `gold_policy_period_features` | Policy-level feature snapshots |
            """
        )

    # ── Helper: render agent content ──────────────────────
    def _render_agent():
        agent = DATA_AGENTS["executive"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )

    # ── Layout based on view mode ─────────────────────────
    if view_mode == "both":
        col_report, col_agent = st.columns([3, 2])
        with col_report:
            _render_report()
        with col_agent:
            _render_agent()
    elif view_mode == "report":
        _render_report()
    elif view_mode == "agent":
        _render_agent()

    # Chat input must be at root level (Streamlit restriction)
    if view_mode in ("both", "agent"):
        agent = DATA_AGENTS["executive"]
        render_data_agent_chat_input(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
        )
