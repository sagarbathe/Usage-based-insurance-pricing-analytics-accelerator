# 🛡️ Usage-based Pricing Intelligence App

**Usage-Based Insurance (UBI) Pricing** is an innovation in auto insurance where premiums are adjusted based on a driver’s actual behavior (e.g., speeding, hard braking, mileage, time of day). The Fabric accelerator in the referenced repository demonstrates an end-to-end UBI Pricing solution built on Microsoft Fabric. Its primary goal is to help insurers answer: “Are we pricing risk correctly, and will we hit our target loss ratios?”.

The solution that unifies telematics (driving behavior) and insurance data to calculate driver risk scores and recommend usage-based premiums. It uses Fabric Lakehouse, Spark notebooks (ingestion, transformation, and feature-engineering), curated gold datasets with a semantic model, Power BI dashboards for actuaries/underwriters, and a built-in Copilot (Fabric Data Agent) for Q&A. The accelerator helps insurers ensure premiums align with actual risk by enabling interactive analytics and AI-driven insights on unified data.

---

## 📊 Repository Analytics

This repository tracks its own statistics automatically:
- **Repository stats:** Views, clones, stars, forks → [stats/SUMMARY.md](stats/SUMMARY.md)
- **Multi-repo analytics:** Track ALL your GitHub repositories → **[capturerepostats](https://github.com/sagarbathe/capturerepostats)**

Stats are collected daily via GitHub Actions and generate automated reports.

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

**Step 1: Data Ingestion**

Telematics (driver behavior) data and insurance data (policy, vehicle, customer, claims) are ingested into OneLake. All tables except Telematics are stored in a lakehouse, Telematics data is stored in a KQL table. A notebook simulates telematics data and calculates per-trip and per-driver metrics such as speeding incidents per 100 miles, harsh braking count, night driving percentage, safety scores while csv files are provided for the lakehouse tables

**Step 2: Feature Engineering & Risk Scoring**

Feature engineering is done in Fabric’s integrated Spark Notebooks, however in real insurance scenarios, this would be achieved by ML models., etc. The telematics metrics are aggregated from trip → driver → policy period. The notebooks then generate a driver risk score  for each policy 
using these features, and combine it with historical claims and accident records to estimate expected future losses. This is essentially the ML/AI step – a predictive model can be trained to compute an expected loss cost or score for each policy period. The result is a set of risk indicators
 and recommended premium adjustments for each policy (e.g. flagging underpriced policies where the model suggests a higher premium is warranted).

**Step 3: Curated Gold Data & Semantic Model**

The refined outputs (risk scores, recommended premiums, reason codes, etc.) are stored back in the Lakehouse as curated Gold tables. These tables represent the business-friendly data (e.g., policy-level risk scores, recommended premium vs actual premium, loss ratios) ready for analysis. A Power BI Semantic Model is then built on top of the Gold layer. This model (a dataset) defines the relationships between entities (driver → policy → claims) and exposes metrics like actual loss ratio (claims/premium), expected loss cost, recommended premium, and flags for underpriced or high-risk policies

**Step 4: Fabric Ontology**

A Fabric Ontology is developed to provide a unified representation of UBI (Usage-Based Insurance) domain concepts, real-world relationships, business context, and calculations. This standardized model enables consistent analytics and supports natural language querying across the 
organization.

The sample ontology provided can be imported via an export/import accelerator I built (sagarbathe/FabricIQ-export_import_package)

**Step 5: Analytics & Insights Consumption**

Finally, the accelerator delivers insights through Power BI reports and Copilot experiences (Fabric Data Agent). It includes pre-built Power BI dashboards for different insurance personas. Currently, a Pricing Adequacy Dashboard for actuarial teams highlights the gap between expected 
loss vs. premiums and identifies policies with potential underpricing (where expected loss exceeds current premium). 
Fabric Data Agents built on both (the semantic model and Fabric Ontology) are provided enabling users to ask questions in natural language and get answers backed by the data and measures in the semantic model (for instance, “Which policies are underpriced relative to expected 
loss?” or “Explain this premium increase in plain English.”). This conversational AI layer adds AI explainability on top of the analytics, helping users explore “why” behind the numbers.


---

## App UI

The Streamlit application provides an integrated experience with four
interactive views per persona:

| View | Description |
|------|-------------|
| **📊 Power BI Dashboard** | Embedded Power BI report with interactive visuals tailored to the persona. Personalize Visuals is enabled so users can tweak existing visuals inline. |
| **🔍 Explore / Ad-hoc** | A blank Power BI report embedded in **edit mode** against the same semantic model. Users can drag fields, create their own visuals, and perform ad-hoc analysis without modifying the published dashboard. |
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
- Power BI reports published to a workspace accessible by the
  App Service Managed Identity
- Admin setting enabled: *"Service principals can use Power BI APIs"*

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

#### Prerequisites for this step

Before running the notebook, ensure the following are in place:

1. **Steps 1–3 completed** — The Lakehouse exists and the base tables
   (including `policy`) are populated with data. The notebook reads
   `policy.csv` from `Files/AutoClaims_csv/` to determine active
   drivers and policy date ranges.
2. **Fabric Eventhouse created** — Create an **Eventhouse** in your
   Fabric workspace (e.g., `ev_driver_telemetry`) with a **database**
   of the same name.
3. **Eventhouse table created** — In the Eventhouse Query Editor, run
   the `.create-merge table` KQL command (printed by the notebook) to
   create the `driver_telemetry_data` table with the required schema.
4. **Eventhouse connection URIs** — Obtain the **Query URI** and
   **Ingest URI** for your Eventhouse. Update the following variables
   in the notebook's configuration cell:
   - `EVENTHOUSE_WORKSPACE` — your Fabric workspace name
   - `EVENTHOUSE_NAME` — your Eventhouse name
   - `EVENTHOUSE_DATABASE` — your database name
   - `EVENTHOUSE_TABLE` — target table name (default:
     `driver_telemetry_data`)
   - `eventhouse_query_uri` — the Query URI
     (e.g., `https://<cluster>.z3.kusto.fabric.microsoft.com`)
   - `eventhouse_ingest_uri` — the Ingest URI
     (e.g., `https://ingest-<cluster>.z3.kusto.fabric.microsoft.com`)
5. **Permissions** — The workspace identity (or your user account) must
   have **Admin** or **Contributor** role on the Eventhouse to write
   data via the Kusto REST API.

**PS: This notebook can be run multiple times to add new driver telemetry data. The notebook is designed to add unique telemtry based on policy durations**

#### Running the notebook

Open and run **`data/create driver telemetry data for eventhouse.ipynb`**.
This notebook:
- Reads policy data to determine active drivers and date ranges.
- Simulates realistic trip-level telemetry (speed, braking, acceleration,
  cornering, safety scores) for each driver.
- Authenticates using `mssparkutils.credentials.getToken()` and streams
  batches to the Eventhouse via the Kusto REST API (MultiJSON format).
- Also creates a `driver_telemetry_data` Delta table in the Lakehouse
  for downstream Spark processing.
- Prevents duplicate/overlapping trips by checking existing trip
  timestamps before generating new ones. Safe to run multiple times.

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
5. Enter these values in `deploy.ps1` as `$PowerBiPricingReportId` and
   `$PowerBiPricingGroupId` (or set them as App Settings directly).

### Step 7b — Create a Blank Report for Ad-hoc Explore

The **Explore / Ad-hoc** view embeds a blank report in edit mode so users
can build their own visuals on the fly. This requires a separate report
linked to the same semantic model:

1. In the Power BI Service, open your workspace.
2. Find the **semantic model** used by the Pricing report.
3. Click **…** → **Create report**.
4. Immediately **save** it (without adding any visuals) — name it
   something like "UBI Pricing Explore".
5. Copy the **Report ID** from the URL and enter it in `deploy.ps1` as
   `$PowerBiPricingExploreReportId`.

> **Why a separate report?** DirectLake semantic models do not support
> the `type: "create"` Power BI JS SDK embed because the service
> principal cannot establish a new data source connection via SSO.
> Embedding an existing (blank) report in edit mode re-uses the report
> author's data connection and avoids this limitation.

> **Tip:** If you build additional reports for other personas
> (Underwriting, Agent/Advisor, Portfolio, Executive), save the `.pbix`
> files into the `reports/` folder and follow the same publish workflow.

### Step 8 — Import Fabric Ontology

Import the pre-built UBI ontology definition into your Fabric workspace.
See the [Ontology Definition](#ontology-definition) section for full
instructions. In summary:

1. Clone the [FabricIQ-export_import_package](https://github.com/sagarbathe/FabricIQ-export_import_package) repo.
2. Use the **import** workflow to upload `ontology/ont_UBI_definition.json`
   into your target Fabric workspace.
3. After importing, update the data binding workspace and lakehouse IDs
   to point to your own Fabric Lakehouse.

### Step 9 — Create Fabric Data Agents

You need to create **two** Fabric Data Agents in your workspace — one
backed by the **Semantic Model** (Lakehouse & KQL tables; created in Step 7) and one backed by the **Fabric Ontology** (created in Step 8).

> 📖 **Documentation:** For step-by-step guidance on creating data agents,
> refer to
> [How to create a Data Agent](https://learn.microsoft.com/en-us/fabric/data-science/how-to-create-data-agent).

#### Agent 1 — Data Agent on Semantic Model (Lakehouse & KQL)

1. In the Fabric portal, navigate to your workspace.
2. Select **+ New item** → **Data Agent** (under Data Science).
3. Give the agent a name (e.g., `da_UBI_SemanticModel`).
4. Under data sources, add the **Semantic Model** that exposes your
   Lakehouse Gold tables and Eventhouse KQL tables.
5. Optionally add custom instructions to guide the agent on table
   relationships and common query patterns.
6. After creation, copy the **agent endpoint URL** from the agent
   settings and set it as `$FabricPricingAgentEndpoint` in `deploy.ps1`.

#### Agent 2 — Data Agent on Fabric Ontology

1. In the Fabric portal, navigate to your workspace.
2. Select **+ New item** → **Data Agent** (under Data Science).
3. Give the agent a name (e.g., `da_UBI_Ontology`).
4. Under data sources, add the **Fabric Ontology** you imported in
   Step 8 (`ont_UBI_definition`).
5. This agent leverages the ontology's entity types, relationships,
   and semantic metadata for richer natural-language reasoning.
6. After creation, copy the **agent endpoint URL** from the agent
   settings and set it as `$FabricOntologyAgentEndpoint` in `deploy.ps1`.

---

## Application Setup

### Deploy to Azure App Service

The app runs on **Azure App Service (Linux, Python 3.11+)**.
Authentication uses a **system-assigned Managed Identity** — no API keys
or client secrets are needed.

#### Quick deploy (PowerShell)

1. Open `deploy.ps1` and fill in the configuration variables at the top.
2. Run:

```powershell
az login
.\deploy.ps1
```

The script creates a resource group, App Service Plan, Web App, enables
Managed Identity, sets all App Settings, and zip-deploys the code.

#### Manual deploy

1. **Create the App Service:**

   ```powershell
   az group create -n rg-ubi-pricing -l centralus
   az appservice plan create -n asp-ubi-pricing -g rg-ubi-pricing --sku B1 --is-linux
   az webapp create -n app-ubi-pricing -g rg-ubi-pricing -p asp-ubi-pricing --runtime "PYTHON:3.11"
   ```

2. **Enable Managed Identity:**

   ```powershell
   az webapp identity assign -n app-ubi-pricing -g rg-ubi-pricing
   ```

3. **Set Startup Command:**

   ```powershell
   az webapp config set -n app-ubi-pricing -g rg-ubi-pricing --startup-file "python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=true --browser.gatherUsageStats=false"
   ```

4. **Configure App Settings (environment variables):**

   ```powershell
   az webapp config appsettings set -n app-ubi-pricing -g rg-ubi-pricing --settings `
       WEBSITES_PORT=8000 `
       FABRIC_WORKSPACE_ID="<YOUR_WORKSPACE_ID>" `
       AZURE_TENANT_ID="<YOUR_TENANT_ID>" `
       POWERBI_PRICING_REPORT_ID="<YOUR_PRICING_REPORT_ID>" `
       POWERBI_PRICING_GROUP_ID="<YOUR_WORKSPACE_ID>" `
       FABRIC_PRICING_AGENT_ENDPOINT="<YOUR_PRICING_AGENT_URL>" `
       FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT="<YOUR_ONTOLOGY_AGENT_URL>"
   ```

5. **Deploy code:**

   ```powershell
   az webapp up -n app-ubi-pricing -g rg-ubi-pricing --runtime "PYTHON:3.11"
   ```

6. **Grant Managed Identity access:**
   - In the **Power BI Admin Portal**, add the App Service MI to a security
     group allowed to use Power BI APIs.
   - In the **Power BI workspace**, grant the MI at least *Member* access
     (required for DirectLake datasets).
   - The MI automatically gets a token for the Fabric Data Agent API.

#### Environment Variables (App Settings)

All sensitive values are read from environment variables at runtime.
Set them in the Azure Portal (Configuration → Application settings)
or via `az webapp config appsettings set`.

| Variable | Required | Description |
|----------|----------|-------------|
| `WEBSITES_PORT` | Yes | Must be `8000` |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | Yes | Must be `true` — triggers `pip install` via Oryx during deployment |
| `FABRIC_WORKSPACE_ID` | Yes | Your Fabric workspace GUID |
| `AZURE_TENANT_ID` | Yes | Your Azure AD tenant GUID |
| `POWERBI_PRICING_REPORT_ID` | Yes | Pricing report GUID |
| `POWERBI_PRICING_EXPLORE_REPORT_ID` | No | Blank report GUID for ad-hoc explore (see [Step 7b](#step-7b--create-a-blank-report-for-ad-hoc-explore)) |
| `POWERBI_PRICING_GROUP_ID` | No | Defaults to `FABRIC_WORKSPACE_ID` |
| `POWERBI_UNDERWRITING_REPORT_ID` | No | Underwriting report GUID |
| `POWERBI_AGENT_REPORT_ID` | No | Agent/Advisor report GUID |
| `POWERBI_PORTFOLIO_REPORT_ID` | No | Portfolio report GUID |
| `POWERBI_EXECUTIVE_REPORT_ID` | No | Executive report GUID |
| `FABRIC_PRICING_AGENT_ENDPOINT` | Yes | Full URL for the Pricing Data Agent |
| `FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT` | Yes | Full URL for the Ontology Data Agent |
| `FABRIC_UNDERWRITING_AGENT_ENDPOINT` | No | Underwriting agent URL |
| `FABRIC_AGENT_ADVISOR_ENDPOINT` | No | Agent/Advisor agent URL |
| `FABRIC_PORTFOLIO_AGENT_ENDPOINT` | No | Portfolio agent URL |
| `FABRIC_EXECUTIVE_AGENT_ENDPOINT` | No | Executive agent URL |

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥ 1.30.0 | Web application framework |
| `azure-identity` | ≥ 1.15.0 | Azure AD authentication (Managed Identity) |
| `openai` | ≥ 1.70.0 | Fabric Data Agent communication (Assistants API) |
| `plotly` | ≥ 5.18.0 | Interactive charts |
| `pandas` | ≥ 2.0.0 | Data manipulation |

---

## Configuration

All configuration is done via **App Settings** (environment variables)
on the Azure App Service. Set them in `deploy.ps1` before deploying,
or update them later in the Azure Portal (Configuration → Application
settings) / via `az webapp config appsettings set`.

### Power BI Reports

Set the report ID and group ID for each persona as App Settings:

```
POWERBI_PRICING_REPORT_ID=<GUID>
POWERBI_PRICING_GROUP_ID=<GUID>
```

### Fabric Data Agents

Set the full endpoint URL for each Data Agent as App Settings:

```
FABRIC_PRICING_AGENT_ENDPOINT=https://api.fabric.microsoft.com/v1/workspaces/<WS>/dataagents/<AGENT>/aiassistant/openai
FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT=https://api.fabric.microsoft.com/v1/workspaces/<WS>/dataagents/<AGENT>/aiassistant/openai
```

### Authentication

The app uses the **system-assigned Managed Identity** on the Azure App
Service. No API keys, client secrets, or manual login is required.

---

## Running the Application

After deploying (see [Deploy to Azure App Service](#deploy-to-azure-app-service)),
the app is available at `https://<APP_NAME>.azurewebsites.net`.
The inline startup command launches Streamlit on port 8000, which Azure
proxies to HTTPS on port 443.

---

## Project Structure

```
├── app.py                     # Main Streamlit entry point & persona router
├── config.py                  # Power BI reports, Data Agent endpoints, persona definitions
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── startup.sh                 # Azure App Service startup script
├── deploy.ps1                 # PowerShell deployment script
│
├── .streamlit/
│   └── config.toml            # Streamlit server configuration
│
├── components/                # Reusable UI components
│   ├── powerbi_auth.py        # Managed Identity token acquisition (view + edit embed tokens)
│   ├── powerbi_embed.py       # Power BI JS SDK embed renderer (dashboard view + edit-mode explore)
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
| Power BI report shows sign-in prompt | Ensure `report_id` and `group_id` are set correctly in App Settings. Verify the MI is enabled and has *Member* access on the workspace. |
| "DirectLake not supported with V1 embed token" | The app uses V2 multi-resource `GenerateToken` API. Ensure the code is up to date — V1 per-report tokens do not support DirectLake datasets. |
| Explore view: "Entra ID authentication failed" / data source credentials error | DirectLake requires the calling identity to resolve data connections. The Explore view uses a blank report in edit mode (not `type: "create"`) to avoid this. Ensure `POWERBI_PRICING_EXPLORE_REPORT_ID` is set and the MI has *Member* access. See [Step 7b](#step-7b--create-a-blank-report-for-ad-hoc-explore). |
| Data Agent returns authentication error | Enable Managed Identity on the App Service and grant it access to Fabric. |
| Data Agent placeholder message appears | Set the corresponding `FABRIC_*_AGENT_ENDPOINT` App Setting. |
| App Service shows "Application Error" | Check logs: `az webapp log tail -n app-ubi-pricing -g rg-ubi-pricing`. Common causes: missing `WEBSITES_PORT=8000` or `SCM_DO_BUILD_DURING_DEPLOYMENT=true` setting. |
| App Service returns 502 / timeout | Streamlit may still be starting. B1 SKU takes ~30-60s. Ensure `WEBSITES_PORT` is `8000` and the startup command is set correctly. |
| Managed Identity token fails on App Service | Ensure system-assigned MI is enabled (Identity blade). Grant the MI *Member* on the Power BI workspace. Enable "Service principals can use Power BI APIs" in the Power BI Admin Portal. |
| Notebooks fail with table-not-found | Run notebooks in order (1 → 6). Ensure the lakehouse is attached to the notebook. |
| Missing CSV files error | Upload the source CSVs to `Files/AutoClaims_csv/` in your lakehouse before running `load auto claim tables.ipynb`. |
| Streamlit import errors | Ensure all dependencies are installed: `pip install -r requirements.txt`. On Azure, set `SCM_DO_BUILD_DURING_DEPLOYMENT=true`. |

---

## License

This project is provided as a reference solution for Usage-Based Insurance
pricing on Microsoft Fabric. See the repository for license details.
