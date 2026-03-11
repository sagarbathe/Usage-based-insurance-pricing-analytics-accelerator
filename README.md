# 🛡️ UBI Insurance Intelligence App

> **Usage-Based Insurance (UBI) Pricing Solution** — a role-based Streamlit
> application combining UBI pricing, portfolio risk analytics, and AI
> explainability powered by **Microsoft Fabric** Gold tables, **Power BI**
> embedded reports, and **Fabric Data Agents**.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Solution Overview](#solution-overview)
3. [App UI](#app-ui)
4. [Persona Pages](#persona-pages)
5. [Gold Tables](#gold-tables)
6. [Ontology Definition](#ontology-definition)
7. [Prerequisites](#prerequisites)
8. [Pre-Work: Setting Up the Fabric Environment](#pre-work-setting-up-the-fabric-environment)
9. [Application Setup](#application-setup)
10. [Configuration](#configuration)
11. [Running the Application](#running-the-application)
12. [Project Structure](#project-structure)
13. [Notebooks Reference](#notebooks-reference)
14. [Troubleshooting](#troubleshooting)

---

## Architecture

<img width="896" height="477" alt="image" src="https://github.com/user-attachments/assets/182f8c63-f239-4f01-8e3d-9bded7c6e0c0" />

---

## Solution Overview

This solution demonstrates an **end-to-end Usage-Based Insurance (UBI)
pricing pipeline** built on Microsoft Fabric:

1. **Data Ingestion** — Auto-claims data (policyholders, vehicles, policies,
   accidents, adjusters, claims) is created and loaded into a Fabric
   **Lakehouse** via PySpark notebooks.
2. **Telemetry Generation** — Simulated driver telemetry data (trips, speed,
   braking, acceleration, cornering, safety scores) is generated and streamed
   into a Fabric **Eventhouse** for real-time analytics.
3. **Feature Engineering & Gold Layer** — PySpark notebooks transform raw
   data into seven Gold-layer Delta tables that power downstream analytics.
4. **Risk Scoring & Premium Computation** — A rules-based (or ML) model
   scores each policy's risk and produces recommended premiums with capping,
   smoothing, and reason-code explainability.
5. **BI & Analytics** — Power BI reports embedded in the Streamlit app
   provide interactive dashboards tailored to five insurance personas.
6. **AI Copilots** — Fabric Data Agents (backed by the OpenAI Assistants
   API) let each persona ask natural-language questions against the Gold
   tables.
   - Fabric Data Agent built on Lakehouse and KQL tables
   - Fabric Data Agent built on FabricIQ Ontology

---

## App UI

The Streamlit application provides an integrated experience with three
interactive views per persona:

| View | Description |
|------|-------------|
| **📊 Power BI Dashboard** | Embedded Power BI report with interactive visuals tailored to the persona |
| **💬 Data Agent on Lakehouse & KQL** | Natural-language Q&A powered by a Fabric Data Agent querying Lakehouse Gold tables and Eventhouse KQL tables |
| **🧠 Data Agent on Fabric Ontology** | Natural-language Q&A powered by a Fabric Data Agent backed by a Fabric Ontology for semantic reasoning |

## UI Screenshot

![alt text](image.png)


> **Note:** This version currently implements the **Pricing / Actuarial**
> persona only. Additional personas (Underwriting, Agent/Advisor, Portfolio
> Manager, Executive/Strategy) will be added in future releases.

---

## Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Microsoft Fabric                         │
│                                                              │
│  Lakehouse ──▶ Notebooks ──▶ Gold Delta Tables               │
│                                    │                         │
│  Eventhouse (KQL) ─────────────────┤                         │
│                                    │                         │
│         ┌──────────────────────────┼──────────────┐          │
│         │                          │              │          │
│         ▼                          ▼              ▼          │
│   Fabric Ontology            Semantic Model    Lakehouse/    │
│   (FabricIQ)                                   Eventhouse    │
│         │                          │              │          │
│         ▼                          ▼              ▼          │
│   Data Agent on              Power BI       Data Agent on   │
│   FabricIQ Ontology          Reports        Lakehouse &     │
│                                              Eventhouse      │
│         │                          │              │          │
│         └──────────────┬───────────┴──────────────┘          │
│                        ▼                                     │
│                 Streamlit App                                 │
│                 (this repo)                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Persona Pages

The app is designed for five role-based views. Each page pairs an **embedded
Power BI report** with **Fabric Data Agent** chat panels. Users can switch
between the Power BI dashboard, a Data Agent on the Lakehouse/KQL semantic
model, or a Data Agent on the Fabric Ontology.

> **Current release:** Only the **Pricing / Actuarial** persona is fully
> implemented. The remaining personas are scaffolded and will be completed
> in upcoming releases.

| Persona | Page | Key Question | Status |
|---------|------|-------------|--------|
| 📐 **Pricing / Actuarial** | `pages/pricing.py` | Are we pricing risk correctly? | ✅ Available |
| ⚖️ **Underwriting** | `pages/underwriting.py` | Why did this premium change, and is it defensible? | 🔜 Coming soon |
| 🧑‍💼 **Agent / Advisor** | `pages/agent_advisor.py` | Help me explain this premium to the customer. | 🔜 Coming soon |
| 📊 **Portfolio Manager** | `pages/portfolio.py` | Is UBI improving the book of business? | 🔜 Coming soon |
| 🧠 **Executive / Strategy** | `pages/executive.py` | Is UBI worth the investment? | 🔜 Coming soon |

---

## Gold Tables

The following Gold-layer Delta tables are created by the Fabric notebooks
and consumed by the Power BI reports and Data Agents:

| Table | Grain | Purpose |
|-------|-------|---------|
| `gold_trip_features` | 1 row per trip | Canonical trip-level features: speed, braking, acceleration, safety score, risk level |
| `gold_driver_monthly_features` | 1 row per driver per month | Monthly rollups of driving behavior for trend analysis |
| `gold_policy_period_features` | 1 row per policy period | Pricing-ready feature snapshots aggregated across a policy term |
| `gold_policy_period_loss` | 1 row per policy period | Actual claims count and payout per policy period |
| `gold_expected_loss_scores` | 1 row per policy | Risk score and expected loss cost per policy |
| `gold_policy_premium_recommendation` | 1 row per policy | Current vs recommended premium, change %, caps, smoothing |
| `gold_premium_reason_codes` | N rows per policy | Top factors explaining each premium recommendation |

---

## Ontology Definition

This repository includes a pre-built **Fabric Ontology** definition in the
`ontology/` folder (`ont_UBI_definition.json`). The ontology defines entity
types (Policyholder, Policy, Vehicle, Claim, Accident, Adjuster, etc.),
their properties, data bindings to the Lakehouse Gold tables, and
relationships between entities. Importing this ontology into your Fabric
workspace enables rich semantic modelling and data agent capabilities.

### Importing the Ontology

To import the ontology definition into your Microsoft Fabric workspace, use
the **FabricIQ Export/Import Package** tool:

👉 **[FabricIQ Export/Import Package](https://github.com/sagarbathe/FabricIQ-export_import_package)**

Follow the instructions in that repository to:

1. Clone or download the [FabricIQ-export_import_package](https://github.com/sagarbathe/FabricIQ-export_import_package) repo.
2. Use the **import** workflow to upload `ontology/ont_UBI_definition.json`
   from this repository into your target Fabric workspace.
3. The tool will create the ontology item in your workspace with all entity
   types, property mappings, data bindings, and relationships pre-configured.

> **Note:** After importing, update the data binding workspace and lakehouse
> IDs in the ontology to point to your own Fabric Lakehouse if they differ
> from the exported values.

---

## Prerequisites

Before setting up the solution, ensure you have:

### Azure & Fabric
- An **Azure subscription** with permissions to create resources
- A **Microsoft Fabric workspace** with an active **Fabric capacity**
  (F2 or higher recommended; trial capacity works for evaluation)
- **Fabric workspace identity** enabled (Settings → Workspace identity)
- **Azure CLI** installed ([install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))

### Power BI
- Power BI reports published to a workspace accessible by the Fabric
  workspace identity (or your Azure CLI identity)
- Admin setting enabled: *"Service principals can use Power BI APIs"*

### Local Development
- **Python 3.10+**
- **Azure CLI** authenticated (`az login`)
- **Git** installed

---

## Pre-Work: Setting Up the Fabric Environment

Complete these steps in your Microsoft Fabric workspace **before** running
the Streamlit app.

### Step 1 — Create a Lakehouse

1. In the Fabric portal, navigate to your workspace.
2. Create a new **Lakehouse** (e.g., `lh_AutoClaims`).
3. Upload the source CSV files for the claims domain into the lakehouse
   `Files/AutoClaims_csv/` folder:
   - `policyholder.csv`
   - `vehicle.csv`
   - `policy.csv`
   - `adjuster.csv`
   - `accident.csv`
   - `claim.csv`

### Step 2 — Create Base Tables

Open and run **`data/create auto claim tables.ipynb`** in a Fabric
notebook environment. This notebook:
- Drops and recreates the base relational tables (`Policyholder`,
  `Vehicle`, `Policy`, `Adjuster`, `Accident`, `Claim`) in the
  lakehouse.

### Step 3 — Load Data into Tables

Open and run **`data/load auto claim tables.ipynb`**. This notebook:
- Reads each CSV from `Files/AutoClaims_csv/`
- Loads data into the corresponding lakehouse tables using schema
  inference from the existing table structures.

### Step 4 — Generate Driver Telemetry Data

Open and run **`data/create driver telemetry data for eventhouse.ipynb`**.
This notebook:
- Reads policy data to determine active drivers and date ranges.
- Simulates realistic trip-level telemetry (speed, braking, acceleration,
  cornering, safety scores) for each driver.
- Writes telemetry data to a Fabric **Eventhouse** (configure your
  Eventhouse connection details in the notebook).
- Also creates a `driver_telemetry_data` table in the lakehouse for
  downstream Spark processing.

### Step 5 — Build Gold Tables

Open and run **`data/nb_create_gold_tables.ipynb`**. This notebook:
- Creates the seven Gold-layer Delta table schemas listed in the
  [Gold Tables](#gold-tables) section.
- Tables are created as empty Delta tables ready for population.

### Step 6 — Score Policies & Compute Premiums

Open and run **`data/nb_score_policies_compute_premium.ipynb`**. This
notebook:
- Reads raw tables (`driver_telemetry_data`, `policy`, `vehicle`,
  `claim`, `accident`).
- Computes `gold_trip_features`, `gold_driver_monthly_features`,
  `gold_policy_period_features`, `gold_policy_period_loss`,
  `gold_expected_loss_scores`, `gold_policy_premium_recommendation`,
  and `gold_premium_reason_codes`.
- Applies a rules-based risk model (`rules_v1`) with configurable
  parameters: target loss ratio (65%), expense load (15%), profit load
  (5%), max change cap (±15%), and smoothing (α = 0.3).

### Step 7 — Publish Power BI Reports

Pre-built Power BI report files are included in the **`reports/`** folder:

| File | Persona |
|------|--------|
| `Pricing Adequacy Dashboard.pbix` | Pricing / Actuarial |

To publish them to your Fabric workspace:

1. Open each `.pbix` file in **Power BI Desktop**.
2. Update the data source connection to point to your Fabric Lakehouse
   Gold tables (Home → Transform data → Data source settings).
3. Click **Publish** → select your Fabric workspace.
4. After publishing, open the report in the Power BI service and note
   the **Report ID** (from the URL: `reportId=<GUID>`) and the
   **Workspace ID** / Group ID (from `groupId=<GUID>` or workspace
   settings).
5. Enter these values in `config.py` under `POWERBI_REPORTS` for the
   corresponding persona.

> **Tip:** If you build additional reports for other personas
> (Underwriting, Agent/Advisor, Portfolio, Executive), save the `.pbix`
> files into the `reports/` folder and follow the same publish workflow.

### Step 8 — Create Fabric Data Agents

1. In the Fabric workspace, create **Data Agents** under Data Science.
2. Configure each agent to query the Gold lakehouse tables.
3. Copy the agent endpoint URLs for use in `config.py`.

---

## Application Setup

```bash
# Clone the repository
git clone https://github.com/sagarbathe/UBIPricing_solution.git
cd UBIPricing_solution

# Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Authenticate with Azure (required for Power BI embedding & Data Agents)
az login
```

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥ 1.30.0 | Web application framework |
| `azure-identity` | ≥ 1.15.0 | Azure AD authentication (CLI + Managed Identity) |
| `openai` | ≥ 1.70.0 | Fabric Data Agent communication (Assistants API) |

---

## Configuration

Edit **`config.py`** to wire the app to your environment:

### Power BI Reports

For each persona, fill in `report_id` and `group_id`:

```python
POWERBI_REPORTS = {
    "pricing": {
        "report_id": "<YOUR_REPORT_GUID>",
        "group_id": "<YOUR_WORKSPACE_GUID>",
        ...
    },
    ...
}
```

### Fabric Data Agents

Replace placeholder endpoints with your actual Data Agent URLs:

```python
DATA_AGENTS = {
    "pricing": {
        "endpoint": "https://api.fabric.microsoft.com/v1/workspaces/<WORKSPACE_ID>/dataagents/<AGENT_ID>/aiassistant/openai",
        ...
    },
    ...
}
```

### Authentication

- **Local development:** Run `az login` — the app uses
  `AzureCliCredential` automatically.
- **Fabric deployment:** Enable Workspace Identity — the app uses
  `ManagedIdentityCredential` automatically.
- No API keys or client secrets are needed.

---

## Running the Application

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Select a persona from the
sidebar to view the corresponding Power BI report and Data Agent.

---

## Project Structure

```
├── app.py                     # Main Streamlit entry point & persona router
├── config.py                  # Power BI reports, Data Agent endpoints, persona definitions
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── components/                # Reusable UI components
│   ├── powerbi_auth.py        # Azure AD token acquisition for Power BI embedding
│   ├── powerbi_embed.py       # Power BI JS SDK embed renderer
│   ├── data_agent_chat.py     # Fabric Data Agent chat panel (OpenAI Assistants API)
│   └── kpi_tables.py          # KPI cards and data table components
│
├── pages/                     # Persona page modules
│   ├── pricing.py             # Pricing / Actuarial
│   ├── underwriting.py        # Underwriting
│   ├── agent_advisor.py       # Agent / Advisor
│   ├── portfolio.py           # Portfolio Manager
│   └── executive.py           # Executive / Strategy
│
├── reports/                   # Power BI report files (.pbix)
│   └── Pricing Adequacy Dashboard.pbix   # Pricing / Actuarial report
│
├── ontology/                  # Fabric Ontology definition
│   └── ont_UBI_definition.json   # UBI domain ontology (entity types, bindings, relationships)
│
└── data/                      # Fabric notebooks & Gold table schemas
    ├── csv/                                                # Source CSV data files
    │   ├── accident.csv
    │   ├── adjuster.csv
    │   ├── claim.csv
    │   ├── policy.csv
    │   ├── policyholder.csv
    │   └── vehicle.csv
    ├── create auto claim tables.ipynb                      # Step 2: Create base tables
    ├── load auto claim tables.ipynb                        # Step 3: Load CSV → tables
    ├── create driver telemetry data for eventhouse.ipynb    # Step 4: Simulate telemetry
    └── gold/
        ├── README.txt                                      # Gold table export format guide
        ├── nb_create_gold_tables.ipynb                     # Step 5: Create Gold schemas
        ├── nb_create_scored_policy_period.ipynb             # Create scored policy period table
        └── nb_score_policies_compute_premium.ipynb          # Step 6: Score & compute premiums
```

---

## Notebooks Reference

| # | Notebook | Run In | Purpose |
|---|----------|--------|---------|
| 1 | `create auto claim tables.ipynb` | Fabric Spark | Creates base relational tables (Policyholder, Vehicle, Policy, Adjuster, Accident, Claim) |
| 2 | `load auto claim tables.ipynb` | Fabric Spark | Loads CSV data into the base tables |
| 3 | `create driver telemetry data for eventhouse.ipynb` | Fabric Spark | Generates simulated driver telemetry and streams to Eventhouse |
| 4 | `gold/nb_create_gold_tables.ipynb` | Fabric Spark | Creates Gold-layer Delta table schemas |
| 5 | `gold/nb_create_scored_policy_period.ipynb` | Fabric Spark | Creates scored policy period table |
| 6 | `gold/nb_score_policies_compute_premium.ipynb` | Fabric Spark | Feature engineering, risk scoring, premium computation, reason codes |

> **Important:** All notebooks must be run **in a Fabric Spark environment**
> attached to your lakehouse. They use PySpark and `%%sql` magic commands.
> Run them in sequence (1 → 6).

---

## Troubleshooting

| Issue | Solution |
|-------|---------|
| Power BI report shows sign-in prompt | Ensure `report_id` and `group_id` are correct in `config.py`. Enable Workspace Identity or run `az login`. |
| Data Agent returns authentication error | Run `az login` locally, or enable Workspace Identity in Fabric. |
| Data Agent placeholder message appears | Replace the `<YOUR_...>` endpoint in `config.py` with your actual Data Agent URL. |
| Notebooks fail with table-not-found | Run notebooks in order (1 → 6). Ensure the lakehouse is attached to the notebook. |
| Missing CSV files error | Upload the source CSVs to `Files/AutoClaims_csv/` in your lakehouse before running `load auto claim tables.ipynb`. |
| Streamlit import errors | Ensure all dependencies are installed: `pip install -r requirements.txt` |

---

## License

This project is provided as a reference solution for Usage-Based Insurance
pricing on Microsoft Fabric. See the repository for license details.
