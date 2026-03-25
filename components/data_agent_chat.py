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

import requests
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


def _get_existing_or_create_new_thread(base_url: str, bearer_token: str, thread_name: str = None) -> dict:
    """
    Get an existing thread or create a new thread for the Fabric Data Agent.
    
    This method ensures proper thread management by either retrieving an existing
    thread with the given name or creating a new one if it doesn't exist.
    
    Parameters
    ----------
    base_url : str
        The Data Agent REST endpoint (will be modified to access thread API).
    bearer_token : str
        The AAD bearer token for authentication.
    thread_name : str, optional
        Name for the thread. If None, generates a unique thread name (creates new thread each time).
        
    Returns
    -------
    dict
        Thread information with 'id' and 'name' keys.
    """
    # Generate unique thread name if not provided (ensures new thread per request)
    if thread_name is None:
        thread_name = f'external-client-thread-{uuid.uuid4()}'
    
    # Adjust URL format for thread API
    if "aiskills" in base_url:
        thread_api_base = base_url.replace("aiskills", "dataagents").removesuffix("/openai").replace("/aiassistant", "/__private/aiassistant")
    else:
        thread_api_base = base_url.removesuffix("/openai").replace("/aiassistant", "/__private/aiassistant")
    
    get_thread_url = f'{thread_api_base}/threads/fabric?tag="{thread_name}"'
    
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "ActivityId": str(uuid.uuid4())
    }
    
    response = requests.get(get_thread_url, headers=headers)
    response.raise_for_status()
    
    thread = response.json()
    thread["name"] = thread_name  # Add thread name to returned object
    
    return thread


def _call_data_agent(endpoint: str, message: str, thread_name: str = None) -> str:
    """
    Send a question to a Fabric Data Agent via the OpenAI
    Assistants API and return the response text.

    Flow: get/create thread → create assistant → post message →
          create run → poll until complete → read reply.
          
    Parameters
    ----------
    endpoint : str
        The Data Agent REST endpoint.
    message : str
        The question to send to the agent.
    thread_name : str, optional
        Name for the conversation thread. If provided, reuses existing thread.
        If None, creates a new unique thread for each call.
    """
    client = _build_openai_client(endpoint.rstrip("/"))
    if client is None:
        return (
            "⚠️ **Authentication failed** — could not obtain a token.\n\n"
            "Ensure the App Service Managed Identity is enabled and has "
            "access to Fabric."
        )

    try:
        # 1 ─ Get bearer token for thread API
        bearer_token = _get_bearer_token()
        
        # 2 ─ Get existing thread or create new one
        thread_info = _get_existing_or_create_new_thread(endpoint, bearer_token, thread_name)
        thread_id = thread_info['id']
        
        # 3 ─ Create assistant (Fabric ignores the model value)
        assistant = client.beta.assistants.create(model="not-used")

        # 4 ─ Post user message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message,
        )

        # 5 ─ Create run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id,
        )

        # 6 ─ Poll until terminal state
        terminal_states = {"completed", "failed", "cancelled", "requires_action"}
        poll_interval = 2
        timeout_seconds = 120
        start_time = time.time()

        while run.status not in terminal_states:
            if time.time() - start_time > timeout_seconds:
                return "⚠️ **Timeout** — the Data Agent did not respond within 2 minutes."
            time.sleep(poll_interval)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        if run.status != "completed":
            return f"⚠️ **Data Agent run finished with status:** `{run.status}`"

        # 7 ─ Read assistant reply
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
        )
        # Return the last assistant message
        for msg in reversed(messages.data):
            if msg.role == "assistant" and msg.content:
                return msg.content[0].text.value

        return "⚠️ The Data Agent returned an empty response."

    except Exception as exc:
        return f"⚠️ **Request failed:** {exc}"


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
            # Use agent_name as thread identifier for conversation persistence
            thread_name = agent_name.replace(' ', '_').lower()
            response = _call_data_agent(endpoint, selected_prompt, thread_name)

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
            # Use agent_name as thread identifier for conversation persistence
            thread_name = agent_name.replace(' ', '_').lower()
            response = _call_data_agent(endpoint, user_input, thread_name)

        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.rerun()
