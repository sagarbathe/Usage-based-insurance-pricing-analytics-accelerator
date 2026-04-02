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
from components.powerbi_embed import render_powerbi_report, render_powerbi_explore
from components.data_agent_chat import render_data_agent_chat, render_data_agent_chat_input


def render() -> None:
    """Render the Pricing / Actuarial persona page."""

    st.header("📐 Pricing / Actuarial")
    st.caption(
        "Are we pricing risk correctly, and will we hit our target loss ratio?"
    )
    st.divider()

    # ── Tabs for view navigation (preserves component state) ─────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Power BI Dashboard",
        "🔍 Explore / Ad-hoc",
        "💬 Pricing Agent on Lakehouse and KQL",
        "🧠 Pricing Agent on FabricIQ Ontology"
    ])

    # ── 1. Power BI Dashboard ─────────────────────────────
    with tab1:
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

    # ── 2. Explore / Ad-hoc Analysis ────────────────────
    with tab2:
        report = POWERBI_REPORTS["pricing"]
        render_powerbi_explore(
            explore_report_id=report.get("explore_report_id", ""),
            group_id=report.get("group_id", ""),
            title="Pricing Ad-hoc Analysis",
        )

    # ── 3. Pricing Agent on Semantic Model ────────────────
    with tab3:
        agent = DATA_AGENTS["pricing"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )

    # ── 4. Pricing Agent on FabricIQ (Ontology) ──────────
    with tab4:
        agent = DATA_AGENTS["pricing_ontology"]
        render_data_agent_chat(
            agent_name=agent["name"],
            endpoint=agent["endpoint"],
            suggested_prompts=agent["suggested_prompts"],
        )
