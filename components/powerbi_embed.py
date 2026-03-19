"""
Power BI Embedded Report Component.

Uses the App Service Managed Identity to generate embed tokens
server-side so end-users never see a Power BI sign-in prompt.
Falls back to a plain iframe if token generation fails.
"""

import html as _html
import json as _json

import streamlit as st

from components.powerbi_auth import get_access_token, get_edit_token


# ── Power BI JS SDK embed via st.components.v1.html ───────────
_EMBED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
  <style>
    html, body {{ margin:0; padding:0; height:100%; background:#fff; }}
    #reportContainer {{ width:100%; height:100%; }}
    #errorBox {{ display:none; color:#c00; font-family:sans-serif; padding:1em; }}
  </style>
</head>
<body>
  <div id="reportContainer"></div>
  <div id="errorBox"></div>
  <script>
    var models = window["powerbi-client"].models;
    var config = {{
      type: "report",
      id: {report_id_json},
      embedUrl: {embed_url_json},
      accessToken: {access_token_json},
      tokenType: models.TokenType.Embed,
      settings: {{
        personalizedVisuals: {{ enabled: true }},
        panes: {{
          filters: {{ expanded: false, visible: false }},
          pageNavigation: {{ visible: true }}
        }},
        background: models.BackgroundType.Default,
        navContentPaneEnabled: true
      }}
    }};
    var container = document.getElementById("reportContainer");
    var report = powerbi.embed(container, config);
    report.on("loaded", function() {{
      report.getPages().then(function(pages) {{
        var active = pages.filter(function(p) {{ return p.isActive; }})[0] || pages[0];
        if (active && active.defaultSize) {{
          var ratio = active.defaultSize.height / active.defaultSize.width;
          var w = container.clientWidth;
          container.style.height = Math.round(w * ratio) + "px";
        }}
      }});
    }});
    report.on("error", function(event) {{
      var err = event.detail || {{}};
      var box = document.getElementById("errorBox");
      box.style.display = "block";
      box.innerText = "Power BI error: " + (err.message || JSON.stringify(err));
    }});
  </script>
</body>
</html>
"""


def render_powerbi_report(
    embed_url: str,
    title: str = "Power BI Report",
    description: str = "",
    height: int = 800,
    report_id: str = "",
    group_id: str = "",
) -> None:
    """
    Render an embedded Power BI report panel.

    Parameters
    ----------
    embed_url : str
        Fallback Power BI embed URL (used only when env-vars are not set).
    title : str
        Display title above the report.
    description : str
        Short description of report contents.
    height : int
        Iframe height in pixels.
    report_id : str
        Power BI report GUID (from config).
    group_id : str
        Power BI workspace / group GUID (from config).
    """
    st.markdown(f"### 📊 {title}")
    if description:
        st.caption(description)

    is_placeholder = "<YOUR_" in embed_url and not report_id

    if is_placeholder:
        # ── Placeholder mode ──────────────────────────────
        st.info(
            "🔗 **Power BI report placeholder**\n\n"
            "To connect a live report:\n"
            "1. Set `POWERBI_*_REPORT_ID` and `POWERBI_*_GROUP_ID` in `deploy.ps1`\n"
            "2. Re-run `deploy.ps1` to update App Settings\n"
            "3. Ensure Managed Identity has access to the Power BI workspace\n\n"
            f"**Expected report:** {title}\n\n"
            f"**Contents:** {description}",
            icon="📊",
        )
        with st.expander("🛠️  Setup guide — Managed Identity embedding"):
            st.markdown(
                """
1. In the **Azure Portal**, open your App Service → **Identity** and
   enable **System-assigned** managed identity.
2. In the **Power BI workspace** that hosts your reports, add the
   managed identity as *Member* (or *Viewer*).
3. In the **Power BI Admin Portal**, enable
   *"Service principals can use Power BI APIs"* for a security group
   containing the managed identity.
4. Set `POWERBI_*_REPORT_ID` and `POWERBI_*_GROUP_ID` in `deploy.ps1`
   and re-deploy to update App Settings.
5. Restart the app — reports will load with no sign-in required.
                """
            )
        return

    # ── Try embed-token path (no sign-in) ─────────────────
    if report_id and group_id:
        token_info = get_access_token(report_id, group_id)

        if "error" in token_info:
            # Show diagnostic error instead of silent sign-in fallback
            st.error(
                "**Power BI embed token could not be generated.**\n\n"
                + token_info["error"],
                icon="🔒",
            )
            with st.expander("Troubleshooting checklist"):
                st.markdown(
                    "1. **Managed Identity Object ID** — Azure Portal → App Service → Identity → copy Object ID\n"
                    "2. **Workspace role** — Power BI Service → Workspace → Access → add the Object ID as **Member**\n"
                    "3. **Admin setting** — Power BI Admin Portal → Tenant settings → "
                    "*'Allow service principals to use Power BI APIs'* → Enabled "
                    "(for a security group containing the MI)\n"
                    "4. **Report ID** — must be a single GUID, not a URL fragment\n"
                    "5. **Group ID** — the workspace GUID that contains the report"
                )
            return

        # Success — render with JS SDK
        page_html = _EMBED_HTML_TEMPLATE.format(
            report_id_json=_json.dumps(token_info["report_id"]),
            embed_url_json=_json.dumps(token_info["embed_url"]),
            access_token_json=_json.dumps(token_info["token"]),
        )
        st.components.v1.html(page_html, height=height, scrolling=True)
    else:
        st.warning(
            "Report ID or Group ID not configured. "
            "Set `POWERBI_*_REPORT_ID` and `POWERBI_*_GROUP_ID` in `deploy.ps1` and re-deploy."
        )


# ── Ad-hoc Explore (blank report in edit mode) ────────────────
_EXPLORE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.jsdelivr.net/npm/powerbi-client@2.23.1/dist/powerbi.min.js"></script>
  <style>
    html, body {{ margin:0; padding:0; height:100%; background:#fff; }}
    #exploreContainer {{ width:100%; height:100%; }}
    #errorBox {{ display:none; color:#c00; font-family:sans-serif; padding:1em; }}
  </style>
</head>
<body>
  <div id="exploreContainer"></div>
  <div id="errorBox"></div>
  <script>
    var models = window["powerbi-client"].models;
    var config = {{
      type: "report",
      id: {report_id_json},
      embedUrl: {embed_url_json},
      accessToken: {access_token_json},
      tokenType: models.TokenType.Embed,
      viewMode: models.ViewMode.Edit,
      permissions: models.Permissions.All,
      settings: {{
        personalizedVisuals: {{ enabled: true }},
        panes: {{
          filters: {{ expanded: true, visible: true }},
          fields: {{ expanded: true }}
        }},
        background: models.BackgroundType.Default
      }}
    }};
    var container = document.getElementById("exploreContainer");
    var report = powerbi.embed(container, config);
    report.on("error", function(event) {{
      var err = event.detail || {{}};
      var box = document.getElementById("errorBox");
      box.style.display = "block";
      box.innerText = "Power BI error: " + (err.message || JSON.stringify(err));
    }});
  </script>
</body>
</html>
"""


def render_powerbi_explore(
    explore_report_id: str,
    group_id: str,
    title: str = "Ad-hoc Analysis",
    height: int = 800,
) -> None:
    """
    Embed a blank Power BI report in edit mode.  Users can drag fields,
    create visuals, and explore the semantic model freely.
    Changes are not saved to the published report.
    """
    st.markdown(f"### \U0001f50d {title}")
    st.caption(
        "Build your own visuals by dragging fields from the data pane. "
        "Changes are not saved to the published report."
    )

    if not explore_report_id or not group_id:
        st.warning(
            "Explore report not configured. "
            "Create a blank report on the semantic model in Power BI Service, "
            "then set `POWERBI_PRICING_EXPLORE_REPORT_ID` in deploy.ps1 and re-deploy."
        )
        return

    # Get an edit-capable embed token for the blank report
    edit_info = get_edit_token(explore_report_id, group_id)
    if "error" in edit_info:
        st.error(
            "**Could not generate an edit token for ad-hoc analysis.**\n\n"
            + edit_info["error"],
            icon="\U0001f512",
        )
        return

    page_html = _EXPLORE_HTML_TEMPLATE.format(
        report_id_json=_json.dumps(edit_info["report_id"]),
        embed_url_json=_json.dumps(edit_info["embed_url"]),
        access_token_json=_json.dumps(edit_info["token"]),
    )
    st.components.v1.html(page_html, height=height, scrolling=True)
