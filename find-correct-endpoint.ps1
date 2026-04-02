# find-correct-endpoint.ps1 - Try to discover the correct Data Agent endpoint

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$DataAgentId = "50a54dc0-3f9f-44b2-84f6-8e54999bffa8"

Write-Host "Discovering correct Data Agent endpoint..." -ForegroundColor Cyan
Write-Host ""

$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
}

$BaseUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId"

# Try different endpoint variations
$EndpointsToTry = @(
    "/chat/completions",
    "/completions",
    "/threads",
    "/sessions",
    "/query",
    "/ask",
    "/assistant",
    "/aiassistant",
    "/aiassistant/chat/completions",
    "/v1/chat/completions"
)

Write-Host "Testing endpoint variations..." -ForegroundColor Yellow
foreach ($Endpoint in $EndpointsToTry) {
    $TestUrl = "$BaseUrl$Endpoint"
    try {
        # Try GET first
        $Response = Invoke-WebRequest -Uri $TestUrl -Headers $Headers -Method Get -ErrorAction Stop
        Write-Host "✓ $Endpoint - GET works (HTTP $($Response.StatusCode))" -ForegroundColor Green
    } catch {
        $StatusCode = $_.Exception.Response.StatusCode.value__
        if ($StatusCode -eq 405) {
            Write-Host "⚠ $Endpoint - found but GET not allowed (try POST)" -ForegroundColor Yellow
        } elseif ($StatusCode -eq 401 -or $StatusCode -eq 403) {
            Write-Host "⚠ $Endpoint - found but permission denied" -ForegroundColor Yellow
        } elseif ($StatusCode -ne 404) {
            Write-Host "⚠ $Endpoint - found (HTTP $StatusCode)" -ForegroundColor Yellow
        } else {
            Write-Host "✗ $Endpoint - not found" -ForegroundColor Gray
        }
    }
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "Checking Fabric Data Agent API documentation..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Based on current Fabric API, Data Agents may use:" -ForegroundColor Yellow
Write-Host "1. Direct chat endpoint: /chat/completions" -ForegroundColor Gray
Write-Host "2. OpenAI-compatible: /v1/chat/completions" -ForegroundColor Gray
Write-Host "3. Session-based: /sessions" -ForegroundColor Gray
Write-Host ""
Write-Host "The application code may need to be updated to use the correct endpoint." -ForegroundColor Yellow
