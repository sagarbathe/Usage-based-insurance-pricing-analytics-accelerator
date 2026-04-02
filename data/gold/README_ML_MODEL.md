# Azure ML Model Integration Guide

## Overview

This guide shows how to create, train, deploy, and use an Azure ML model for UBI risk prediction instead of the previous rules-based approach.

## Architecture

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
│    └─> nb_score_policies_compute_premium.ipynb (modified)  │
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

## Step-by-Step Execution

### Prerequisites

1. **Azure ML Workspace**: Already configured in deployment-config.ps1
   - Subscription: `04054f52-6b7b-47c7-b836-005253626f42`
   - Resource Group: `RG_ML`
   - Workspace: `sbazureml`

2. **Authentication**: Run in terminal
   ```powershell
   az login
   az account set --subscription 04054f52-6b7b-47c7-b836-005253626f42
   ```

3. **Gold Tables**: Ensure these tables exist in Fabric:
   - `gold_policy_period_features`
   - `gold_policy_period_loss`

### Step 1: Prepare Training Data in Fabric

**Run in Fabric**: Open [fabric_prep_training_data.ipynb](./fabric_prep_training_data.ipynb) in your Fabric workspace

This notebook:
- ✅ Loads historical policy data from gold tables
- ✅ Calculates baseline expected loss by coverage type
- ✅ Engineers 3 target variables (risk_factor, expected_loss_cost, risk_score)
- ✅ Saves to lakehouse table: `gold_ml_training_data`

**Output**: `gold_ml_training_data` table with 8 features + 3 targets

**Then export to parquet**:
```python
spark.table('gold_ml_training_data').coalesce(1).write.mode('overwrite').parquet('/lakehouse/default/Files/ml_data/training_data.parquet')
```

### Step 2: Train and Deploy Model in Azure ML

**Run in Azure ML Studio** (ml.azure.com): Upload and run [azureml_train_deploy_model.ipynb](./azureml_train_deploy_model.ipynb)

**Before running:**
1. Download `training_data.parquet` from Fabric lakehouse (Files → ml_data)
2. Upload to Azure ML Studio → Data → Upload file
3. Update `DATA_PATH` in the notebook

This notebook:
- ✅ Loads training data from uploaded parquet
- ✅ Trains MultiOutputRegressor(GradientBoostingRegressor)
- ✅ Registers model in Azure ML workspace
- ✅ Creates managed online endpoint: `ubi-risk-endpoint`
- ✅ Deploys model and tests endpoint
- ✅ Returns endpoint URI and key

**Output**: 
- Registered model (e.g., `azure_ml_ubi_model` v1)
- Endpoint URL and authentication key

### Step 3: Update Configuration

After successful deployment, update **[deployment-config.ps1](../../deployment-config.ps1)**:

```powershell
# Replace <your-ml-endpoint-name> with the actual endpoint name
$AzureMLEndpointName    = "ubi-risk-03271530"  # Use the name from Step 2
$AzureMLDeploymentName  = "blue"               # Or leave empty for default
```

### Step 4: Score Policies with ML Model

Open and run: **[nb_score_policies_compute_premium.ipynb](./nb_score_policies_compute_premium.ipynb)**

This notebook (already modified):
- ✅ Reads Azure ML config from environment variables
- ✅ Connects to Azure ML endpoint using DefaultAzureCredential
- ✅ Pulls policy features from gold tables
- ✅ Calls Azure ML endpoint for predictions
- ✅ Saves predictions to `gold_expected_loss_scores` table
- ✅ Calculates recommended premiums based on ML predictions

### Step 5: Deploy Streamlit App

Run the deployment script to push environment variables:

```powershell
.\deploy-containerapp.ps1
```

This will:
- Deploy the Streamlit app with all Azure ML configuration
- Grant managed identity access to invoke Azure ML endpoints
- Make predictions available through Fabric Data Agent chat

## Model Input Schema

The Azure ML model expects these features:

| Feature | Type | Description |
|---------|------|-------------|
| `speeding_per_100_miles` | float | Speeding incidents per 100 miles |
| `harsh_events_per_100_miles` | float | Harsh braking/acceleration/cornering per 100 miles |
| `night_miles_share` | float | Proportion of miles driven at night (0-1) |
| `avg_safety_score` | float | Average trip safety score (0-100) |
| `total_trips` | int | Total number of trips |
| `total_miles` | float | Total distance driven |
| `high_risk_trip_share` | float | Proportion of high-risk trips (0-1) |
| `baseline_elc` | float | Baseline expected loss cost for coverage type |

## Model Output Schema

The model returns:

| Output | Type | Description |
|--------|------|-------------|
| `risk_factor` | float | Multiplier for baseline (e.g., 1.5 = 50% higher risk) |
| `expected_loss_cost` | float | Predicted claim cost for this policy |
| `risk_score` | float | Normalized risk score (0-100, higher = riskier) |

## Troubleshooting

### Error: "AbfsRestOperationException: Bad Request" when saving files
- ✅ **Fixed**: Notebooks now use `/tmp` directory which doesn't sync to OneLake
- ✅ This is a Fabric-specific issue - `/tmp` avoids OneLake file system conflicts
- ✅ Model files are properly registered to Azure ML from `/tmp`

### Error: "Model not found"
- ✅ Run Step 1 (training notebook) to register the model
- ✅ Check model name in deployment-config.ps1 matches registered model

### Error: "Endpoint not found"
- ✅ Run Step 2 (deployment notebook) to create the endpoint
- ✅ Update deployment-config.ps1 with actual endpoint name

### Error: "Unauthorized" or "403 Forbidden"
- ✅ Run `az login` to authenticate
- ✅ Grant managed identity access to Azure ML workspace
- ✅ Ensure RBAC role: "AzureML Data Scientist" or "Contributor"

### Error: "Input schema mismatch"
- ✅ Verify all 8 input features are present in the request
- ✅ Check feature names match exactly (case-sensitive)
- ✅ Ensure numeric types (not strings)

## Configuration Reference

All configurations live in **[deployment-config.ps1](../../deployment-config.ps1)**:

```powershell
# Azure Machine Learning Configuration
$AzureMLSubscriptionId  = "04054f52-6b7b-47c7-b836-005253626f42"
$AzureMLResourceGroup   = "RG_ML"
$AzureMLWorkspaceName   = "sbazureml"
$AzureMLEndpointName    = "<your-ml-endpoint-name>"  # Update after Step 2
$AzureMLDeploymentName  = ""
$AzureMLModelName       = "azure_ml_ubi_model"
$AzureMLModelVersion    = "1.0"
```

## Next Steps

1. ✅ Complete Steps 1-2 to train and deploy the model
2. ✅ Update deployment-config.ps1 with endpoint name
3. ✅ Run scoring notebook to generate predictions
4. ✅ Redeploy app to use new ML-based scores

## Benefits of ML vs Rules-Based

| Aspect | Rules-Based (Old) | ML-Based (New) |
|--------|-------------------|----------------|
| **Accuracy** | Fixed formulas | Learns from actual loss data |
| **Adaptability** | Manual tuning | Automatic pattern detection |
| **Complexity** | Limited interactions | Captures non-linear relationships |
| **Maintenance** | Update formulas manually | Retrain with new data |
| **Explainability** | Transparent weights | SHAP values / feature importance |
