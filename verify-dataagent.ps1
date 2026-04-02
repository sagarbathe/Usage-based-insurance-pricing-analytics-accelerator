# verify-dataagent.ps1 - Verify Fabric Data Agent exists and get correct ID

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"

Write-Host "Checking Fabric Data Agents in workspace..." -ForegroundColor Cyan

# Get an access token for Fabric API
$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv

if (-not $Token) {
    Write-Host "Failed to get access token. Make sure you're logged in with 'az login'" -ForegroundColor Red
    exit 1
}

# List all items in the workspace to find Data Agents
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$WorkspaceUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items"

try {
    $Response = Invoke-RestMethod -Uri $WorkspaceUrl -Headers $Headers -Method Get
    
    Write-Host "`nAll items in workspace:" -ForegroundColor Green
    $Response.value | ForEach-Object {
        Write-Host "  - $($_.displayName) (Type: $($_.type), ID: $($_.id))" -ForegroundColor Gray
    }
    
    # Filter for Data Agents (type might be 'DataAgent' or 'Dataagent')
    $DataAgents = $Response.value | Where-Object { $_.type -like "*agent*" }
    
    if ($DataAgents) {
        Write-Host "`nData Agents found:" -ForegroundColor Green
        $DataAgents | ForEach-Object {
            Write-Host "  - Name: $($_.displayName)" -ForegroundColor Yellow
            Write-Host "    ID: $($_.id)" -ForegroundColor Yellow
            Write-Host "    Type: $($_.type)" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "`nNo Data Agents found in this workspace." -ForegroundColor Yellow
        Write-Host "Available item types: $($Response.value.type | Select-Object -Unique)" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "`nError: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "If you don't see your Data Agent, you may need to:" -ForegroundColor Cyan
Write-Host "1. Verify the workspace ID is correct" -ForegroundColor Gray
Write-Host "2. Check that the Data Agent was created in this workspace" -ForegroundColor Gray
Write-Host "3. Ensure your account has permission to view the workspace" -ForegroundColor Gray
