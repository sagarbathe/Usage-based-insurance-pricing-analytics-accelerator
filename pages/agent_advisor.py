"""
🧑‍💼 Agent / Advisor Persona Page

Purpose: "Help me explain this premium to the customer."

Power BI Report: Customer Premium Explanation
Data Agent: Agent Copilot
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Agent / Advisor persona page."""

    st.header("🧑‍💼 Agent / Advisor")
    st.caption("Help me explain this premium to the customer.")
    st.divider()

    # ── Tabs for view navigation (preserves component state) ─────────────────────
    tab1, tab2, tab3 = st.tabs([
        "◻️ Split View",
        "📊 Expand Report",
        "💬 Expand Agent"
    ])

    # ── Helper: render report content ─────────────────────
    def _render_report():
        report = POWERBI_REPORTS["agent_advisor"]
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
- **Current vs Recommended Premium** — clear side-by-side comparison
- **Simple Reason Codes** — customer-friendly icons and labels explaining the change
- **Safety Improvement Opportunities** — actionable tips the customer can follow
            """
        )
        st.markdown("#### 💡 Customer Conversation Tips")
        st.markdown(
            """
| If the customer asks… | You can say… |
|----------------------|-------------|
| *"Why did my premium go up?"* | Use the reason codes panel to show specific driving factors |
| *"What can I do to lower it?"* | Point to the safety improvement section for actionable tips |
| *"Is this fair?"* | Show the peer comparison — how they rank vs similar drivers |
            """
        )
        st.markdown("#### 🗂️ Gold Tables Powering This View")
        st.markdown(
            """
| Table | Purpose |
|-------|---------|
| `gold_policy_premium_recommendation` | Current vs recommended premium, change % |
| `gold_premium_reason_codes` | Explainable factors behind the recommendation |
            """
        )

    # ── Helper: render agent content ──────────────────────
    def _render_agent():
        agent = DATA_AGENTS["agent_advisor"]
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
