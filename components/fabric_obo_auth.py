"""
Fabric Data Agent authentication via On-Behalf-Of (OBO) flow.

Architecture
------------
- The Streamlit app sits behind Azure Container Apps **Easy Auth**
  (Microsoft Entra identity provider). Easy Auth handles the user
  sign-in and forwards the user's access token to the app via the
  ``X-MS-TOKEN-AAD-ACCESS-TOKEN`` request header. That token's
  audience is *this app's* AAD app registration
  (``api://<OBO_CLIENT_ID>``).
- To call Microsoft Fabric **as the signed-in user**, the app
  performs the OAuth 2.0 *On-Behalf-Of* exchange against Microsoft
  Entra: it presents the incoming user assertion together with its
  own confidential-client credentials and receives a downstream
  access token whose audience is the Fabric API.
- The downstream token is then attached as ``Authorization: Bearer
  <token>`` on calls to Fabric Data Agents.

Environment variables (set as Container App secrets / settings)
---------------------------------------------------------------
- ``OBO_CLIENT_ID``       — AppId of the AAD app registration that
                            backs Easy Auth and acts as the OBO
                            confidential client.
- ``OBO_CLIENT_SECRET``   — Client secret for that app.
- ``OBO_TENANT_ID``       — Tenant ID (defaults to ``AZURE_TENANT_ID``
                            if not set).

Local-dev fallback
------------------
If ``USE_CLI_AUTH=1`` is set and no ``X-MS-TOKEN-AAD-ACCESS-TOKEN``
header is present, this module skips OBO and uses
``AzureCliCredential`` to mint a Fabric token directly as the
signed-in CLI user. This avoids needing Easy Auth running locally.
"""

from __future__ import annotations

import logging
import os
import typing as t

import streamlit as st

logging.getLogger("msal").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)

_FABRIC_OBO_SCOPE = "https://api.fabric.microsoft.com/user_impersonation"
_FABRIC_DEFAULT_SCOPE = "https://api.fabric.microsoft.com/.default"

_EASY_AUTH_TOKEN_HEADER = "x-ms-token-aad-access-token"


# ── Helpers ──────────────────────────────────────────────────


def _get_easy_auth_user_token() -> str | None:
    """Return the user access token forwarded by Container Apps Easy Auth.

    Easy Auth injects ``X-MS-TOKEN-AAD-ACCESS-TOKEN`` into every
    request when the AAD identity provider is configured.
    """
    # Preferred: stable Streamlit API (>= 1.37).
    try:
        headers = st.context.headers  # type: ignore[attr-defined]
        if headers:
            for k, v in dict(headers).items():
                if k.lower() == _EASY_AUTH_TOKEN_HEADER and v:
                    return v
    except Exception:
        pass

    # Fallback: private API on older Streamlit versions.
    try:
        from streamlit.web.server.websocket_headers import (  # type: ignore[import-not-found]
            _get_websocket_headers,
        )

        headers = _get_websocket_headers() or {}
        for k, v in headers.items():
            if k.lower() == _EASY_AUTH_TOKEN_HEADER and v:
                return v
    except Exception:
        pass

    return None


def _get_local_dev_fabric_token() -> str | None:
    """Return a Fabric token from ``az login`` for local development."""
    if os.environ.get("USE_CLI_AUTH", "").strip() not in ("1", "true", "True"):
        return None
    try:
        from azure.identity import AzureCliCredential

        return AzureCliCredential().get_token(_FABRIC_DEFAULT_SCOPE).token
    except Exception:
        return None


# ── OBO exchange ─────────────────────────────────────────────


def _obo_config() -> tuple[str, str, str] | None:
    """Return (client_id, client_secret, tenant_id) or None if not configured."""
    client_id = os.environ.get("OBO_CLIENT_ID", "").strip()
    client_secret = os.environ.get("OBO_CLIENT_SECRET", "").strip()
    tenant_id = (
        os.environ.get("OBO_TENANT_ID", "").strip()
        or os.environ.get("AZURE_TENANT_ID", "").strip()
    )
    if not (client_id and client_secret and tenant_id):
        return None
    return client_id, client_secret, tenant_id


def _exchange_user_token_for_fabric_token(user_assertion: str) -> str | None:
    """Perform the OAuth 2.0 OBO exchange and return a Fabric access token."""
    cfg = _obo_config()
    if cfg is None:
        return None
    client_id, client_secret, tenant_id = cfg

    try:
        from msal import ConfidentialClientApplication
    except ImportError:
        return None

    app = ConfidentialClientApplication(
        client_id=client_id,
        client_credential=client_secret,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
    )
    result = app.acquire_token_on_behalf_of(
        user_assertion=user_assertion,
        scopes=[_FABRIC_OBO_SCOPE],
    )
    if "access_token" in result:
        return result["access_token"]

    # Surface a concise error in logs to aid diagnosis (no PII).
    err = result.get("error", "unknown")
    desc = (result.get("error_description") or "").splitlines()[0:1]
    print(f"⚠️ OBO exchange failed: {err} — {' '.join(desc)}")
    return None


# ── Public API ───────────────────────────────────────────────


def get_fabric_bearer_token() -> tuple[str | None, str]:
    """Acquire a Fabric API bearer token.

    Returns
    -------
    (token, source)
        ``token`` is the access token (or ``None`` on failure).
        ``source`` is one of ``"obo"``, ``"cli"`` or ``"none"`` to
        aid diagnostics.
    """
    user_assertion = _get_easy_auth_user_token()
    if user_assertion:
        token = _exchange_user_token_for_fabric_token(user_assertion)
        if token:
            return token, "obo"

    cli_token = _get_local_dev_fabric_token()
    if cli_token:
        return cli_token, "cli"

    return None, "none"
