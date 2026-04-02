# test-fabric-dataagent-api.ps1 - Test which API pattern Fabric Data Agents support

$WorkspaceId = "db7dcf85-001e-4277-a85e-3c92029900bc"
$DataAgentId = "50a54dc0-3f9f-44b2-84f6-8e54999bffa8"
$BaseUrl = "https://api.fabric.microsoft.com/v1/workspaces/$WorkspaceId/dataagents/$DataAgentId"

Write-Host "Testing Fabric Data Agent API patterns..." -ForegroundColor Cyan
Write-Host ""

$Token = az account get-access-token --resource https://api.fabric.microsoft.com --query accessToken -o tsv
$Headers = @{
    "Authorization" = "Bearer $Token"
    "Content-Type" = "application/json"
    "api-version" = "2024-05-01-preview"
}

# Test 1: Check if chat/completions is available (simpler API)
Write-Host "Test 1: Checking /aiassistant/openai/chat/completions..." -ForegroundColor Yellow
$ChatUrl = "$BaseUrl/aiassistant/openai/chat/completions"
try {
    $Body = @{
        model = "gpt-4"
        messages = @(
            @{
                role = "user"
                content = "Hello, test message"
            }
        )
    } | ConvertTo-Json
    
    $Response = Invoke-RestMethod -Uri $ChatUrl -Headers $Headers -Method Post -Body $Body
    Write-Host "✓ Chat completions endpoint works!" -ForegroundColor Green
    Write-Host "  Response: $($Response | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
} catch {
    $StatusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "✗ Status: $StatusCode - $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Check if threads API is available
Write-Host "`nTest 2: Checking thread creation..." -ForegroundColor Yellow
$ThreadUrl = "$BaseUrl/__private/aiassistant/threads/fabric?tag=`"test-thread-$(Get-Random)`""
try {
    $ThreadResponse = Invoke-RestMethod -Uri $ThreadUrl -Headers $Headers -Method Get
    Write-Host "✓ Thread endpoint works!" -ForegroundColor Green
    Write-Host "  Thread ID: $($ThreadResponse.id)" -ForegroundColor Gray
    
    # Test 3: Try creating a message in the thread
    Write-Host "`nTest 3: Testing message creation in thread..." -ForegroundColor Yellow
    $MessageUrl = "$BaseUrl/aiassistant/openai/threads/$($ThreadResponse.id)/messages?api-version=2024-05-01-preview"
    $MessageBody = @{
        role = "user"
        content = "Test message"
    } | ConvertTo-Json
    
    try {
        $MessageResponse = Invoke-RestMethod -Uri $MessageUrl -Headers $Headers -Method Post -Body $MessageBody
        Write-Host "✓ Message creation works!" -ForegroundColor Green
        
        # Test 4: Try creating a run
        Write-Host "`nTest 4: Testing run creation..." -ForegroundColor Yellow
        $RunUrl = "$BaseUrl/aiassistant/openai/threads/$($ThreadResponse.id)/runs?api-version=2024-05-01-preview"
        $RunBody = @{
            assistant_id = "assistant"
        } | ConvertTo-Json
        
        try {
            $RunResponse = Invoke-RestMethod -Uri $RunUrl -Headers $Headers -Method Post -Body $RunBody
            Write-Host "✓ Run creation works!" -ForegroundColor Green
            Write-Host "  Run ID: $($RunResponse.id)" -ForegroundColor Gray
        } catch {
            Write-Host "✗ Run creation failed: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "  This suggests Assistants API may not be fully supported" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "✗ Message creation failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Thread creation failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n---" -ForegroundColor Cyan
Write-Host "Recommendation:" -ForegroundColor Cyan
Write-Host "If chat/completions works, use that instead of the Assistants API (threads/runs)" -ForegroundColor Gray
Write-Host "It's simpler and may be better supported by Fabric Data Agents" -ForegroundColor Gray
