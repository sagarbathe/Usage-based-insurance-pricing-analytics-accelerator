# test-graphql-api.ps1 - Test Fabric GraphQL API for Data Agents

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$DataAgentId = "50a54dc0-3f9f-44b2-84f6-8e54999bffa8"

Write-Host "Testing Fabric GraphQL API for Data Agents..." -ForegroundColor Cyan
Write-Host ""

$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Try the v1 query endpoint
Write-Host "Test 1: POST to /v1/workspaces/{workspace}/dataagents/{id}/query..." -ForegroundColor Yellow
$QueryUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId/query"
$QueryBody = @{
    question = "List the top 3 underpriced policies"
} | ConvertTo-Json

try {
    Write-Host "URL: $QueryUrl" -ForegroundColor Gray
    $Response = Invoke-RestMethod -Uri $QueryUrl -Headers $Headers -Method Post -Body $QueryBody -TimeoutSec 45
    Write-Host "✓ Query endpoint works!" -ForegroundColor Green
    Write-Host "  Response:" -ForegroundColor Gray
    Write-Host ($Response | ConvertTo-Json -Depth 5 | Out-String).Substring(0, [Math]::Min(1000, ($Response | ConvertTo-Json -Depth 5).Length)) -ForegroundColor White
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Query endpoint failed ($StatusCode)" -ForegroundColor Red
    try {
        Write-Host "  Error: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow  
    }
}

# Try alternative endpoints
Write-Host "`nTest 2: POST to /invoke endpoint..." -ForegroundColor Yellow  
$InvokeUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId/invoke"
try {
    $Response2 = Invoke-RestMethod -Uri $InvokeUrl -Headers $Headers -Method Post -Body $QueryBody -TimeoutSec 45
    Write-Host "✓ Invoke endpoint works!" -ForegroundColor Green
    Write-Host ($Response2 | ConvertTo-Json -Depth 5) -ForegroundColor White
} catch {
    $StatusCode2 = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Invoke endpoint failed ($StatusCode2)" -ForegroundColor Red
}

Write-Host "`nTest 3: POST to /execute endpoint..." -ForegroundColor Yellow
$ExecuteUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId/execute"
try {
    $Response3 = Invoke-RestMethod -Uri $ExecuteUrl -Headers $Headers -Method Post -Body $QueryBody -TimeoutSec 45
    Write-Host "✓ Execute endpoint works!" -ForegroundColor Green
    Write-Host ($Response3 | ConvertTo-Json -Depth 5) -ForegroundColor White
} catch {
    $StatusCode3 = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Execute endpoint failed ($StatusCode3)" -ForegroundColor Red
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "If any simple endpoint works, we can use that instead of OpenAI Assistants API" -ForegroundColor Yellow
