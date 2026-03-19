"""
Configuration for Usage-based Pricing Intelligence App.
Contains Power BI report URLs, Fabric Data Agent endpoints,
and persona definitions.

Authentication: System-assigned Managed Identity on Azure App Service.
All IDs and endpoints are read from App Settings (environment variables)
configured in deploy.ps1.
"""

import os


def _env(name: str, default: str = "") -> str:
    """Return an environment variable or a default."""
    return os.environ.get(name, default)


# ──────────────────────────────────────────────
# Common IDs (set once via Azure App Settings)
# ──────────────────────────────────────────────
_WORKSPACE_ID = _env("FABRIC_WORKSPACE_ID", "<YOUR_WORKSPACE_ID>")
_TENANT_ID = _env("AZURE_TENANT_ID", "<YOUR_TENANT_ID>")

# ──────────────────────────────────────────────
# Power BI Embedded Reports
# Override report_id per persona via env vars,
# e.g. POWERBI_PRICING_REPORT_ID
# ──────────────────────────────────────────────
POWERBI_REPORTS = {
    "pricing": {
        "title": "Pricing Adequacy Dashboard",
        "report_id": _env("POWERBI_PRICING_REPORT_ID", "<YOUR_PRICING_REPORT_ID>"),
        "group_id": _env("POWERBI_PRICING_GROUP_ID", _WORKSPACE_ID),
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={_env('POWERBI_PRICING_REPORT_ID', '<YOUR_PRICING_REPORT_ID>')}"
            f"&autoAuth=true&ctid={_TENANT_ID}"
        ),
        "description": (
            "Expected Loss Cost vs Recommended Premium · Loss Ratio by coverage type · "
            "Distribution of premium increases/decreases · Policies where ELC > Premium"
        ),
        # Blank report on the same semantic model for ad-hoc explore
        "explore_report_id": _env("POWERBI_PRICING_EXPLORE_REPORT_ID", ""),
    },
    "underwriting": {
        "title": "UBI Underwriting Workbench",
        "report_id": _env("POWERBI_UNDERWRITING_REPORT_ID", "<YOUR_UNDERWRITING_REPORT_ID>"),
        "group_id": _env("POWERBI_UNDERWRITING_GROUP_ID", _WORKSPACE_ID),
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={_env('POWERBI_UNDERWRITING_REPORT_ID', '<YOUR_UNDERWRITING_REPORT_ID>')}"
            f"&groupId={_env('POWERBI_UNDERWRITING_GROUP_ID', _WORKSPACE_ID)}"
        ),
        "description": (
            "Driver behavior summary · Risk score trend · "
            "Comparison vs similar drivers · Reason codes driving premium change"
        ),
    },
    "agent_advisor": {
        "title": "Customer Premium Explanation",
        "report_id": _env("POWERBI_AGENT_REPORT_ID", "<YOUR_AGENT_REPORT_ID>"),
        "group_id": _env("POWERBI_AGENT_GROUP_ID", _WORKSPACE_ID),
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={_env('POWERBI_AGENT_REPORT_ID', '<YOUR_AGENT_REPORT_ID>')}"
            f"&groupId={_env('POWERBI_AGENT_GROUP_ID', _WORKSPACE_ID)}"
        ),
        "description": (
            "Current vs recommended premium · Simple reason codes · "
            "Safety improvement opportunities"
        ),
    },
    "portfolio": {
        "title": "UBI Portfolio Health",
        "report_id": _env("POWERBI_PORTFOLIO_REPORT_ID", "<YOUR_PORTFOLIO_REPORT_ID>"),
        "group_id": _env("POWERBI_PORTFOLIO_GROUP_ID", _WORKSPACE_ID),
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={_env('POWERBI_PORTFOLIO_REPORT_ID', '<YOUR_PORTFOLIO_REPORT_ID>')}"
            f"&groupId={_env('POWERBI_PORTFOLIO_GROUP_ID', _WORKSPACE_ID)}"
        ),
        "description": (
            "Risk distribution over time · Premium change vs loss outcome · "
            "High-risk driver trend · Coverage level profitability"
        ),
    },
    "executive": {
        "title": "UBI Business Impact",
        "report_id": _env("POWERBI_EXECUTIVE_REPORT_ID", "<YOUR_EXECUTIVE_REPORT_ID>"),
        "group_id": _env("POWERBI_EXECUTIVE_GROUP_ID", _WORKSPACE_ID),
        "embed_url": (
            f"https://app.powerbi.com/reportEmbed"
            f"?reportId={_env('POWERBI_EXECUTIVE_REPORT_ID', '<YOUR_EXECUTIVE_REPORT_ID>')}"
            f"&groupId={_env('POWERBI_EXECUTIVE_GROUP_ID', _WORKSPACE_ID)}"
        ),
        "description": (
            "Loss ratio before vs after UBI · Retention proxy · "
            "Risk reduction trends · Strategic KPIs"
        ),
    },
}

# ──────────────────────────────────────────────
# Fabric Data Agent Endpoints
# Override via env vars, e.g. FABRIC_PRICING_AGENT_ENDPOINT
# ──────────────────────────────────────────────
_AGENT_BASE = f"https://api.fabric.microsoft.com/v1/workspaces/{_WORKSPACE_ID}/dataagents"

DATA_AGENTS = {
    "pricing": {
        "name": "Pricing Agent",
        "endpoint": _env(
            "FABRIC_PRICING_AGENT_ENDPOINT",
            f"{_AGENT_BASE}/{_env('FABRIC_PRICING_AGENT_ID', '<YOUR_PRICING_AGENT_ID>')}/aiassistant/openai",
        ),
        "suggested_prompts": [
            "Which policies are underpriced relative to expected loss?",
            "Why is policy POL4020 underpriced?",
            "List drivers with high severity accidents who were underpriced the following year",
        ],
    },
    "pricing_ontology": {
        "name": "Pricing Agent (FabricIQ)",
        "endpoint": _env(
            "FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT",
            f"{_AGENT_BASE}/{_env('FABRIC_PRICING_ONTOLOGY_AGENT_ID', '<YOUR_PRICING_ONTOLOGY_AGENT_ID>')}/aiassistant/openai",
        ),
        "suggested_prompts": [
            "Which policies are underpriced relative to expected loss?",
            "Why is policy POL4020 underpriced?",
            "List drivers with high severity accidents who were underpriced the following year",
        ],
    },
    "underwriting": {
        "name": "Underwriting Copilot",
        "endpoint": _env(
            "FABRIC_UNDERWRITING_AGENT_ENDPOINT",
            "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/underwriting-copilot",
        ),
        "suggested_prompts": [
            "Explain this premium increase in plain English.",
            "Which driving behaviors contributed most?",
            "Compare this driver to similar drivers.",
        ],
    },
    "agent_advisor": {
        "name": "Agent Copilot",
        "endpoint": _env(
            "FABRIC_AGENT_ADVISOR_ENDPOINT",
            "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/agent-copilot",
        ),
        "suggested_prompts": [
            "How do I explain this increase to the customer?",
            "What can the customer do to lower their premium?",
            "Was night driving a major factor?",
        ],
    },
    "portfolio": {
        "name": "Portfolio Risk Copilot",
        "endpoint": _env(
            "FABRIC_PORTFOLIO_AGENT_ENDPOINT",
            "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/portfolio-copilot",
        ),
        "suggested_prompts": [
            "Are high-risk drivers improving after premium changes?",
            "Which segments benefit most from UBI?",
            "Where are we still losing money?",
        ],
    },
    "executive": {
        "name": "Executive Copilot",
        "endpoint": _env(
            "FABRIC_EXECUTIVE_AGENT_ENDPOINT",
            "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/executive-copilot",
        ),
        "suggested_prompts": [
            "Summarize the business impact of UBI.",
            "What risks remain in the portfolio?",
            "What's the next opportunity for optimization?",
        ],
    },
}

# ──────────────────────────────────────────────
# Persona definitions
# ──────────────────────────────────────────────
PERSONAS = {
    "pricing": {
        "icon": "📐",
        "title": "Pricing / Actuarial",
        "purpose": "Are we pricing risk correctly, and will we hit our target loss ratio?",
        "gold_tables": [
            "gold_policy_premium_recommendation",
            "gold_expected_loss_scores",
            "gold_policy_period_loss",
        ],
    },
    "underwriting": {
        "icon": "⚖️",
        "title": "Underwriting",
        "purpose": "Why did this premium change, and is it defensible?",
        "gold_tables": [
            "gold_policy_period_features",
            "gold_premium_reason_codes",
            "gold_trip_features",
        ],
    },
    "agent_advisor": {
        "icon": "🧑‍💼",
        "title": "Agent / Advisor",
        "purpose": "Help me explain this premium to the customer.",
        "gold_tables": [
            "gold_policy_premium_recommendation",
            "gold_premium_reason_codes",
        ],
    },
    "portfolio": {
        "icon": "📊",
        "title": "Portfolio Manager",
        "purpose": "Is UBI improving the book of business?",
        "gold_tables": [
            "gold_driver_monthly_features",
            "gold_policy_premium_recommendation",
            "gold_policy_period_loss",
        ],
    },
    "executive": {
        "icon": "🧠",
        "title": "Executive / Strategy",
        "purpose": "Is UBI worth the investment?",
        "gold_tables": [
            "gold_policy_premium_recommendation",
            "gold_expected_loss_scores",
            "gold_policy_period_loss",
            "gold_driver_monthly_features",
            "gold_policy_period_features",
        ],
    },
}
