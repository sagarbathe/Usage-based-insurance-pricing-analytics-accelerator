# test-dataagent-endpoint.ps1 - Test if the Data Agent endpoint is accessible

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$DataAgentId = "50a54dc0-3f9f-44b2-84f6-8e54999bffa8"

Write-Host "Testing Fabric Data Agent endpoint..." -ForegroundColor Cyan
Write-Host "Workspace: $WorkspaceId" -ForegroundColor Gray
Write-Host "Data Agent: $DataAgentId" -ForegroundColor Gray
Write-Host ""

# Get access token
$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv

if (-not $Token) {
    Write-Host "Failed to get access token. Run 'az login' first." -ForegroundColor Red
    exit 1
}

$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test 1: Check if the Data Agent item exists
Write-Host "Test 1: Checking if Data Agent exists..." -ForegroundColor Yellow
$ItemUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/items/$DataAgentId"
try {
    $Item = Invoke-RestMethod -Uri $ItemUrl -Headers $Headers -Method Get
    Write-Host "✓ Data Agent found: $($Item.displayName)" -ForegroundColor Green
    Write-Host "  Type: $($Item.type)" -ForegroundColor Gray
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Data Agent not found (HTTP $StatusCode)" -ForegroundColor Red
    if ($StatusCode -eq 404) {
        Write-Host "  The Data Agent ID may be incorrect or it doesn't exist in this workspace." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Test 2: Try the assistants endpoint
Write-Host "`nTest 2: Testing assistants endpoint..." -ForegroundColor Yellow
$AssistantsUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId/aiassistant/openai/assistants"
try {
    $Assistants = Invoke-RestMethod -Uri $AssistantsUrl -Headers $Headers -Method Get
    Write-Host "✓ Assistants endpoint accessible" -ForegroundColor Green
    if ($Assistants.data) {
        Write-Host "  Found $($Assistants.data.Count) assistant(s)" -ForegroundColor Gray
        $Assistants.data | ForEach-Object {
            Write-Host "    - ID: $($_.id), Name: $($_.name)" -ForegroundColor Gray
        }
    }
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    $ErrorMessage = $_.Exception.Message
    Write-Host "✗ Assistants endpoint failed (HTTP $StatusCode)" -ForegroundColor Red
    Write-Host "  URL: $AssistantsUrl" -ForegroundColor Gray
    Write-Host "  Error: $ErrorMessage" -ForegroundColor Yellow
    
    if ($StatusCode -eq 404) {
        Write-Host "`n  Possible reasons:" -ForegroundColor Yellow
        Write-Host "  1. The Data Agent ID is incorrect" -ForegroundColor Gray
        Write-Host "  2. The Data Agent endpoint URL format has changed" -ForegroundColor Gray
        Write-Host "  3. Data Agents may not be available yet in your tenant" -ForegroundColor Gray
    } elseif ($StatusCode -eq 403) {
        Write-Host "`n  Permission issue - your account may need:" -ForegroundColor Yellow
        Write-Host "  1. Be a member/contributor of the workspace" -ForegroundColor Gray
        Write-Host "  2. Have the 'DataAgent.Contributor' or similar role" -ForegroundColor Gray
    }
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "Next steps if tests failed:" -ForegroundColor Cyan
Write-Host "1. Run .\verify-dataagent.ps1 to list all Data Agents in the workspace" -ForegroundColor Gray
Write-Host "2. Update deployment-config.ps1 with the correct Data Agent ID" -ForegroundColor Gray
Write-Host "3. Redeploy: .\deploy-containerapp.ps1" -ForegroundColor Gray
