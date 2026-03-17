"""
Usage-based Pricing Intelligence App
================================
A role-based insurance application combining Usage-Based Pricing,
Portfolio Risk, and AI Explainability — powered by Microsoft Fabric Gold tables.

Run:
    cd insurance_app
    streamlit run app.py
"""

import sys
import os
import streamlit as st

# Ensure app directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PERSONAS

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Usage-based Pricing Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# # ── Hide default Streamlit multipage nav ──
# st.markdown(
#     """
#     <style>
#     [data-testid="stSidebarNav"] {
#         display: none;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# ──────────────────────────────────────────────
# Custom CSS
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Hide default Streamlit multipage nav */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b2a 0%, #1b263b 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e1dd !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        font-size: 1.05rem;
        padding: 0.4rem 0;
    }

    /* KPI metric cards */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.82rem;
        color: #6c757d;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.4rem;
        font-weight: 700;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 20px;
    }

    /* Divider */
    hr {
        margin: 1rem 0;
        border-color: #dee2e6;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 0.5rem;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.6rem;
    }
    .app-header .subtitle {
        color: #6c757d;
        font-size: 0.9rem;
    }

    /* Grey out locked persona radio options */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:not(:nth-child(1)) {
        opacity: 0.4;
        pointer-events: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Sidebar – Persona Selector
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ Usage-based Pricing")
    st.markdown("##### Intelligence App")
    st.markdown("---")

    st.markdown("### 🧭 Select Persona")

    persona_options = {
        key: f"{meta['icon']}  {meta['title']}"
        for key, meta in PERSONAS.items()
    }

    # selected_persona = st.radio(
    #     "Persona",
    #     options=list(persona_options.keys()),
    #     format_func=lambda k: persona_options[k],
    #     label_visibility="collapsed",
    # )

    # Only "pricing" is enabled; all others are disabled
    enabled_personas = {"pricing"}

    selected_persona = st.radio(
        "Persona",
        options=list(persona_options.keys()),
        format_func=lambda k: persona_options[k] if k in enabled_personas else f"🔒 {persona_options[k]}",
        label_visibility="collapsed",
        index=list(persona_options.keys()).index("pricing"),
        disabled=False,
    )

    # Force selection back to pricing if user selects a disabled persona
    if selected_persona not in enabled_personas:
        st.warning("🔒 This persona is not available yet.")
        selected_persona = "pricing"

    st.markdown("---")

    # Persona context
    persona = PERSONAS[selected_persona]
    st.markdown(f"**Purpose:**  \n_{persona['purpose']}_")

    st.markdown("**Gold tables used:**")
    for t in persona["gold_tables"]:
        st.markdown(f"- `{t}`")

    st.markdown("---")
    st.caption("Powered by Microsoft Fabric")
    st.caption("Power BI Reports · Fabric Data Agents")

# ──────────────────────────────────────────────
# Main content – render selected persona page
# ──────────────────────────────────────────────
if selected_persona == "pricing":
    from pages.pricing import render
    render()

elif selected_persona == "underwriting":
    from pages.underwriting import render
    render()

elif selected_persona == "agent_advisor":
    from pages.agent_advisor import render
    render()

elif selected_persona == "portfolio":
    from pages.portfolio import render
    render()

elif selected_persona == "executive":
    from pages.executive import render
    render()
