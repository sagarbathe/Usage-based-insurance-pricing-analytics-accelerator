<#
.SYNOPSIS
    Repair the OBO AAD app: expose an `access_as_user` OAuth2Permission,
    grant admin consent for it, and update Easy Auth loginParameters to
    request that scope so X-MS-TOKEN-AAD-ACCESS-TOKEN has the right audience.

.DESCRIPTION
    The 401 sign-in failure occurred because Easy Auth was configured to
    request `api://<appId>/.default`, but the app didn't expose any
    OAuth2Permissions. AAD rejects `.default` when the resource has no
    granted/consentable scopes.

    Fix:
      1. PATCH the AAD app's `api.oauth2PermissionScopes` to include
         `access_as_user` (admin+user consent enabled).
      2. Pre-authorize Easy Auth (the same app) so no per-tenant
         consent prompt is needed.
      3. Update authConfig loginParameters to
         `scope=openid profile offline_access api://<appId>/access_as_user`
         so the access token forwarded to the app has audience
         `api://<appId>` — exactly what the OBO assertion requires.
      4. Bump revision.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\deployment-config.ps1"

Write-Host '==> Resolving OBO_CLIENT_ID...'
$AppId = az containerapp show -g $ResourceGroup -n $ContainerAppName `
    --query "properties.template.containers[0].env[?name=='OBO_CLIENT_ID'].value | [0]" -o tsv
if (-not $AppId) { throw 'OBO_CLIENT_ID not set on Container App.' }
Write-Host "    OBO_CLIENT_ID: $AppId"

Write-Host '==> Looking up app object id...'
$ObjectId = az ad app show --id $AppId --query id -o tsv

Write-Host '==> Checking existing OAuth2 permissions on app...'
$ExistingScopesJson = az ad app show --id $AppId --query 'api.oauth2PermissionScopes' -o json
$ExistingScopes = if ($ExistingScopesJson) { $ExistingScopesJson | ConvertFrom-Json } else { @() }
$AccessAsUser = $ExistingScopes | Where-Object { $_.value -eq 'access_as_user' } | Select-Object -First 1

if (-not $AccessAsUser) {
    Write-Host '    Adding access_as_user scope via Microsoft Graph PATCH...'
    $ScopeId = [guid]::NewGuid().ToString()
    $NewScope = @{
        id                      = $ScopeId
        adminConsentDescription = "Allow the app to call Fabric APIs on behalf of the signed-in user."
        adminConsentDisplayName = 'Access Fabric as the signed-in user'
        userConsentDescription  = "Allow this app to call Fabric on your behalf."
        userConsentDisplayName  = 'Access Fabric as you'
        value                   = 'access_as_user'
        type                    = 'User'
        isEnabled               = $true
    }
    $UpdatedScopes = @($ExistingScopes) + $NewScope
    $Body = @{ api = @{ oauth2PermissionScopes = $UpdatedScopes } } | ConvertTo-Json -Depth 10 -Compress
    $BodyFile = New-TemporaryFile
    Set-Content -Path $BodyFile -Value $Body -Encoding UTF8
    try {
        az rest --method PATCH `
            --uri "https://graph.microsoft.com/v1.0/applications/$ObjectId" `
            --body "@$BodyFile" `
            --headers 'Content-Type=application/json' | Out-Null
    } finally {
        Remove-Item $BodyFile -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 5
    $AccessAsUser = (az ad app show --id $AppId --query 'api.oauth2PermissionScopes' -o json | ConvertFrom-Json) `
        | Where-Object { $_.value -eq 'access_as_user' } | Select-Object -First 1
    if (-not $AccessAsUser) { throw 'Failed to add access_as_user scope.' }
} else {
    Write-Host "    Existing access_as_user scope id: $($AccessAsUser.id)"
}

Write-Host '==> Pre-authorizing the same app to use access_as_user (no consent prompt)...'
$PreAuthBody = @{
    api = @{
        preAuthorizedApplications = @(
            @{ appId = $AppId; delegatedPermissionIds = @($AccessAsUser.id) }
        )
    }
} | ConvertTo-Json -Depth 10 -Compress
$BodyFile = New-TemporaryFile
Set-Content -Path $BodyFile -Value $PreAuthBody -Encoding UTF8
try {
    az rest --method PATCH `
        --uri "https://graph.microsoft.com/v1.0/applications/$ObjectId" `
        --body "@$BodyFile" `
        --headers 'Content-Type=application/json' | Out-Null
} finally {
    Remove-Item $BodyFile -Force -ErrorAction SilentlyContinue
}

Write-Host '==> Re-PUTting authConfig with corrected loginParameters...'
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
                    clientId                = $AppId
                    clientSecretSettingName = 'obo-client-secret'
                    openIdIssuer            = "https://login.microsoftonline.com/$AzureTenantId/v2.0"
                }
                validation = @{
                    allowedAudiences = @("api://$AppId")
                }
                login = @{
                    loginParameters = @(
                        "scope=openid profile offline_access api://$AppId/access_as_user"
                    )
                }
            }
        }
        login = @{
            preserveUrlFragmentsForLogins = $false
            tokenStore = @{
                enabled = $true
                azureBlobStorage = @{
                    sasUrlSettingName = 'easyauth-tok-sas'
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

Write-Host '==> Bumping revision...'
$Suffix = "scopefix-$(Get-Date -Format HHmmss)"
$NewRev = az containerapp update -g $ResourceGroup -n $ContainerAppName `
    --revision-suffix $Suffix --query "properties.latestRevisionName" -o tsv
Write-Host "    New revision: $NewRev"

Write-Host ''
Write-Host '======================================================'
Write-Host ' OBO scope fix complete.'
Write-Host '======================================================'
Write-Host ' Sign in fresh in INCOGNITO and try a Data Agent.'
