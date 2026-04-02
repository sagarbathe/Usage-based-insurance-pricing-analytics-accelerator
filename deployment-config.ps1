# deployment-config.ps1 — Single source of configuration for all deployment scripts
#
# This file is dot-sourced by deploy.ps1 and deploy-containerapp.ps1
# Edit values here once, and both scripts will use the updated configuration.

# ────────────────────────────────────────────────
# Azure Infrastructure Configuration
# ────────────────────────────────────────────────
$ResourceGroup   = "rg-ubi-pricing"
$Location        = "centralus"
$AppServicePlan  = "asp-ubi-pricing"       # Used by App Service deployment
$AppName         = "app-ubi-pricing"       # Must be globally unique
$Sku             = "B1"                    # App Service SKU (B1, S1, P1v3, etc.)
$PythonVersion   = "3.11"

# Container Apps specific (used by deploy-containerapp.ps1)
$ContainerRegistry = "acrubipricingsagar"  # Must be globally unique, lowercase, no hyphens
$ContainerAppEnv   = "env-ubi-pricing"
$ContainerAppName  = "app-ubi-pricing"
$ImageName         = "ubi-pricing-app"
$ImageTag          = "latest"

# ────────────────────────────────────────────────
# Fabric & Power BI Configuration
# ────────────────────────────────────────────────
$FabricWorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$AzureTenantId     = "6d9c4b13-597a-4bd5-9af2-5987259103fd"

# Power BI Report IDs
$PowerBiPricingReportId         = "76cdd8e3-f32a-4de1-b167-74ef41440769"
$PowerBiPricingExploreReportId  = "c663f8be-c2a6-4848-b771-5a7b37514ecd"
$PowerBiPricingGroupId          = $FabricWorkspaceId
$PowerBiUnderwritingReportId    = ""
$PowerBiAgentReportId           = ""
$PowerBiPortfolioReportId       = ""
$PowerBiExecutiveReportId       = ""

# Fabric Data Agent Endpoints (full URLs ending in /openai)
$FabricPricingAgentEndpoint    = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/50a54dc0-3f9f-44b2-84f6-8e54999bffa8/aiassistant/openai"
$FabricOntologyAgentEndpoint   = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/cf55aeb3-4c5c-4b09-9d56-bb32c997e083/aiassistant/openai"
$FabricUnderwritingEndpoint    = ""
$FabricAgentAdvisorEndpoint    = ""
$FabricPortfolioEndpoint       = ""
$FabricExecutiveEndpoint       = ""

# ────────────────────────────────────────────────
# Azure Machine Learning Configuration
# ────────────────────────────────────────────────
# Used by notebooks for ML-based risk scoring and premium calculation
# Get the Endpoint URL and API Key from Step 10 output of azureml_train_deploy_model.ipynb

$AzureMLSubscriptionId  = "04054f52-6b7b-47c7-b836-005253626f42"  # Azure subscription containing the ML workspace
$AzureMLResourceGroup   = "RG_ML"                                  # Resource group with ML workspace
$AzureMLWorkspaceName   = "sbazureml"                              # Azure ML workspace name
$AzureMLModelName       = "azure_ml_ubi_model"                     # Model name for tracking and logging
$AzureMLModelVersion    = "8"                                      # Model version (update after retraining)
$AzureMLEndpointName    = "ubi-risk-endpoint"                      # Online endpoint name for UBI risk model

# ⚠️ IMPORTANT: Update these values after deploying the model
# Run azureml_train_deploy_model.ipynb in Azure ML Studio (all cells, Steps 1-10)
# Copy the Endpoint URL and Primary Key from Step 10 output and paste below:
$AzureMLEndpointUrl     = "https://ubi-risk-endpoint.eastus2.inference.ml.azure.com/score"  # Example: "https://ubi-risk-endpoint.eastus2.inference.ml.azure.com/score"
$AzureMLEndpointKey     = "C73Ffb4NEWGBhfzJW2zywiqABonA0ceO2rlZYrR9ZnfRO7v50V4GJQQJ99CCAAAAAAAAAAAAINFRAZML3kWc"  # Example: "AbC123...XYZ789" (Primary key from endpoint authentication)

# Optional: specific deployment name (leave empty for default/blue deployment)
$AzureMLDeploymentName  = ""
