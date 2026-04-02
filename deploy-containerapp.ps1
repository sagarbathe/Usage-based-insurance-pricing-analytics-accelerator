# deploy-containerapp.ps1 — Deploy Streamlit app to Azure Container Apps
# More reliable than App Service for Python applications

$ErrorActionPreference = "Stop"

# Load configuration from shared config file
. "$PSScriptRoot\deployment-config.ps1"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Azure Container Apps Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Azure ML Model Deployment Status
Write-Host "`n==> Checking Azure ML Model Configuration..." -ForegroundColor Cyan

$mlConfigured = $false
if ($AzureMLEndpointUrl -and $AzureMLEndpointKey -and $AzureMLEndpointUrl -ne "" -and $AzureMLEndpointKey -ne "") {
    Write-Host "    ✓ Azure ML endpoint is configured" -ForegroundColor Green
    Write-Host "      Endpoint: $($AzureMLEndpointUrl.Substring(0, [Math]::Min(50, $AzureMLEndpointUrl.Length)))..." -ForegroundColor Gray
    Write-Host "      Model: $AzureMLModelName v$AzureMLModelVersion" -ForegroundColor Gray
    $mlConfigured = $true
} else {
    Write-Host "    ⚠️  Azure ML endpoint is NOT configured" -ForegroundColor Yellow
    Write-Host "      The notebook scoring will not work without an ML model endpoint" -ForegroundColor Yellow
}

Write-Host ""
$deployML = Read-Host "Do you want to (re)deploy the Azure ML model? (y/N)"

if ($deployML -eq 'y' -or $deployML -eq 'Y') {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "Azure ML Model Deployment Required" -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "To deploy/redeploy the ML model:" -ForegroundColor Yellow
    Write-Host "  1. Open Azure ML Studio: https://ml.azure.com" -ForegroundColor White
    Write-Host "  2. Navigate to workspace: $AzureMLWorkspaceName" -ForegroundColor White
    Write-Host "  3. Open/upload notebook: data/gold/azureml_train_deploy_model.ipynb" -ForegroundColor White
    Write-Host "  4. Run all cells (Steps 1-10)" -ForegroundColor White
    Write-Host "  5. Copy Endpoint URL and API Key from Step 10 output" -ForegroundColor White
    Write-Host "  6. Update deployment-config.ps1:" -ForegroundColor White
    Write-Host "       `$AzureMLEndpointUrl = 'https://your-endpoint-url/score'" -ForegroundColor Gray
    Write-Host "       `$AzureMLEndpointKey = 'your-primary-key'" -ForegroundColor Gray
    Write-Host "  7. Re-run this script: .\deploy-containerapp.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 0
} else {
    if (-not $mlConfigured) {
        Write-Host "    ⚠️  Continuing without ML model deployment" -ForegroundColor Yellow
        Write-Host "       Notebook scoring features will not work until model is deployed" -ForegroundColor Yellow
    } else {
        Write-Host "    ✓ Using existing ML model configuration" -ForegroundColor Green
    }
    Write-Host ""
}

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

# Step 6: Check if Container App exists
Write-Host "==> Checking if Container App exists..." -ForegroundColor Yellow
$AppExists = az containerapp show --name $ContainerAppName --resource-group $ResourceGroup 2>$null
$DeploymentType = if ($AppExists) { "update" } else { "create" }

if ($DeploymentType -eq "update") {
    Write-Host "==> Updating existing Container App (preserves managed identity)..." -ForegroundColor Yellow
    az containerapp update `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --image "${AcrLoginServer}/${ImageName}:${ImageTag}" `
        --cpu 1.0 `
        --memory 2.0Gi `
        --min-replicas 1 `
        --max-replicas 3 `
        --set-env-vars `
            "FABRIC_WORKSPACE_ID=$FabricWorkspaceId" `
            "AZURE_TENANT_ID=$AzureTenantId" `
            "POWERBI_PRICING_REPORT_ID=$PowerBiPricingReportId" `
            "POWERBI_PRICING_EXPLORE_REPORT_ID=$PowerBiPricingExploreReportId" `
            "POWERBI_PRICING_GROUP_ID=$PowerBiPricingGroupId" `
            "FABRIC_PRICING_AGENT_ENDPOINT=$FabricPricingAgentEndpoint" `
            "FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT=$FabricOntologyAgentEndpoint" `
            "AZURE_ML_SUBSCRIPTION_ID=$AzureMLSubscriptionId" `
            "AZURE_ML_RESOURCE_GROUP=$AzureMLResourceGroup" `
            "AZURE_ML_WORKSPACE_NAME=$AzureMLWorkspaceName" `
            "AZURE_ML_ENDPOINT_NAME=$AzureMLEndpointName" `
            "AZURE_ML_ENDPOINT_URL=$AzureMLEndpointUrl" `
            "AZURE_ML_ENDPOINT_KEY=$AzureMLEndpointKey" `
            "AZURE_ML_DEPLOYMENT_NAME=$AzureMLDeploymentName" `
            "AZURE_ML_MODEL_NAME=$AzureMLModelName" `
            "AZURE_ML_MODEL_VERSION=$AzureMLModelVersion" `
        --output none
    
    if ($LASTEXITCODE -ne 0) { throw "Failed to update Container App" }
    Write-Host "==> Container App updated successfully (managed identity preserved)" -ForegroundColor Green
} else {
    Write-Host "==> Creating new Container App with managed identity..." -ForegroundColor Yellow
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
        --system-assigned `
        --env-vars `
            "FABRIC_WORKSPACE_ID=$FabricWorkspaceId" `
            "AZURE_TENANT_ID=$AzureTenantId" `
            "POWERBI_PRICING_REPORT_ID=$PowerBiPricingReportId" `
            "POWERBI_PRICING_EXPLORE_REPORT_ID=$PowerBiPricingExploreReportId" `
            "POWERBI_PRICING_GROUP_ID=$PowerBiPricingGroupId" `
            "FABRIC_PRICING_AGENT_ENDPOINT=$FabricPricingAgentEndpoint" `
            "FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT=$FabricOntologyAgentEndpoint" `
            "AZURE_ML_SUBSCRIPTION_ID=$AzureMLSubscriptionId" `
            "AZURE_ML_RESOURCE_GROUP=$AzureMLResourceGroup" `
            "AZURE_ML_WORKSPACE_NAME=$AzureMLWorkspaceName" `
            "AZURE_ML_ENDPOINT_NAME=$AzureMLEndpointName" `
            "AZURE_ML_ENDPOINT_URL=$AzureMLEndpointUrl" `
            "AZURE_ML_ENDPOINT_KEY=$AzureMLEndpointKey" `
            "AZURE_ML_DEPLOYMENT_NAME=$AzureMLDeploymentName" `
            "AZURE_ML_MODEL_NAME=$AzureMLModelName" `
            "AZURE_ML_MODEL_VERSION=$AzureMLModelVersion" `
        --output none
    
    if ($LASTEXITCODE -ne 0) { throw "Failed to create Container App" }
    Write-Host "==> Container App created with managed identity" -ForegroundColor Green
}

# Step 7: Restart the latest revision to ensure clean start with new configuration
Write-Host "==> Restarting the latest revision..." -ForegroundColor Yellow
$LatestRevision = az containerapp revision list `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "[0].name" `
    -o tsv
if ($LASTEXITCODE -eq 0 -and $LatestRevision) {
    az containerapp revision restart `
        --name $ContainerAppName `
        --resource-group $ResourceGroup `
        --revision $LatestRevision `
        --output none
    if ($LASTEXITCODE -eq 0) {
        Write-Host "==> Latest revision restarted successfully" -ForegroundColor Green
    } else {
        Write-Host "Warning: Restart command failed, but deployment may still be successful" -ForegroundColor Yellow
    }
} else {
    Write-Host "Warning: Could not determine latest revision, skipping restart" -ForegroundColor Yellow
}

# Get the app URL
$AppUrl = az containerapp show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "properties.configuration.ingress.fqdn" `
    -o tsv

# Get the Managed Identity Principal ID
$ManagedIdentityPrincipalId = az containerapp identity show `
    --name $ContainerAppName `
    --resource-group $ResourceGroup `
    --query "principalId" `
    -o tsv

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nApp URL: https://$AppUrl" -ForegroundColor Cyan
Write-Host "`nManaged Identity Principal ID: $ManagedIdentityPrincipalId" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
if ($DeploymentType -eq "create") {
    Write-Host "1. Grant the Managed Identity (ID above) access to Power BI workspace as Member" -ForegroundColor Yellow
    Write-Host "2. Add the Managed Identity to security group 'grp_spFabricAPIaccess'" -ForegroundColor Yellow
    Write-Host "3. Wait 10-15 minutes for permissions to propagate" -ForegroundColor Yellow
    Write-Host "4. Test the application at the URL above" -ForegroundColor Yellow
} else {
    Write-Host "1. Managed Identity preserved - no access changes needed" -ForegroundColor Yellow
    Write-Host "2. Test the application at the URL above" -ForegroundColor Yellow
}
Write-Host "`n"
