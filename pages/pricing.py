"""
📐 Pricing / Actuarial Persona Page

Purpose: "Are we pricing risk correctly, and will we hit our target loss ratio?"

Three views:
  1. Power BI Dashboard
  2. Pricing Agent on Semantic Model (Data Agent)
  3. Pricing Agent on FabricIQ (Ontology)
"""

import streamlit as st

from config import POWERBI_REPORTS, DATA_AGENTS
from components.powerbi_embed import render_powerbi_report
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Pricing / Actuarial persona page."""

    st.header("📐 Pricing / Actuarial")
    st.caption(
        "Are we pricing risk correctly, and will we hit our target loss ratio?"
    )
    st.divider()

    # ── View selector ─────────────────────────────────────
    view_key = "pricing_view_mode"
    if view_key not in st.session_state:
        st.session_state[view_key] = "dashboard"

    cols = st.columns(3)
    with cols[0]:
        if st.button("📊 Power BI Dashboard", key="pricing_btn_dashboard",
                     use_container_width=True,
                     disabled=(st.session_state[view_key] == "dashboard")):
            st.session_state[view_key] = "dashboard"
            st.rerun()
    with cols[1]:
        if st.button("💬 Pricing Agent on Semantic Model", key="pricing_btn_agent_sm",
                     use_container_width=True,
                     disabled=(st.session_state[view_key] == "agent_semantic")):
            st.session_state[view_key] = "agent_semantic"
            st.rerun()
    with cols[2]:
        if st.button("🧠 Pricing Agent on FabricIQ", key="pricing_btn_agent_onto",
                     use_container_width=True,
                     disabled=(st.session_state[view_key] == "agent_ontology")):
            st.session_state[view_key] = "agent_ontology"
            st.rerun()

    st.divider()

    view_mode = st.session_state[view_key]

    # ── 1. Power BI Dashboard ─────────────────────────────
    if view_mode == "dashboard":
        report = POWERBI_REPORTS["pricing"]
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
- **Expected Loss Cost vs Recommended Premium** — scatter view to identify mispriced policies
- **Loss Ratio by Coverage Type** — are certain coverages consistently unprofitable?
- **Policies where ELC > Premium** — underpricing risk flagged visually
            """
        )

    # ── 2. Pricing Agent on Semantic Model ────────────────
    elif view_mode == "agent_semantic":
        agent = DATA_AGENTS["pricing"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )
        render_data_agent_chat_input(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
        )

    # ── 3. Pricing Agent on FabricIQ (Ontology) ──────────
    elif view_mode == "agent_ontology":
        agent = DATA_AGENTS["pricing_ontology"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )
        render_data_agent_chat_input(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
        )
