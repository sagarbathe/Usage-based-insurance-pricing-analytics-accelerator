"""
Fabric Data Agent Chat Component.

Renders a persona-specific chat panel that connects to a
Microsoft Fabric Data Agent using the OpenAI *Assistants* API
(threads → messages → runs).  Authentication uses the App Service
Managed Identity — no API keys needed.

Reference:
  https://learn.microsoft.com/en-us/fabric/data-science/data-agent-end-to-end-tutorial
"""

import time
import uuid
import typing as t

import streamlit as st

from components.powerbi_auth import _get_credential

_FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


def _get_bearer_token() -> str | None:
    """Return a bearer token for the Fabric Data Agent API, or None."""
    try:
        credential = _get_credential()
        token = credential.get_token(_FABRIC_SCOPE)
        return token.token
    except Exception:
        return None


# ── OpenAI Assistants client wired to Fabric auth ────────────
def _build_openai_client(base_url: str):
    """
    Return an ``openai.OpenAI`` client whose ``base_url`` points at
    the Fabric Data Agent published URL and whose auth header
    carries the AAD bearer token.
    """
    from openai import OpenAI
    from openai._models import FinalRequestOptions
    from openai._types import Omit
    from openai._utils import is_given

    bearer = _get_bearer_token()
    if bearer is None:
        return None

    class _FabricOpenAI(OpenAI):
        def __init__(self, _bearer: str, **kwargs: t.Any) -> None:
            self._bearer = _bearer
            default_query = kwargs.pop("default_query", {})
            default_query["api-version"] = "2024-05-01-preview"
            super().__init__(
                api_key="not-used",
                base_url=base_url,
                default_query=default_query,
                **kwargs,
            )

        def _prepare_options(self, options: FinalRequestOptions) -> None:
            headers: dict[str, str | Omit] = (
                {**options.headers} if is_given(options.headers) else {}
            )
            options.headers = headers
            headers["Authorization"] = f"Bearer {self._bearer}"
            if "Accept" not in headers:
                headers["Accept"] = "application/json"
            if "ActivityId" not in headers:
                headers["ActivityId"] = str(uuid.uuid4())
            return super()._prepare_options(options)

    return _FabricOpenAI(_bearer=bearer)


def _call_data_agent(endpoint: str, message: str) -> str:
    """
    Send a question to a Fabric Data Agent via the OpenAI
    Assistants API and return the response text.

    Flow: create assistant → create thread → post message →
          create run → poll until complete → read reply.
    """
    client = _build_openai_client(endpoint.rstrip("/"))
    if client is None:
        return (
            "⚠️ **Authentication failed** — could not obtain a token.\n\n"
            "Ensure the App Service Managed Identity is enabled and has "
            "access to Fabric."
        )

    thread = None
    try:
        # 1 ─ Create assistant (Fabric ignores the model value)
        assistant = client.beta.assistants.create(model="not-used")

        # 2 ─ Create thread
        thread = client.beta.threads.create()

        # 3 ─ Post user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=message,
        )

        # 4 ─ Create run
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )

        # 5 ─ Poll until terminal state
        terminal_states = {"completed", "failed", "cancelled", "requires_action"}
        poll_interval = 2
        timeout_seconds = 120
        start_time = time.time()

        while run.status not in terminal_states:
            if time.time() - start_time > timeout_seconds:
                return "⚠️ **Timeout** — the Data Agent did not respond within 2 minutes."
            time.sleep(poll_interval)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id,
            )

        if run.status != "completed":
            return f"⚠️ **Data Agent run finished with status:** `{run.status}`"

        # 6 ─ Read assistant reply
        messages = client.beta.threads.messages.list(
            thread_id=thread.id,
            order="asc",
        )
        # Return the last assistant message
        for msg in reversed(messages.data):
            if msg.role == "assistant" and msg.content:
                return msg.content[0].text.value

        return "⚠️ The Data Agent returned an empty response."

    except Exception as exc:
        return f"⚠️ **Request failed:** {exc}"

    finally:
        # Clean up the thread
        if thread is not None:
            try:
                client.beta.threads.delete(thread.id)
            except Exception:
                pass


def render_data_agent_chat(
    agent_name: str,
    endpoint: str,
    suggested_prompts: list[str],
) -> None:
    """
    Render a Fabric Data Agent chat panel with conversation history
    and suggested prompt buttons.

    Parameters
    ----------
    agent_name : str
        Display name for the agent (e.g. "Pricing Copilot").
    endpoint : str
        The Data Agent REST endpoint.
    suggested_prompts : list[str]
        Example prompts shown as quick-action buttons.
    """
    st.markdown(f"### 🤖 {agent_name}")

    is_placeholder = "<YOUR_" in endpoint

    if is_placeholder:
        st.info(
            "🔗 **Fabric Data Agent placeholder**\n\n"
            "To connect a live agent:\n"
            "1. Set the `FABRIC_*_AGENT_ENDPOINT` variable in `deploy.ps1`\n"
            "2. Re-run `deploy.ps1` to update App Settings\n"
            "3. Restart the app\n\n"
            "Authentication is handled automatically via the App Service "
            "Managed Identity.",
            icon="🤖",
        )
        with st.expander("🛠️  How to set up a Fabric Data Agent"):
            st.markdown(
                """
1. In **Microsoft Fabric**, go to your workspace
2. Create a new **Data Agent** under Data Science
3. Configure it to query your Gold lakehouse tables
4. Copy the agent endpoint URL
5. Set it as `FABRIC_*_AGENT_ENDPOINT` in `deploy.ps1` and re-deploy

No API keys are needed — the app authenticates with the
App Service Managed Identity.

See: [Fabric Data Agent docs](https://learn.microsoft.com/en-us/fabric/data-science/data-agent-overview)
                """
            )

    # ── Chat session state ────────────────────────────────
    chat_key = f"chat_history_{agent_name.replace(' ', '_').lower()}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # ── Layout: chat (left, wider) | suggested prompts (right) ──
    col_chat, col_prompts = st.columns([3, 1])

    # ── Suggested prompts (right column) ──────────────────
    selected_prompt = None
    with col_prompts:
        st.markdown("**💡 Suggested questions:**")
        for i, prompt in enumerate(suggested_prompts):
            if st.button(prompt, key=f"prompt_{agent_name}_{i}", use_container_width=True):
                selected_prompt = prompt

    # ── Chat history (left column) ────────────────────────
    with col_chat:
        chat_container = st.container(height=450)
        with chat_container:
            for msg in st.session_state[chat_key]:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    # Use suggested prompt if clicked
    if selected_prompt:
        st.session_state[chat_key].append({"role": "user", "content": selected_prompt})

        with st.spinner(f"{agent_name} is thinking…"):
            response = _call_data_agent(endpoint, selected_prompt)

        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.rerun()


def render_data_agent_chat_input(agent_name: str, endpoint: str) -> None:
    """
    Render the chat input widget for the Data Agent.

    MUST be called at the top level of the page (outside st.columns,
    st.tabs, st.expander, etc.) due to Streamlit restrictions on
    st.chat_input placement.
    """
    chat_key = f"chat_history_{agent_name.replace(' ', '_').lower()}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    user_input = st.chat_input(
        f"Ask {agent_name}…",
        key=f"input_{agent_name.replace(' ', '_').lower()}",
    )

    if user_input:
        st.session_state[chat_key].append({"role": "user", "content": user_input})

        with st.spinner(f"{agent_name} is thinking…"):
            response = _call_data_agent(endpoint, user_input)

        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.rerun()
