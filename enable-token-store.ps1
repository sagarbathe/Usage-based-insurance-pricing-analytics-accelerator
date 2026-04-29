<#
.SYNOPSIS
    Enable the Easy Auth token store and configure loginParameters so the
    Container App receives X-MS-TOKEN-AAD-ACCESS-TOKEN with an audience
    of api://<OBO_CLIENT_ID> (required for the OBO flow).

.DESCRIPTION
    Without the token store, Container Apps Easy Auth never forwards the
    X-MS-TOKEN-AAD-ACCESS-TOKEN header even though the user is signed in
    (only the principal headers and the ID token are forwarded).
    Without loginParameters.scope, no upstream access token is requested
    at all, so even with the token store there is nothing to forward.

    This script:
      1. Ensures the configured storage account allows shared-key access
         (needed to mint a long-lived SAS).
      2. Creates an `easyauth-tokens` blob container.
      3. Generates a 2-year account-key SAS URL with rwdl/rwdlacup perms.
      4. Stores the SAS URL as a Container App secret
         (`easyauth-token-store-sas`).
      5. Re-PUTs the authConfig with:
           - login.tokenStore.enabled = true
           - login.tokenStore.azureBlobStorage.sasUrlSettingName = ...
           - identityProviders.azureActiveDirectory.login.loginParameters
             = ["scope=openid profile offline_access api://<appId>/.default"]
      6. Bumps the active revision so the new auth config takes effect on
         the running replicas.
#>

[CmdletBinding()]
param(
    [string]$StorageAccountName = 'acrubipricingsagartok',
    [string]$BlobContainerName  = 'easyauth-tokens',
    [int]   $SasYears           = 2
)

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\deployment-config.ps1"

Write-Host '==> Resolving OBO_CLIENT_ID from Container App env vars...'
$OboClientId = az containerapp show -g $ResourceGroup -n $ContainerAppName `
    --query "properties.template.containers[0].env[?name=='OBO_CLIENT_ID'].value | [0]" -o tsv
if (-not $OboClientId) { throw 'OBO_CLIENT_ID env var not found on Container App. Run enable-obo-auth.ps1 first.' }
Write-Host "    OBO_CLIENT_ID: $OboClientId"

Write-Host "==> Ensuring shared-key access is enabled on $StorageAccountName..."
az storage account update -g $ResourceGroup -n $StorageAccountName --allow-shared-key-access true | Out-Null
Write-Host '    Waiting 30s for shared-key change to propagate...'
Start-Sleep -Seconds 30

Write-Host '==> Fetching storage account key...'
$StorageKey = az storage account keys list -g $ResourceGroup -n $StorageAccountName --query '[0].value' -o tsv
if (-not $StorageKey) { throw 'Could not retrieve storage account key.' }

Write-Host "==> Ensuring blob container '$BlobContainerName' exists (using AAD login auth)..."
az storage container create `
    --name $BlobContainerName `
    --account-name $StorageAccountName `
    --auth-mode login | Out-Null

Write-Host "==> Generating $SasYears-year account-key SAS for the container..."
$ExpiryUtc = (Get-Date).ToUniversalTime().AddYears($SasYears).ToString('yyyy-MM-ddTHH:mm:ssZ')
$Sas = az storage container generate-sas `
    --account-name $StorageAccountName `
    --account-key $StorageKey `
    --name $BlobContainerName `
    --permissions racwdli `
    --expiry $ExpiryUtc `
    --https-only `
    -o tsv
if (-not $Sas) { throw 'Failed to generate SAS.' }
$SasUrl = "https://$StorageAccountName.blob.core.windows.net/$BlobContainerName" + '?' + $Sas
Write-Host "    SAS expires: $ExpiryUtc"

$SecretName = 'easyauth-tok-sas'
Write-Host "==> Storing SAS URL as Container App secret '$SecretName'..."
# PowerShell mangles '&' chars when invoking az.cmd. Stash the value
# in an env var, then let cmd.exe expand it INSIDE quotes (where '&'
# is literal), so the SAS URL reaches az.cmd intact.
$env:__SASTMP = $SasUrl
try {
    cmd /c "az containerapp secret set -g $ResourceGroup -n $ContainerAppName --secrets `"$SecretName=%__SASTMP%`" >nul"
} finally {
    Remove-Item Env:__SASTMP -ErrorAction SilentlyContinue
}

Write-Host '==> PUTting updated authConfig (token store + loginParameters)...'
$Sub = az account show --query id -o tsv
$AuthUri = "/subscriptions/$Sub/resourceGroups/$ResourceGroup/providers/Microsoft.App/containerApps/$ContainerAppName/authConfigs/current?api-version=2024-03-01"

$AuthBody = @{
    properties = @{
        platform = @{ enabled = $true; runtimeVersion = '~1' }
        globalValidation = @{
            unauthenticatedClientAction = 'RedirectToLoginPage'
            redirectToProvider          = 'azureactivedirectory'
        }
        identityProviders = @{
            azureActiveDirectory = @{
                enabled = $true
                registration = @{
                    clientId                = $OboClientId
                    clientSecretSettingName = 'obo-client-secret'
                    openIdIssuer            = "https://login.microsoftonline.com/$AzureTenantId/v2.0"
                }
                validation = @{
                    allowedAudiences = @("api://$OboClientId")
                }
                login = @{
                    # Request offline_access (refresh token) AND an access
                    # token whose audience is this app, so OBO can exchange
                    # it for a Fabric token.
                    loginParameters = @(
                        "scope=openid profile offline_access api://$OboClientId/.default"
                    )
                }
            }
        }
        login = @{
            preserveUrlFragmentsForLogins = $false
            tokenStore = @{
                enabled = $true
                azureBlobStorage = @{
                    sasUrlSettingName = $SecretName
                }
            }
        }
    }
} | ConvertTo-Json -Depth 12 -Compress

$BodyFile = New-TemporaryFile
Set-Content -Path $BodyFile -Value $AuthBody -Encoding UTF8
try {
    az rest --method PUT --uri $AuthUri --body "@$BodyFile" --headers 'Content-Type=application/json' | Out-Null
} finally {
    Remove-Item $BodyFile -Force -ErrorAction SilentlyContinue
}

Write-Host '==> Bumping active revision to apply new auth config...'
$Suffix = "tokenstore-$(Get-Date -Format HHmmss)"
$NewRev = az containerapp update -g $ResourceGroup -n $ContainerAppName `
    --revision-suffix $Suffix --query "properties.latestRevisionName" -o tsv
Write-Host "    New revision: $NewRev"

Write-Host ''
Write-Host '======================================================'
Write-Host ' Token store + loginParameters configured.'
Write-Host '======================================================'
Write-Host ' NEXT: in an INCOGNITO window, sign in fresh, then click'
Write-Host ' a Fabric Data Agent and ask a question. The diagnostic'
Write-Host ' line should now read "obo" (success) or surface a real'
Write-Host ' MSAL error to fix.'
