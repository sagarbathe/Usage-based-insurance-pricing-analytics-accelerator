# test-chat-completions.ps1 - Test if Data Agent supports chat completions API

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$DataAgentId = "50a54dc0-3f9f-44b2-84f6-8e54999bffa8"
$BaseUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId/aiassistant/openai"

Write-Host "Testing simplified chat API..." -ForegroundColor Cyan
Write-Host ""

$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

# Test: Direct chat without threads/runs
Write-Host "Test: POST to /chat/completions (no threads)..." -ForegroundColor Yellow
$ChatUrl = "$BaseUrl/chat/completions?api-version=2024-05-01-preview"
$ChatBody = @{
    messages = @(
        @{
            role = "user"
            content = "List the top 3 underpriced policies"
        }
    )
} | ConvertTo-Json -Depth 5

try {
    Write-Host "URL: $ChatUrl" -ForegroundColor Gray
    $Response = Invoke-RestMethod -Uri $ChatUrl -Headers $Headers -Method Post -Body $ChatBody -TimeoutSec 30
    Write-Host "✓ Chat completions works!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($Response | ConvertTo-Json -Depth 5) -ForegroundColor White
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Failed with status: $StatusCode" -ForegroundColor Red
    try {
        $ErrorBody = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "Error details:" -ForegroundColor Yellow
        Write-Host ($ErrorBody | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    } catch {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "If chat/completions works, we should switch to that simpler API" -ForegroundColor Yellow
Write-Host "instead of the complex threads/messages/runs pattern" -ForegroundColor Yellow
