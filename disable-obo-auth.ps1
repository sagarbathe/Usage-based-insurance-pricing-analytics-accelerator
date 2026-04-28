<#
.SYNOPSIS
    Tear down the OBO/Easy Auth stack created by enable-obo-auth.ps1.

.DESCRIPTION
    - Disables Easy Auth on the Container App.
    - Removes the OBO_* env vars and the obo-client-secret.
    - Deletes the AAD app registration `<ContainerAppName>-obo`.
    - Restarts the latest revision so the app falls back to the
      Managed-Identity auth path (if any).
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\deployment-config.ps1"

$AppDisplayName = "$ContainerAppName-obo"

Write-Host '==> Disabling Easy Auth on Container App...'
az containerapp auth update -g $ResourceGroup -n $ContainerAppName --enabled false | Out-Null

Write-Host '==> Removing OBO env vars from Container App...'
az containerapp update -g $ResourceGroup -n $ContainerAppName `
    --remove-env-vars OBO_CLIENT_ID OBO_TENANT_ID OBO_CLIENT_SECRET 2>$null | Out-Null

Write-Host '==> Removing obo-client-secret from Container App...'
az containerapp secret remove -g $ResourceGroup -n $ContainerAppName --secret-names obo-client-secret 2>$null | Out-Null

Write-Host "==> Deleting AAD app '$AppDisplayName' (if present)..."
$AppId = az ad app list --display-name $AppDisplayName --query '[0].appId' -o tsv
if ($AppId) {
    az ad app delete --id $AppId | Out-Null
    Write-Host "    Deleted appId $AppId"
} else {
    Write-Host '    No matching AAD app found.'
}

Write-Host '==> Restarting latest revision...'
$Latest = az containerapp revision list -g $ResourceGroup -n $ContainerAppName --query '[0].name' -o tsv
az containerapp revision restart -g $ResourceGroup -n $ContainerAppName --revision $Latest | Out-Null

Write-Host ''
Write-Host 'OBO/Easy Auth resources removed.'
