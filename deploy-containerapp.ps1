# deploy-containerapp.ps1 — Deploy Streamlit app to Azure Container Apps
# More reliable than App Service for Python applications

$ErrorActionPreference = "Stop"

# Configuration
$ResourceGroup = "rg-ubi-pricing"
$Location = "centralus"
$ContainerRegistry = "acrubipricingsagar"  # Must be globally unique, lowercase, no hyphens
$ContainerAppEnv = "env-ubi-pricing"
$ContainerAppName = "app-ubi-pricing"
$ImageName = "ubi-pricing-app"
$ImageTag = "latest"

# Fabric & Power BI config
$FabricWorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$AzureTenantId = "6d9c4b13-597a-4bd5-9af2-5987259103fd"
$PowerBiPricingReportId = "76cdd8e3-f32a-4de1-b167-74ef41440769"
$PowerBiPricingExploreReportId = "c663f8be-c2a6-4848-b771-5a7b37514ecd"
$PowerBiPricingGroupId = $FabricWorkspaceId
$FabricPricingAgentEndpoint = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/7a3c56ac-ed13-4fe8-bac2-e2a1cb295ab3/aiassistant/openai"
$FabricOntologyAgentEndpoint = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/cf55aeb3-4c5c-4b09-9d56-bb32c997e083/aiassistant/openai"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Azure Container Apps Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Create Resource Group
Write-Host "==> Creating resource group..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output none
if ($LASTEXITCODE -ne 0) { Write-Host "Resource group may already exist" -ForegroundColor Yellow }

# Step 2: Create Azure Container Registry
Write-Host "==> Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create `
    --name $ContainerRegistry `
    --resource-group $ResourceGroup `
    --sku Basic `
    --admin-enabled true `
    --output none
if ($LASTEXITCODE -ne 0) { Write-Host "ACR may already exist" -ForegroundColor Yellow }

# Step 3: Build and push Docker image to ACR
Write-Host "==> Building and pushing Docker image to ACR..." -ForegroundColor Yellow
Write-Host "    This may take 3-5 minutes..." -ForegroundColor Gray
az acr build `
    --registry $ContainerRegistry `
    --image "${ImageName}:${ImageTag}" `
    --file Dockerfile `
    .
if ($LASTEXITCODE -ne 0) { throw "Failed to build and push Docker image" }

# Step 4: Create Container Apps environment
Write-Host "==> Creating Container Apps environment..." -ForegroundColor Yellow
az containerapp env create `
    --name $ContainerAppEnv `
    --resource-group $ResourceGroup `
    --location $Location `
    --output none
if ($LASTEXITCODE -ne 0) { Write-Host "Container Apps environment may already exist" -ForegroundColor Yellow }

# Step 5: Get ACR credentials
Write-Host "==> Getting ACR credentials..." -ForegroundColor Yellow
$AcrUsername = az acr credential show --name $ContainerRegistry --query "username" -o tsv
$AcrPassword = az acr credential show --name $ContainerRegistry --query "passwords[0].value" -o tsv
$AcrLoginServer = az acr show --name $ContainerRegistry --query "loginServer" -o tsv

# Step 6: Deploy Container App
Write-Host "==> Deploying Container App..." -ForegroundColor Yellow
az containerapp create `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --environment $ContainerAppEnv `
    --image "${AcrLoginServer}/${ImageName}:${ImageTag}" `
    --registry-server $AcrLoginServer `
    --registry-username $AcrUsername `
    --registry-password $AcrPassword `
    --target-port 8000 `
    --ingress external `
    --min-replicas 1 `
    --max-replicas 3 `
    --cpu 1.0 `
    --memory 2.0Gi `
    --env-vars `
        "FABRIC_WORKSPACE_ID=$FabricWorkspaceId" `
        "AZURE_TENANT_ID=$AzureTenantId" `
        "POWERBI_PRICING_REPORT_ID=$PowerBiPricingReportId" `
        "POWERBI_PRICING_EXPLORE_REPORT_ID=$PowerBiPricingExploreReportId" `
        "POWERBI_PRICING_GROUP_ID=$PowerBiPricingGroupId" `
        "FABRIC_PRICING_AGENT_ENDPOINT=$FabricPricingAgentEndpoint" `
        "FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT=$FabricOntologyAgentEndpoint" `
    --output none

if ($LASTEXITCODE -ne 0) { throw "Failed to deploy Container App" }

# Step 7: Enable Managed Identity
Write-Host "==> Enabling Managed Identity..." -ForegroundColor Yellow
az containerapp identity assign `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --system-assigned `
    --output none
if ($LASTEXITCODE -ne 0) { Write-Host "WARNING: Failed to assign Managed Identity" -ForegroundColor Yellow }

# Get the app URL
$AppUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" `
    -o tsv

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nApp URL: https://$AppUrl" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Grant the Managed Identity access to Power BI & Fabric" -ForegroundColor Yellow
Write-Host "2. Test the application at the URL above" -ForegroundColor Yellow
Write-Host "`n"
