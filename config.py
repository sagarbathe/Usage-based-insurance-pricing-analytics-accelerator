"""
Configuration for UBI Insurance Intelligence App.
Contains Power BI report URLs, Fabric Data Agent endpoints,
and persona definitions.

Authentication: Azure CLI (`az login`) for local dev,
Fabric Workspace Identity when deployed.
"""

# ──────────────────────────────────────────────
# Power BI Embedded Reports
# Fill in report_id + group_id for each report.
# The embed_url is used only as a fallback when
# env-vars are not set (users will see a sign-in).
# ──────────────────────────────────────────────
POWERBI_REPORTS = {
    "pricing": {
        "title": "Pricing Adequacy Dashboard",
        "report_id": "76cdd8e3-f32a-4de1-b167-74ef41440769",
        "group_id": "db7dcf85-001e-4277-a85e-3c92029900bc",
        "embed_url": "https://app.powerbi.com/reportEmbed?reportId=76cdd8e3-f32a-4de1-b167-74ef41440769&autoAuth=true&ctid=6d9c4b13-597a-4bd5-9af2-5987259103fd&actionBarEnabled=true",
        "description": (
            "Expected Loss Cost vs Recommended Premium · Loss Ratio by coverage type · "
            "Distribution of premium increases/decreases · Policies where ELC > Premium"
        ),
    },
    "underwriting": {
        "title": "UBI Underwriting Workbench",
        "report_id": "<YOUR_UNDERWRITING_REPORT_ID>",
        "group_id": "db7dcf85-001e-4277-a85e-3c92029900bc",
        "embed_url": "https://app.powerbi.com/reportEmbed?reportId=<YOUR_UNDERWRITING_REPORT_ID>&groupId=<YOUR_WORKSPACE_ID>",
        "description": (
            "Driver behavior summary · Risk score trend · "
            "Comparison vs similar drivers · Reason codes driving premium change"
        ),
    },
    "agent_advisor": {
        "title": "Customer Premium Explanation",
        "report_id": "<YOUR_AGENT_REPORT_ID>",
        "group_id": "db7dcf85-001e-4277-a85e-3c92029900bc",
        "embed_url": "https://app.powerbi.com/reportEmbed?reportId=<YOUR_AGENT_REPORT_ID>&groupId=<YOUR_WORKSPACE_ID>",
        "description": (
            "Current vs recommended premium · Simple reason codes · "
            "Safety improvement opportunities"
        ),
    },
    "portfolio": {
        "title": "UBI Portfolio Health",
        "report_id": "<YOUR_PORTFOLIO_REPORT_ID>",
        "group_id": "db7dcf85-001e-4277-a85e-3c92029900bc",
        "embed_url": "https://app.powerbi.com/reportEmbed?reportId=<YOUR_PORTFOLIO_REPORT_ID>&groupId=<YOUR_WORKSPACE_ID>",
        "description": (
            "Risk distribution over time · Premium change vs loss outcome · "
            "High-risk driver trend · Coverage level profitability"
        ),
    },
    "executive": {
        "title": "UBI Business Impact",
        "report_id": "<YOUR_EXECUTIVE_REPORT_ID>",
        "group_id": "db7dcf85-001e-4277-a85e-3c92029900bc",
        "embed_url": "https://app.powerbi.com/reportEmbed?reportId=<YOUR_EXECUTIVE_REPORT_ID>&groupId=<YOUR_WORKSPACE_ID>",
        "description": (
            "Loss ratio before vs after UBI · Retention proxy · "
            "Risk reduction trends · Strategic KPIs"
        ),
    },
}

# ──────────────────────────────────────────────
# Fabric Data Agent Endpoints (placeholders)
# Replace with your actual Data Agent endpoints
# ──────────────────────────────────────────────
DATA_AGENTS = {
    "pricing": {
        "name": "Pricing Agent",
        "endpoint": "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/7a3c56ac-ed13-4fe8-bac2-e2a1cb295ab3/aiassistant/openai",
        "suggested_prompts": [
            "Which policies are underpriced relative to expected loss?",
            "Why is policy POL4020 underpriced?",
            "List drivers with high severity accidents who were underpriced the following year",
        ],
    },
    "pricing_ontology": {
        "name": "Pricing Agent (FabricIQ)",
        "endpoint": "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/cf55aeb3-4c5c-4b09-9d56-bb32c997e083/aiassistant/openai",
        "suggested_prompts": [
            "Which scored policy periods have the highest risk score?",
            "Show me underpriced policies and their reason codes.",
            "What is the average premium change for high-risk drivers?",
        ],
    },
    "underwriting": {
        "name": "Underwriting Copilot",
        "endpoint": "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/underwriting-copilot",
        "suggested_prompts": [
            "Explain this premium increase in plain English.",
            "Which driving behaviors contributed most?",
            "Compare this driver to similar drivers.",
        ],
    },
    "agent_advisor": {
        "name": "Agent Copilot",
        "endpoint": "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/agent-copilot",
        "suggested_prompts": [
            "How do I explain this increase to the customer?",
            "What can the customer do to lower their premium?",
            "Was night driving a major factor?",
        ],
    },
    "portfolio": {
        "name": "Portfolio Risk Copilot",
        "endpoint": "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/portfolio-copilot",
        "suggested_prompts": [
            "Are high-risk drivers improving after premium changes?",
            "Which segments benefit most from UBI?",
            "Where are we still losing money?",
        ],
    },
    "executive": {
        "name": "Executive Copilot",
        "endpoint": "https://<YOUR_FABRIC_WORKSPACE>.fabric.microsoft.com/dataagent/executive-copilot",
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
