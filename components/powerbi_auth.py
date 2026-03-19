"""
Power BI Embed-Token Generator (Managed Identity).

Acquires an access token for the Power BI REST API using the
Azure App Service system-assigned Managed Identity.

Pre-requisites
--------------
1. Create a Linux App Service (Python 3.11+).
2. Enable **System-assigned Managed Identity** in the App Service
   Identity blade.
3. Grant the managed identity access:
   - *Viewer* role on the Power BI workspace containing your reports.
   - In the Power BI Admin Portal, enable "Service principals can use
     Power BI APIs" for a security group containing the MI.
4. No secrets or env-vars are required — the identity is attached
   automatically at runtime.
"""

import logging

import requests
import streamlit as st

# ── Silence noisy azure-identity / msal logs ──────────────────
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("msal").setLevel(logging.WARNING)

_POWERBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
_POWERBI_API = "https://api.powerbi.com/v1.0/myorg"


def _get_credential():
    """Return a ManagedIdentityCredential for the App Service MI."""
    from azure.identity import ManagedIdentityCredential
    return ManagedIdentityCredential()


# ── Token cache (avoid re-auth on every Streamlit rerun) ──────
@st.cache_data(ttl=3000, show_spinner=False)
def get_access_token(report_id: str, group_id: str) -> dict:
    """
    Acquire a Power BI **V2 embed token** for a Fabric DirectLake
    report using the Managed Identity.

    Flow:
      1. AAD token via Managed Identity.
      2. GET /groups/{gid}/reports/{rid} → embed URL + dataset ID.
      3. POST /GenerateToken (V2 multi-resource API) with the
         report and dataset → scoped embed token.

    Returns
    -------
    dict  On success: {"token", "embed_url", "report_id"}.
          On failure: {"error": str}.
    """
    # Step 1 — AAD token
    try:
        credential = _get_credential()
        aad_token = credential.get_token(_POWERBI_SCOPE).token
    except Exception as exc:
        return {"error": f"Managed Identity could not acquire an AAD token for Power BI.\n\n`{exc}`"}

    headers = {"Authorization": f"Bearer {aad_token}"}

    # Step 2 — Get report metadata (embed URL + datasetId)
    report_url = f"{_POWERBI_API}/groups/{group_id}/reports/{report_id}"
    try:
        resp = requests.get(report_url, headers=headers, timeout=15)
    except requests.RequestException as exc:
        return {"error": f"GET report request failed: `{exc}`"}

    if resp.status_code != 200:
        return {
            "error": (
                f"**GET /reports** returned HTTP {resp.status_code}\n\n"
                f"```json\n{resp.text[:500]}\n```\n\n"
                f"**report_id:** `{report_id}`  \n"
                f"**group_id:** `{group_id}`"
            )
        }

    report_meta = resp.json()
    embed_url = report_meta.get("embedUrl", "")
    dataset_id = report_meta.get("datasetId", "")

    # Step 3 — V2 multi-resource GenerateToken (supports DirectLake)
    gen_url = f"{_POWERBI_API}/GenerateToken"
    body = {
        "datasets": [{"id": dataset_id}],
        "reports": [{"id": report_id, "allowEdit": False}],
        "targetWorkspaces": [{"id": group_id}],
    }
    try:
        resp = requests.post(gen_url, headers=headers, json=body, timeout=15)
    except requests.RequestException as exc:
        return {"error": f"V2 GenerateToken request failed: `{exc}`"}

    if resp.status_code != 200:
        return {
            "error": (
                f"**POST /GenerateToken (V2)** returned HTTP {resp.status_code}\n\n"
                f"```json\n{resp.text[:500]}\n```\n\n"
                f"**dataset_id:** `{dataset_id}`  \n"
                f"**report_id:** `{report_id}`\n\n"
                "Ensure the MI is a **Member** of the Power BI workspace "
                "and *'Allow service principals to use Power BI APIs'* is "
                "enabled in the Power BI Admin Portal."
            )
        }

    return {
        "token": resp.json()["token"],
        "embed_url": embed_url,
        "report_id": report_id,
        "dataset_id": dataset_id,
    }


@st.cache_data(ttl=3000, show_spinner=False)
def get_edit_token(report_id: str, group_id: str) -> dict:
    """
    Acquire a V2 embed token with **edit** permission for a report.
    Used for the ad-hoc explore experience (blank report in edit mode).

    Returns
    -------
    dict  On success: {"token", "embed_url", "report_id"}.
          On failure: {"error": str}.
    """
    try:
        credential = _get_credential()
        aad_token = credential.get_token(_POWERBI_SCOPE).token
    except Exception as exc:
        return {"error": f"Managed Identity AAD token failed.\n\n`{exc}`"}

    headers = {"Authorization": f"Bearer {aad_token}"}

    # Get report metadata (embed URL + datasetId)
    report_url = f"{_POWERBI_API}/groups/{group_id}/reports/{report_id}"
    try:
        resp = requests.get(report_url, headers=headers, timeout=15)
    except requests.RequestException as exc:
        return {"error": f"GET explore report request failed: `{exc}`"}

    if resp.status_code != 200:
        return {
            "error": (
                f"**GET /reports (explore)** returned HTTP {resp.status_code}\n\n"
                f"```json\n{resp.text[:500]}\n```"
            )
        }

    report_meta = resp.json()
    embed_url = report_meta.get("embedUrl", "")
    dataset_id = report_meta.get("datasetId", "")

    # V2 GenerateToken with allowEdit=True
    gen_url = f"{_POWERBI_API}/GenerateToken"
    body = {
        "datasets": [{"id": dataset_id}],
        "reports": [{"id": report_id, "allowEdit": True}],
        "targetWorkspaces": [{"id": group_id}],
    }
    try:
        resp = requests.post(gen_url, headers=headers, json=body, timeout=15)
    except requests.RequestException as exc:
        return {"error": f"V2 GenerateToken (edit) request failed: `{exc}`"}

    if resp.status_code != 200:
        return {
            "error": (
                f"**POST /GenerateToken (edit)** returned HTTP {resp.status_code}\n\n"
                f"```json\n{resp.text[:500]}\n```"
            )
        }

    return {
        "token": resp.json()["token"],
        "embed_url": embed_url,
        "report_id": report_id,
    }
