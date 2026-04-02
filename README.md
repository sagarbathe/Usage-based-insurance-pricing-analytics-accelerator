# 🛡️ Usage-Based Insurance Pricing Analytics Accelerator

**Usage-Based Insurance (UBI) Pricing** is an innovation in auto insurance where premiums are adjusted based on a driver's actual behavior (e.g., speeding, hard braking, mileage, time of day). This accelerator demonstrates an end-to-end UBI pricing solution built on **Microsoft Fabric** and **Azure Machine Learning**. Its primary goal is to help insurers answer: "Are we pricing risk correctly, and will we hit our target loss ratios?".

This solution unifies telematics (driving behavior) and insurance data to calculate driver risk scores using **production-grade ML models** and recommend usage-based premiums. It leverages:
- **Microsoft Fabric**: Lakehouse, Spark notebooks, KQL Eventhouse for ingestion, transformation, and feature engineering
- **Azure Machine Learning**: Production ML model training, deployment, and managed online inference endpoints
- **Power BI**: Interactive dashboards with embedded analytics
- **Fabric Data Agent**: Natural language Q&A powered by Fabric Ontology and semantic models
- **Streamlit App**: Unified experience connecting all components

The accelerator helps insurers ensure premiums align with actual risk by enabling interactive analytics, ML-driven predictions, and AI-powered insights on unified data.

---

## 📊 Repository Analytics

This repository tracks its own statistics automatically:
- **Repository stats:** Views, clones, stars, forks → [stats/SUMMARY.md](stats/SUMMARY.md)
- **Multi-repo analytics:** Track ALL your GitHub repositories → **[capturerepostats](https://github.com/sagarbathe/capturerepostats)**

Stats are collected daily via GitHub Actions and generate automated reports.

---

## 🆕 What's New: Azure ML Integration

**This accelerator extends the Fabric-only approach with Azure Machine Learning:**

- ✅ **Production ML Models**: Replace rules-based scoring with trained ML models
- ✅ **Multi-Output Regression**: Predict risk_factor, expected_loss_cost, and risk_score simultaneously
- ✅ **Managed Online Endpoints**: Real-time inference with auto-scaling and monitoring
- ✅ **End-to-End MLOps**: Training data preparation → Model training → Model registration → Deployment → Inference
- ✅ **Seamless Integration**: Fabric notebooks call Azure ML endpoints via HTTP for predictions

📖 **[Azure ML Integration Guide](data/gold/README_ML_MODEL.md)** - Complete setup instructions

---

## Table of Contents

1. [Architecture](#architecture)
2. [Solution Overview](#solution-overview)
3. [Azure ML Workflow](#azure-ml-workflow)
4. [App UI](#app-ui)
5. [Persona Pages](#persona-pages)
6. [Gold Tables](#gold-tables)
7. [Ontology Definition](#ontology-definition)
8. [Prerequisites](#prerequisites)
9. [Pre-Work: Setting Up the Fabric Environment](#pre-work-setting-up-the-fabric-environment)
10. [Azure ML Setup](#azure-ml-setup)
11. [Application Setup](#application-setup)
12. [Configuration](#configuration)
13. [Running the Application](#running-the-application)
14. [Project Structure](#project-structure)
15. [Notebooks Reference](#notebooks-reference)
16. [Troubleshooting](#troubleshooting)

---

## Architecture

<img width="1323" height="499" alt="image" src="https://github.com/user-attachments/assets/6c86d158-016b-4ab3-9584-38a4dbf2d6c8" />


### Azure ML Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Fabric: Prepare Training Data                           │
│    └─> fabric_prep_training_data.ipynb                     │
│        - Reads gold tables (features + actual loss)         │
│        - Engineers target variables                         │
│        - Saves to gold_ml_training_data table               │
│        - Exports to parquet for Azure ML                    │
└─────────────────────────────────────────────────────────────┘
                            ↓ (download parquet)
┌─────────────────────────────────────────────────────────────┐
│ 2. Azure ML: Train, Register & Deploy                      │
│    └─> azureml_train_deploy_model.ipynb                    │
│        - Loads training data from uploaded parquet          │
│        - Trains multi-output regression model               │
│        - Registers model in Azure ML workspace              │
│        - Creates online endpoint & deploys                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ (endpoint URI + key)
┌─────────────────────────────────────────────────────────────┐
│ 3. Fabric: Score Policies                                  │
│    └─> nb_score_policies_compute_premium.ipynb (enhanced)  │
│        - Reads policy features from gold tables             │
│        - Calls Azure ML endpoint for predictions            │
│        - Saves scores to gold_expected_loss_scores          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Streamlit App                                            │
│    └─> app.py + Fabric Data Agent                          │
│        - Reads gold_expected_loss_scores table              │
│        - Powers dashboards and chat experiences             │
└─────────────────────────────────────────────────────────────┘
```

---

## Solution Overview

This solution demonstrates an **end-to-end Usage-Based Insurance (UBI) pricing pipeline** built on Microsoft Fabric and Azure ML:

**Step 1: Data Ingestion**

Telematics (driver behavior) data and insurance data (policy, vehicle, customer, claims) are ingested into OneLake. All tables except Telematics are stored in a lakehouse; Telematics data is stored in a KQL table. A notebook simulates telematics data and calculates per-trip and per-driver metrics such as speeding incidents per 100 miles, harsh braking count, night driving percentage, and safety scores, while CSV files are provided for the lakehouse tables.

**Step 2: Feature Engineering & ML Training** 🆕

Feature engineering is done in Fabric's integrated Spark Notebooks. The telematics metrics are aggregated from trip → driver → policy period. **Unlike rules-based approaches, this accelerator uses Azure ML to train production-grade machine learning models**. The notebook [fabric_prep_training_data.ipynb](data/gold/fabric_prep_training_data.ipynb) prepares training data with features and historical outcomes. Then [azureml_train_deploy_model.ipynb](data/gold/azureml_train_deploy_model.ipynb) trains a multi-output regression model to predict:
- `risk_factor`: Multiplier for baseline loss cost
- `expected_loss_cost`: Predicted claim cost
- `risk_score`: Normalized risk score (0-100)

The trained model is registered and deployed to an Azure ML managed online endpoint for real-time inference.

**Step 3: Risk Scoring via ML Endpoint** 🆕

The refined scoring process now uses the Azure ML endpoint instead of rules-based logic. The notebook [nb_score_policies_compute_premium.ipynb](data/gold/nb_score_policies_compute_premium.ipynb) reads policy features and calls the Azure ML endpoint via HTTP REST API to get predictions. Results are stored in the `gold_expected_loss_scores` table with model metadata (model name, version, scoring timestamp).

**Step 4: Curated Gold Data & Semantic Model**

The refined outputs (ML-based risk scores, recommended premiums, reason codes, etc.) are stored back in the Lakehouse as curated Gold tables. These tables represent the business-friendly data (e.g., policy-level risk scores, recommended premium vs actual premium, loss ratios) ready for analysis. A Power BI Semantic Model is then built on top of the Gold layer. This model (a dataset) defines the relationships between entities (driver → policy → claims) and exposes metrics like actual loss ratio (claims/premium), expected loss cost, recommended premium, and flags for underpriced or high-risk policies.

**Step 5: Fabric Ontology**

A Fabric Ontology is developed to provide a unified representation of UBI (Usage-Based Insurance) domain concepts, real-world relationships, business context, and calculations. This standardized model enables consistent analytics and supports natural language querying across the organization.

The sample ontology provided can be imported via an export/import accelerator: [FabricIQ-export_import_package](https://github.com/sagarbathe/FabricIQ-export_import_package)

**Step 6: Analytics & Insights Consumption**

Finally, the accelerator delivers insights through Power BI reports and Copilot experiences (Fabric Data Agent). It includes pre-built Power BI dashboards for different insurance personas. Currently, a Pricing Adequacy Dashboard for actuarial teams highlights the gap between expected loss vs. premiums and identifies policies with potential underpricing (where expected loss exceeds current premium). Fabric Data Agents built on both (the semantic model and Fabric Ontology) enable users to ask questions in natural language and get answers backed by the data and measures in the semantic model (for instance, "Which policies are underpriced relative to expected loss?" or "Explain this premium increase in plain English."). This conversational AI layer adds AI explainability on top of the analytics, helping users explore "why" behind the numbers.

---

## Azure ML Workflow

The Azure ML integration follows this workflow:

### 1. Prepare Training Data (Fabric)
**Notebook**: [fabric_prep_training_data.ipynb](data/gold/fabric_prep_training_data.ipynb)
- Load features from `gold_policy_period_features`
- Load actual outcomes from `gold_policy_period_loss`
- Engineer 3 target variables based on historical data
- Save to `gold_ml_training_data` table
- Export as parquet for Azure ML

### 2. Train & Deploy Model (Azure ML)
**Notebook**: [azureml_train_deploy_model.ipynb](data/gold/azureml_train_deploy_model.ipynb)
- Upload training parquet to Azure ML
- Train MultiOutputRegressor with GradientBoostingRegressor
- Register model in Azure ML workspace
- Create managed online endpoint (e.g., `ubi-risk-endpoint`)
- Deploy model with auto-scaling
- Test endpoint and capture URL/key

### 3. Score Policies (Fabric)
**Notebook**: [nb_score_policies_compute_premium.ipynb](data/gold/nb_score_policies_compute_premium.ipynb)
- Read policy features from gold tables
- Call Azure ML endpoint via HTTP POST
- Round predictions to 2 decimal places
- Save to `gold_expected_loss_scores` with model metadata

### 4. Calculate Premiums (Fabric)
- Load ML predictions from `gold_expected_loss_scores`
- Apply business rules (target loss ratio, expense load, profit load)
- Apply caps and smoothing
- Save to `gold_policy_premium_recommendation`

📖 **Detailed Guide**: [Azure ML Integration Guide](data/gold/README_ML_MODEL.md)

---

## App UI

The Streamlit application provides an integrated experience with four interactive views per persona:

| View | Description |
|------|-------------|
| **📊 Power BI Dashboard** | Embedded Power BI report with interactive visuals tailored to the persona. Personalize Visuals is enabled so users can tweak existing visuals inline. |
| **🔍 Explore / Ad-hoc** | A blank Power BI report embedded in **edit mode** against the same semantic model. Users can drag fields, create their own visuals, and perform ad-hoc analysis without modifying the published dashboard. |
| **💬 Data Agent on Lakehouse & KQL** | Natural-language Q&A powered by a Fabric Data Agent querying Lakehouse Gold tables and Eventhouse KQL tables |
| **🧠 Data Agent on Fabric Ontology** | Natural-language Q&A powered by a Fabric Data Agent backed by a Fabric Ontology for semantic reasoning |

## UI Screenshot

![alt text](image.png)

> **Note:** This version currently implements the **Pricing / Actuarial** persona only. Additional personas (Underwriting, Agent/Advisor, Portfolio Manager, Executive/Strategy) will be added in future releases.

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
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Azure Machine Learning                      │
│                                                              │
│  Training Data ──▶ Model Training ──▶ Model Registry         │
│                                           │                  │
│                                           ▼                  │
│                                    Managed Online            │
│                                      Endpoint                │
│                                           │                  │
│                                           ▼                  │
│                                  (Real-time Inference)       │
│                                           │                  │
└───────────────────────────────────────────┼─────────────────┘
                                            │
                                            ▼
                                    Fabric Notebooks
                                    (scoring policies)
```

---

## Persona Pages

The app is designed for five role-based views. Each page pairs an **embedded Power BI report** with **Fabric Data Agent** chat panels. Users can switch between the Power BI dashboard, a Data Agent on the Lakehouse/KQL semantic model, or a Data Agent on the Fabric Ontology.

> **Current release:** Only the **Pricing / Actuarial** persona is fully implemented. The remaining personas are scaffolded and will be completed in upcoming releases.

| Persona | Page | Key Question | Status |
|---------|------|-------------|--------|
| 📐 **Pricing / Actuarial** | `pages/pricing.py` | Are we pricing risk correctly? | ✅ Available |
| ⚖️ **Underwriting** | `pages/underwriting.py` | Why did this premium change, and is it defensible? | 🔜 Coming soon |
| 🧑‍💼 **Agent / Advisor** | `pages/agent_advisor.py` | Help me explain this premium to the customer. | 🔜 Coming soon |
| 📊 **Portfolio Manager** | `pages/portfolio.py` | Is UBI improving the book of business? | 🔜 Coming soon |
| 🧠 **Executive / Strategy** | `pages/executive.py` | Is UBI worth the investment? | 🔜 Coming soon |

---

## Gold Tables

The following Gold-layer Delta tables are created by the Fabric notebooks and consumed by the Power BI reports and Data Agents:

| Table | Grain | Purpose |
|-------|-------|---------|
| `gold_trip_features` | 1 row per trip | Canonical trip-level features: speed, braking, acceleration, safety score, risk level |
| `gold_driver_monthly_features` | 1 row per driver per month | Monthly rollups of driving behavior for trend analysis |
| `gold_policy_period_features` | 1 row per policy period | Pricing-ready feature snapshots aggregated across a policy term |
| `gold_policy_period_loss` | 1 row per policy period | Actual claims count and payout per policy period |
| **`gold_ml_training_data` 🆕** | **1 row per policy** | **ML training dataset with 8 features + 3 target variables** |
| `gold_expected_loss_scores` | 1 row per policy | **ML-predicted** risk score and expected loss cost per policy |
| `gold_policy_premium_recommendation` | 1 row per policy | Current vs recommended premium, change %, caps, smoothing |
| `gold_premium_reason_codes` | N rows per policy | Top factors explaining each premium recommendation |

---

## Ontology Definition

This repository includes a pre-built **Fabric Ontology** definition in the `ontology/` folder (`ont_UBI_definition.json`). The ontology defines entity types (Policyholder, Policy, Vehicle, Claim, Accident, Adjuster, etc.), their properties, data bindings to the Lakehouse Gold tables, and relationships between entities. Importing this ontology into your Fabric workspace enables rich semantic modelling and data agent capabilities.

### Importing the Ontology

To import the ontology definition into your Microsoft Fabric workspace, use the **FabricIQ Export/Import Package** tool:

👉 **[FabricIQ Export/Import Package](https://github.com/sagarbathe/FabricIQ-export_import_package)**

Follow the instructions in that repository to:

1. Clone or download the [FabricIQ-export_import_package](https://github.com/sagarbathe/FabricIQ-export_import_package) repo.
2. Use the **import** workflow to upload `ontology/ont_UBI_definition.json` from this repository into your target Fabric workspace.
3. The tool will create the ontology item in your workspace with all entity types, property mappings, data bindings, and relationships pre-configured.

> **Note:** After importing, update the data binding workspace and lakehouse IDs in the ontology to point to your own Fabric Lakehouse if they differ from the exported values.

---

## Prerequisites

Before setting up the solution, ensure you have:

### Azure & Fabric
- An **Azure subscription** with permissions to create resources
- A **Microsoft Fabric workspace** with an active **Fabric capacity** (F2 or higher recommended; trial capacity works for evaluation)
- **Fabric workspace identity** enabled (Settings → Workspace identity)
- **Azure CLI** installed ([install guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli))

### Azure Machine Learning 🆕
- **Azure ML workspace** created in your subscription
- **Permissions**: AzureML Data Scientist or Contributor role
- **Managed Identity**: Access granted to Azure ML workspace
- **Azure ML Studio** access for running training notebooks

### Power BI
- Power BI reports published to a workspace accessible by the Container App Managed Identity
- Admin setting enabled: *"Service principals can use Power BI APIs"*

---

## Pre-Work: Setting Up the Fabric Environment

Complete these steps in your Microsoft Fabric workspace **before** running the Streamlit app.

### Step 1 — Create a Lakehouse

1. In the Fabric portal, navigate to your workspace.
2. Create a new **Lakehouse** (e.g., `lh_AutoClaims`).
3. Upload the source CSV files for the claims domain into the lakehouse `Files/AutoClaims_csv/` folder:
   - `policyholder.csv`
   - `vehicle.csv`
   - `policy.csv`
   - `adjuster.csv`
   - `accident.csv`
   - `claim.csv`

### Step 2 — Create Base Tables

Open and run **`data/create auto claim tables.ipynb`** in a Fabric notebook environment. This notebook:
- Drops and recreates the base relational tables (`Policyholder`, `Vehicle`, `Policy`, `Adjuster`, `Accident`, `Claim`) in the lakehouse.

### Step 3 — Load Data into Tables

Open and run **`data/load auto claim tables.ipynb`**. This notebook:
- Reads each CSV from `Files/AutoClaims_csv/`
- Loads data into the corresponding lakehouse tables using schema validation.

### Step 4 — Create Eventhouse & KQL Table

1. Create a new **Eventhouse** in your Fabric workspace (e.g., `eh_AutoClaims`).
2. Open and run **`data/create driver telemetry data for eventhouse.ipynb`**. This notebook:
   - Generates synthetic telematics data (trip-level driving behavior)
   - Streams data to the Eventhouse KQL table `driver_telemetry_data`

### Step 5 — Create Gold Tables

Open and run **`data/gold/nb_create_gold_tables.ipynb`** in Fabric. This notebook:
- Joins telematics and policy data
- Calculates trip-level features (speeding, harsh events, safety scores)
- Aggregates to policy-period level
- Creates gold tables for analysis

### Step 6 — Score Policies with Azure ML

Open and run **`data/gold/nb_score_policies_compute_premium.ipynb`** in Fabric. This notebook:
- Performs feature engineering on policy-period data
- Calls the Azure ML real-time endpoint to get prediction metrics (risk_factor, expected_loss_cost, risk_score)
- Calculates recommended premiums based on ML predictions
- Applies business rules (target loss ratio, caps, smoothing)
- Saves results to `gold_expected_loss_scores` and `gold_policy_premium_recommendation` tables

> **Note:** This step requires the Azure ML endpoint to be deployed first (see Azure ML Setup section below).

### Step 7 — Create Materialized Views for Ontology

Open and run **`data/gold/nb_create_scored_policy_period.ipynb`** in Fabric. This notebook:
- Creates materialized views on which the Fabric Ontology is built
- Prepares data structures optimized for semantic querying
- Enables rich data agent experiences with proper entity relationships

---

## Azure ML Setup

Follow these steps to set up the Azure ML model:

### Step 1 — Prepare Training Data

**Run in Fabric**: [fabric_prep_training_data.ipynb](data/gold/fabric_prep_training_data.ipynb)
- Combines features and historical outcomes
- Engineers target variables
- Exports training data as parquet

### Step 2 — Train and Deploy Model

**Run in Azure ML Studio**: [azureml_train_deploy_model.ipynb](data/gold/azureml_train_deploy_model.ipynb)
- Upload training parquet from Fabric
- Train multi-output regression model
- Register model in Azure ML workspace
- Create managed online endpoint
- Deploy model and test
- **Copy endpoint URL and primary key** for configuration

### Step 3 — Update Configuration

Edit **[deployment-config.ps1](deployment-config.ps1)** and add your Azure ML endpoint details:

```powershell
# Azure Machine Learning Configuration
$AzureMLEndpointUrl = "https://your-endpoint.region.inference.ml.azure.com/score"
$AzureMLEndpointKey = "your-primary-key-here"
```

📖 **Detailed Instructions**: [Azure ML Integration Guide](data/gold/README_ML_MODEL.md)

---

## Application Setup

### Step 1 — Clone Repository

```bash
git clone https://github.com/sagarbathe/Usage-based-insurance-pricing-analytics-accelerator.git
cd Usage-based-insurance-pricing-analytics-accelerator
```

### Step 2 — Install Dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Step 3 — Configure Application

Edit **[deployment-config.ps1](deployment-config.ps1)** with your environment details:

```powershell
# Fabric Workspace Configuration
$FabricWorkspaceId = "your-workspace-id"
$FabricLakehouseId = "your-lakehouse-id"
$FabricEventhouseId = "your-eventhouse-id"

# Power BI Configuration
$PowerBIWorkspaceId = "your-powerbi-workspace-id"
$PowerBIReportId = "your-report-id"

# Azure ML Configuration (from Step 2 above)
$AzureMLEndpointUrl = "your-endpoint-url"
$AzureMLEndpointKey = "your-endpoint-key"
```

---

## Configuration

All configuration is managed through **[deployment-config.ps1](deployment-config.ps1)**. This file contains:

- **Fabric settings**: Workspace IDs, Lakehouse IDs, Eventhouse IDs
- **Power BI settings**: Workspace and report IDs
- **Azure ML settings**: Endpoint URL, key, model name/version
- **Container App settings**: Resource group, container registry, app name

The deployment script automatically reads this configuration and sets environment variables for the Streamlit app.

---

## Running the Application

### Local Development

```powershell
streamlit run app.py
```

### Deploy to Azure Container Apps

```powershell
# Login to Azure
az login
az account set --subscription "your-subscription-id"

# Deploy container app
.\deploy-containerapp.ps1
```

The deployment script will:
1. Check if Azure ML model should be deployed
2. Build and push Docker container
3. Create/update Azure Container App
4. Configure environment variables
5. Grant managed identity access to Fabric and Azure ML

---

## Project Structure

```
├── app.py                              # Main Streamlit application
├── config.py                           # Configuration loader
├── deployment-config.ps1              # Centralized configuration
├── deploy-containerapp.ps1            # Deployment automation
├── Dockerfile                         # Container definition
├── requirements.txt                   # Python dependencies
├── pages/
│   ├── pricing.py                    # Pricing persona page
│   └── [other personas]              # Coming soon
├── components/
│   ├── powerbi_embed.py              # Power BI embedding
│   ├── data_agent_chat.py            # Fabric Data Agent chat
│   └── kpi_tables.py                 # KPI widgets
├── data/
│   ├── create auto claim tables.ipynb
│   ├── load auto claim tables.ipynb
│   ├── create driver telemetry data for eventhouse.ipynb
│   └── gold/
│       ├── fabric_prep_training_data.ipynb  🆕
│       ├── azureml_train_deploy_model.ipynb 🆕
│       ├── nb_create_gold_tables.ipynb
│       ├── nb_score_policies_compute_premium.ipynb
│       └── README_ML_MODEL.md
├── ontology/
│   └── ont_UBI_definition.json       # Fabric Ontology definition
└── stats/
    └── SUMMARY.md                     # Repository analytics
```

---

## Notebooks Reference

| Notebook | Location | Purpose |
|----------|----------|---------|
| `create auto claim tables.ipynb` | `data/` | Create base lakehouse tables (Policy, Claim, Accident, etc.) |
| `load auto claim tables.ipynb` | `data/` | Load CSV data into lakehouse tables |
| `create driver telemetry data for eventhouse.ipynb` | `data/` | Generate and stream telematics data to KQL table |
| **`fabric_prep_training_data.ipynb` 🆕** | `data/gold/` | **Prepare ML training data in Fabric** |
| **`azureml_train_deploy_model.ipynb` 🆕** | `data/gold/` | **Train and deploy ML model in Azure ML** |
| `nb_create_gold_tables.ipynb` | `data/gold/` | Create gold-layer feature tables |
| `nb_score_policies_compute_premium.ipynb` | `data/gold/` | **Call Azure ML endpoint** and calculate premiums |

---

## Troubleshooting

### Azure ML Issues

#### Error: "Endpoint not found"
- ✅ Verify endpoint was created in Azure ML Studio
- ✅ Check endpoint name in deployment-config.ps1 matches deployed endpoint
- ✅ Ensure endpoint is in "Succeeded" state

#### Error: "Unauthorized" or "403 Forbidden"
- ✅ Run `az login` to authenticate
- ✅ Grant managed identity "AzureML Data Scientist" role on workspace
- ✅ Verify endpoint key is correct

#### Error: "Model input schema mismatch"
- ✅ Verify all 8 input features are present in request payload
- ✅ Check feature names match exactly (case-sensitive)
- ✅ Ensure all features are numeric (not strings)

### Fabric Issues

#### Error: "Table not found"
- ✅ Run gold table creation notebooks in sequence
- ✅ Verify lakehouse ID in configuration is correct

#### Error: "Data Agent returns empty results"
- ✅ Verify ontology is imported correctly
- ✅ Check data agent has access to lakehouse
- ✅ Ensure tables have data

### Power BI Issues

#### Error: "Report not found"
- ✅ Verify report is published to specified workspace
- ✅ Check Power BI workspace ID and report ID in config
- ✅ Grant managed identity access to Power BI workspace

📖 **More Troubleshooting**: [Azure ML Integration Guide - Troubleshooting Section](data/gold/README_ML_MODEL.md#troubleshooting)

---

## Related Resources

- **Original Fabric Accelerator**: [Usage-based-Pricing-Accelerator-Azure-apps](https://github.com/sagarbathe/Usage-based-Pricing-Accelerator-Azure-apps) (rules-based version)
- **Fabric Ontology Tool**: [FabricIQ-export_import_package](https://github.com/sagarbathe/FabricIQ-export_import_package)
- **Repository Analytics**: [capturerepostats](https://github.com/sagarbathe/capturerepostats)

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using Microsoft Fabric, Azure Machine Learning, Power BI, and Streamlit**
