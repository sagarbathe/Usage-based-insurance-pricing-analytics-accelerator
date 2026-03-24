# deploy.ps1 — Deploy the Streamlit app to Azure App Service.
#
# Prerequisites:
#   - Azure CLI installed and authenticated (az login)
#   - Subscription selected (az account set -s <SUB_ID>)
#
# Usage:
#   1. Fill in the configuration variables below
#   2. Run: .\deploy.ps1
#
# All Power BI and Fabric Data Agent values are set as App Settings
# automatically during deployment — no manual portal step needed.

$ErrorActionPreference = "Stop"

# ────────────────────────────────────────────────
# Azure infrastructure — edit these before running
# ────────────────────────────────────────────────
$ResourceGroup   = if ($env:RESOURCE_GROUP)      { $env:RESOURCE_GROUP }      else { "rg-ubi-pricing" }
$Location        = if ($env:LOCATION)            { $env:LOCATION }            else { "centralus" }
$AppServicePlan  = if ($env:APP_SERVICE_PLAN)    { $env:APP_SERVICE_PLAN }    else { "asp-ubi-pricing" }
$AppName         = if ($env:APP_NAME)            { $env:APP_NAME }            else { "app-ubi-pricing" }  # must be globally unique
$Sku             = if ($env:SKU)                 { $env:SKU }                 else { "B1" }               # B1, S1, P1v3, etc.
$PythonVersion   = if ($env:PYTHON_VERSION)      { $env:PYTHON_VERSION }      else { "3.11" }

# ────────────────────────────────────────────────
# Fabric & Power BI config — fill in your values
# ────────────────────────────────────────────────
$FabricWorkspaceId              = "db7dcf85-001e-4277-a85e-3c92029900bc"        # Fabric workspace GUID
$AzureTenantId                  = "6d9c4b13-597a-4bd5-9af2-5987259103fd"            # Azure AD tenant GUID

# Power BI report IDs (set the ones you have; leave others as-is)
$PowerBiPricingReportId         = "76cdd8e3-f32a-4de1-b167-74ef41440769"          # Pricing report GUID
$PowerBiPricingExploreReportId  = "c663f8be-c2a6-4848-b771-5a7b37514ecd"                                              # Blank report GUID for ad-hoc explore (create one on the same semantic model)
$PowerBiPricingGroupId          = $FabricWorkspaceId                  # usually same as workspace
$PowerBiUnderwritingReportId    = ""                                  # optional
$PowerBiAgentReportId           = ""                                  # optional
$PowerBiPortfolioReportId       = ""                                  # optional
$PowerBiExecutiveReportId       = ""                                  # optional

# Fabric Data Agent endpoints (full URLs)
$FabricPricingAgentEndpoint     = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/50a54dc0-3f9f-44b2-84f6-8e54999bffa8/aiassistant/openai"     # e.g. https://api.fabric.microsoft.com/v1/workspaces/.../aiassistant/openai
$FabricOntologyAgentEndpoint    = "https://api.fabric.microsoft.com/v1/workspaces/db7dcf85-001e-4277-a85e-3c92029900bc/dataagents/cf55aeb3-4c5c-4b09-9d56-bb32c997e083/aiassistant/openai"    # e.g. https://api.fabric.microsoft.com/v1/workspaces/.../aiassistant/openai
$FabricUnderwritingEndpoint     = ""                                  # optional
$FabricAgentAdvisorEndpoint     = ""                                  # optional
$FabricPortfolioEndpoint        = ""                                  # optional
$FabricExecutiveEndpoint        = ""                                  # optional

Write-Host "==> Creating resource group: $ResourceGroup"
az group create `
    --name $ResourceGroup `
    --location $Location `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to create resource group" }

Write-Host "==> Creating App Service Plan: $AppServicePlan ($Sku)"
az appservice plan create `
    --name $AppServicePlan `
    --resource-group $ResourceGroup `
    --sku $Sku `
    --is-linux `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to create App Service Plan" }

Write-Host "==> Creating Web App: $AppName"
az webapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --plan $AppServicePlan `
    --runtime "PYTHON:$PythonVersion" `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to create Web App" }

Write-Host "==> Enabling system-assigned Managed Identity"
az webapp identity assign `
    --name $AppName `
    --resource-group $ResourceGroup `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to assign Managed Identity" }

Write-Host "==> Setting startup command"
az webapp config set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --startup-file "python -m streamlit run app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=true --browser.gatherUsageStats=false" `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to set startup command" }

Write-Host "==> Configuring App Settings (ports + Fabric/Power BI values)"
# Build the settings list — always include WEBSITES_PORT and core IDs
$settings = @(
    "WEBSITES_PORT=8000",
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true",
    "FABRIC_WORKSPACE_ID=$FabricWorkspaceId",
    "AZURE_TENANT_ID=$AzureTenantId",
    "POWERBI_PRICING_REPORT_ID=$PowerBiPricingReportId",
    "POWERBI_PRICING_EXPLORE_REPORT_ID=$PowerBiPricingExploreReportId",
    "POWERBI_PRICING_GROUP_ID=$PowerBiPricingGroupId",
    "FABRIC_PRICING_AGENT_ENDPOINT=$FabricPricingAgentEndpoint",
    "FABRIC_PRICING_ONTOLOGY_AGENT_ENDPOINT=$FabricOntologyAgentEndpoint"
)
# Add optional settings only if a value was provided
if ($PowerBiUnderwritingReportId)    { $settings += "POWERBI_UNDERWRITING_REPORT_ID=$PowerBiUnderwritingReportId" }
if ($PowerBiAgentReportId)           { $settings += "POWERBI_AGENT_REPORT_ID=$PowerBiAgentReportId" }
if ($PowerBiPortfolioReportId)       { $settings += "POWERBI_PORTFOLIO_REPORT_ID=$PowerBiPortfolioReportId" }
if ($PowerBiExecutiveReportId)       { $settings += "POWERBI_EXECUTIVE_REPORT_ID=$PowerBiExecutiveReportId" }
if ($FabricUnderwritingEndpoint)     { $settings += "FABRIC_UNDERWRITING_AGENT_ENDPOINT=$FabricUnderwritingEndpoint" }
if ($FabricAgentAdvisorEndpoint)     { $settings += "FABRIC_AGENT_ADVISOR_ENDPOINT=$FabricAgentAdvisorEndpoint" }
if ($FabricPortfolioEndpoint)        { $settings += "FABRIC_PORTFOLIO_AGENT_ENDPOINT=$FabricPortfolioEndpoint" }
if ($FabricExecutiveEndpoint)        { $settings += "FABRIC_EXECUTIVE_AGENT_ENDPOINT=$FabricExecutiveEndpoint" }

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings @settings `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to set app settings" }

Write-Host "==> Deploying application code (zip deploy)"
# Create a temporary zip excluding unnecessary files
$TmpZip = Join-Path $env:TEMP "ubi-deploy-$(Get-Random).zip"

# Build list of files to include (exclude dev/data artifacts)
$ExcludePatterns = @(".git", ".venv", "venv", "__pycache__", ".env", ".vscode", ".idea", "data\csv", "reports", "deploy.ps1", "deploy.sh")
$FilesToZip = Get-ChildItem -Path . -Recurse -File | Where-Object {
    $relativePath = $_.FullName.Substring((Get-Location).Path.Length + 1)
    $exclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($relativePath -like "$pattern*" -or $relativePath -like "*\$pattern\*" -or $relativePath -like "*\$pattern") {
            $exclude = $true
            break
        }
    }
    if ($_.Extension -eq ".pyc" -or $_.Extension -eq ".ipynb") { $exclude = $true }
    -not $exclude
}

# Stage files into a temp directory preserving folder structure, then zip
$StagingDir = Join-Path $env:TEMP "ubi-staging-$(Get-Random)"
$BaseDir = (Get-Location).Path
foreach ($file in $FilesToZip) {
    $relativePath = $file.FullName.Substring($BaseDir.Length + 1)
    $destPath = Join-Path $StagingDir $relativePath
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null }
    Copy-Item $file.FullName -Destination $destPath
}
Compress-Archive -Path "$StagingDir\*" -DestinationPath $TmpZip -Force
Remove-Item -Path $StagingDir -Recurse -Force

az webapp deploy `
    --name $AppName `
    --resource-group $ResourceGroup `
    --src-path $TmpZip `
    --type zip `
    --output none
if ($LASTEXITCODE -ne 0) { throw "Failed to deploy application" }

Remove-Item -Path $TmpZip -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=============================================="
Write-Host "  Deployment complete!"
Write-Host "  URL: https://$AppName.azurewebsites.net"
Write-Host "=============================================="
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Grant the Managed Identity access to Power BI & Fabric."
Write-Host "     - Azure Portal > App Service > Identity > copy Object ID"
Write-Host "     - Power BI Admin Portal > enable 'Service principals can use Power BI APIs'"
Write-Host "     - Power BI Workspace > add the identity as Viewer"
Write-Host ""
Write-Host "  2. To update settings later:"
Write-Host "     az webapp config appsettings set -n $AppName -g $ResourceGroup --settings KEY=VALUE"
Write-Host ""
Write-Host "     See README.md for the full environment variable list."
