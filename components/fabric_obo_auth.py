"""
Fabric Data Agent authentication via browser MSAL + On-Behalf-Of (OBO).

Flow
----
1. The user signs in via an MSAL.js popup rendered in the sidebar
   (``streamlit-msal``). The popup requests an access token whose
   audience is *this app's* AAD app registration
   (scope ``api://<OBO_CLIENT_ID>/.default``).
2. The Python backend takes that user assertion and performs the
   OAuth 2.0 On-Behalf-Of swap with its confidential-client
   credentials, receiving a Fabric-audience token.
3. The Fabric token is used to call Fabric Data Agents.

Environment variables
---------------------
- ``OBO_CLIENT_ID``       — AppId of the AAD app registration.
- ``OBO_CLIENT_SECRET``   — Client secret for that app.
- ``OBO_TENANT_ID``       — Tenant ID (defaults to ``AZURE_TENANT_ID``).

Local-dev fallback
------------------
If ``USE_CLI_AUTH=1``, skip MSAL/OBO and use ``AzureCliCredential``
to mint a Fabric token directly as the signed-in CLI user.
"""

from __future__ import annotations

import logging
import os
import time

import streamlit as st

logging.getLogger("msal").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)

_FABRIC_OBO_SCOPE = "https://api.fabric.microsoft.com/user_impersonation"
_FABRIC_DEFAULT_SCOPE = "https://api.fabric.microsoft.com/.default"

# Session keys
_SK_USER_TOKEN = "_msal_user_access_token"
_SK_FABRIC_TOKEN = "_fabric_obo_token"
_SK_FABRIC_EXP = "_fabric_obo_token_exp"
_SK_USERNAME = "_msal_username"


def _obo_config() -> tuple[str, str, str] | None:
    client_id = os.environ.get("OBO_CLIENT_ID", "").strip()
    client_secret = os.environ.get("OBO_CLIENT_SECRET", "").strip()
    tenant_id = (
        os.environ.get("OBO_TENANT_ID", "").strip()
        or os.environ.get("AZURE_TENANT_ID", "").strip()
    )
    if not (client_id and client_secret and tenant_id):
        return None
    return client_id, client_secret, tenant_id


def _use_cli() -> bool:
    return os.environ.get("USE_CLI_AUTH", "").strip() in ("1", "true", "True")


def render_signin_widget() -> str | None:
    """Render the MSAL sign-in widget. Returns the user access token, or None.

    Must be called inside a Streamlit container (sidebar is recommended).
    """
    if _use_cli():
        st.session_state[_SK_USERNAME] = "cli-user"
        return "cli"

    cfg = _obo_config()
    if cfg is None:
        st.error("OBO env vars (OBO_CLIENT_ID / OBO_CLIENT_SECRET / OBO_TENANT_ID) not set.")
        return None
    client_id, _client_secret, tenant_id = cfg

    try:
        from streamlit_msal import Msal
    except ImportError:
        st.error("streamlit-msal not installed. Add it to requirements.txt.")
        return None

    auth_data = Msal.initialize_ui(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        scopes=[f"api://{client_id}/.default"],
        connecting_label="Connecting…",
        disconnected_label="Sign in to access Fabric Data Agents",
        sign_in_label="Sign in",
        sign_out_label="Sign out",
    )

    if not auth_data:
        st.session_state.pop(_SK_USER_TOKEN, None)
        st.session_state.pop(_SK_FABRIC_TOKEN, None)
        st.session_state.pop(_SK_FABRIC_EXP, None)
        st.session_state.pop(_SK_USERNAME, None)
        return None

    access_token = auth_data.get("accessToken")
    account = auth_data.get("account") or {}
    st.session_state[_SK_USER_TOKEN] = access_token
    st.session_state[_SK_USERNAME] = (
        account.get("username") or account.get("name") or "user"
    )
    return access_token


def get_signed_in_username() -> str | None:
    return st.session_state.get(_SK_USERNAME)


def _exchange_user_token_for_fabric_token(
    user_assertion: str,
) -> tuple[str | None, int, str]:
    """OAuth 2.0 OBO exchange. Returns (token, expires_in, debug_info)."""
    cfg = _obo_config()
    if cfg is None:
        return None, 0, "OBO env vars missing"
    client_id, client_secret, tenant_id = cfg

    try:
        from msal import ConfidentialClientApplication
    except ImportError:
        return None, 0, "msal not installed"

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
        return result["access_token"], int(result.get("expires_in", 3600)), "ok"
    err = result.get("error", "unknown")
    desc_lines = (result.get("error_description") or "").splitlines()
    desc = desc_lines[0] if desc_lines else ""
    corr = result.get("correlation_id", "")
    return None, 0, f"{err} | {desc} | corr={corr}"


def get_fabric_bearer_token() -> tuple[str | None, str]:
    """Return (token, source_or_debug_reason)."""
    if _use_cli():
        try:
            from azure.identity import AzureCliCredential

            return AzureCliCredential().get_token(_FABRIC_DEFAULT_SCOPE).token, "cli"
        except Exception as e:
            return None, f"cli auth failed: {e}"

    cached = st.session_state.get(_SK_FABRIC_TOKEN)
    cached_exp = st.session_state.get(_SK_FABRIC_EXP, 0)
    if cached and time.time() < cached_exp - 60:
        return cached, "obo (cached)"

    user_token = st.session_state.get(_SK_USER_TOKEN)
    if not user_token:
        return None, "user not signed in (use the sign-in widget in the sidebar)"

    fabric_token, expires_in, info = _exchange_user_token_for_fabric_token(user_token)
    if fabric_token is None:
        return None, f"obo exchange failed: {info}"

    st.session_state[_SK_FABRIC_TOKEN] = fabric_token
    st.session_state[_SK_FABRIC_EXP] = time.time() + expires_in
    return fabric_token, "obo"
