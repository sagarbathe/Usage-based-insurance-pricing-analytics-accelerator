<#
.SYNOPSIS
    Provision the OBO (On-Behalf-Of) authentication stack for Fabric Data Agents.

.DESCRIPTION
    Creates the AAD app registration, configures Container Apps Easy Auth as
    the upstream user sign-in mechanism, and wires the OBO client_id /
    client_secret / tenant_id into the Container App as secrets and
    environment variables.

    What it does:
      1. Creates AAD app `<ContainerAppName>-obo`.
         - Web redirect URI:  https://<fqdn>/.auth/login/aad/callback
         - Implicit grant:    ID token enabled (required by Easy Auth)
         - Sign-in audience:  AzureADMyOrg
         - Exposes API:       api://<appId>/access_as_user
         - Required permission: Microsoft Fabric Service / user_impersonation
      2. Creates a 1-year client secret.
      3. Configures Container App Easy Auth (Microsoft provider) with that
         app id / secret and `unauthenticatedClientAction = RedirectToLoginPage`.
         No token store is needed (the app reads the user token straight
         from the X-MS-TOKEN-AAD-ACCESS-TOKEN header).
      4. Adds `OBO_CLIENT_ID`, `OBO_TENANT_ID` env vars and `obo-client-secret`
         secret to the Container App; restarts the latest revision.

    Re-running is idempotent: existing app registration is reused.

.NOTES
    After this script runs, you must grant **admin consent** for the
    Fabric `user_impersonation` permission in the Entra portal
    (or via `az ad app permission admin-consent --id <appId>`).
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# Load shared deployment values
. "$PSScriptRoot\deployment-config.ps1"

$AppDisplayName = "$ContainerAppName-obo"
$FabricApiAppId = '00000009-0000-0000-c000-000000000000'  # Microsoft Fabric / Power BI Service
$FabricUserImpersonationScopeId = '4ae1bf56-f562-4747-b7bc-2fa0874ed46f'

Write-Host '==> Resolving Container App FQDN...'
$Fqdn = az containerapp show -g $ResourceGroup -n $ContainerAppName --query 'properties.configuration.ingress.fqdn' -o tsv
if (-not $Fqdn) { throw "Could not resolve FQDN for $ContainerAppName" }
$RedirectUri = "https://$Fqdn/.auth/login/aad/callback"
Write-Host "    FQDN:         $Fqdn"
Write-Host "    Redirect URI: $RedirectUri"

Write-Host "==> Looking up existing AAD app '$AppDisplayName'..."
$AppId = az ad app list --display-name $AppDisplayName --query '[0].appId' -o tsv
if (-not $AppId) {
    Write-Host '    Not found. Creating new AAD app registration...'
    $AppId = az ad app create `
        --display-name $AppDisplayName `
        --sign-in-audience AzureADMyOrg `
        --web-redirect-uris $RedirectUri `
        --enable-id-token-issuance true `
        --query appId -o tsv
} else {
    Write-Host "    Reusing existing app: $AppId"
    az ad app update --id $AppId --web-redirect-uris $RedirectUri --enable-id-token-issuance true | Out-Null
}

Write-Host '==> Setting Application ID URI (api://<appId>)...'
az ad app update --id $AppId --identifier-uris "api://$AppId" | Out-Null

Write-Host '==> Adding Fabric user_impersonation delegated permission...'
az ad app permission add --id $AppId `
    --api $FabricApiAppId `
    --api-permissions "$FabricUserImpersonationScopeId=Scope" 2>$null | Out-Null

Write-Host '==> Ensuring service principal exists for the app...'
$Sp = az ad sp list --filter "appId eq '$AppId'" --query '[0].id' -o tsv
if (-not $Sp) {
    az ad sp create --id $AppId | Out-Null
}

Write-Host '==> Creating client secret (1-year)...'
$Secret = az ad app credential reset --id $AppId --display-name "obo-$(Get-Date -Format yyyyMMdd)" --years 1 --query password -o tsv
if (-not $Secret) { throw 'Failed to create client secret' }

Write-Host "==> Storing secret on Container App as 'obo-client-secret'..."
az containerapp secret set -g $ResourceGroup -n $ContainerAppName `
    --secrets "obo-client-secret=$Secret" | Out-Null

Write-Host '==> Setting Container App env vars (OBO_CLIENT_ID, OBO_TENANT_ID, OBO_CLIENT_SECRET)...'
az containerapp update -g $ResourceGroup -n $ContainerAppName `
    --set-env-vars `
        "OBO_CLIENT_ID=$AppId" `
        "OBO_TENANT_ID=$AzureTenantId" `
        "OBO_CLIENT_SECRET=secretref:obo-client-secret" | Out-Null

Write-Host '==> Configuring Easy Auth via REST PUT (Microsoft Entra provider)...'
$Sub = az account show --query id -o tsv
$AuthUri = "/subscriptions/$Sub/resourceGroups/$ResourceGroup/providers/Microsoft.App/containerApps/$ContainerAppName/authConfigs/current?api-version=2024-03-01"

# Body: enable platform, redirect unauthenticated to provider, configure AAD,
# expose the client secret name (Container Apps reads it from app secrets).
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
                    clientId                  = $AppId
                    clientSecretSettingName   = 'obo-client-secret'
                    openIdIssuer              = "https://login.microsoftonline.com/$AzureTenantId/v2.0"
                }
                validation = @{
                    allowedAudiences = @("api://$AppId")
                }
            }
        }
        login = @{ preserveUrlFragmentsForLogins = $false }
    }
} | ConvertTo-Json -Depth 10 -Compress

$BodyFile = New-TemporaryFile
Set-Content -Path $BodyFile -Value $AuthBody -Encoding UTF8
try {
    az rest --method PUT --uri $AuthUri --body "@$BodyFile" --headers 'Content-Type=application/json' | Out-Null
} finally {
    Remove-Item $BodyFile -Force -ErrorAction SilentlyContinue
}

Write-Host '==> Restarting latest revision...'
$Latest = az containerapp revision list -g $ResourceGroup -n $ContainerAppName --query '[0].name' -o tsv
az containerapp revision restart -g $ResourceGroup -n $ContainerAppName --revision $Latest | Out-Null

Write-Host ''
Write-Host '======================================================'
Write-Host ' OBO + Easy Auth provisioning complete.'
Write-Host '======================================================'
Write-Host " App URL:        https://$Fqdn"
Write-Host " AAD AppId:      $AppId"
Write-Host " Tenant:         $AzureTenantId"
Write-Host ''
Write-Host ' NEXT STEPS:'
Write-Host "  1. Grant admin consent for the Fabric user_impersonation permission:"
Write-Host "     az ad app permission admin-consent --id $AppId"
Write-Host '  2. Sign in to the app in an incognito window and verify the'
Write-Host '     Fabric Data Agent tabs work (calls now made as you, not the MI).'
