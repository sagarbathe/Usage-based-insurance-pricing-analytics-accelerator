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
import traceback
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
    Uses the Fabric-specific thread API endpoint.
    
    This enables conversation persistence: providing the same thread_name
    across multiple calls will reuse the same thread, maintaining conversation
    history. If thread_name is None, a unique random name is generated.
    
    Parameters
    ----------
    base_url : str
        The Data Agent REST endpoint.
    bearer_token : str
        The AAD bearer token for authentication.
    thread_name : str, optional
        Name for the thread. If None, generates a unique thread name.
        Use the same name to continue a conversation with history.
        
    Returns
    -------
    dict
        Thread information with 'id' and 'name' keys.
    """
    # Generate unique thread name if not provided
    if thread_name is None:
        thread_name = f'external-client-thread-{uuid.uuid4()}'
    
    # Adjust URL format for thread API (use Fabric's private endpoint)
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
    Send a question to a Fabric Data Agent using OpenAI Assistants API pattern.

    Flow: create assistant → get/create thread → check for in-progress runs →
          post message → create run → poll until complete → read reply.
          
    Threads are kept alive for conversation history. If a run is already in progress,
    we wait for it to complete before starting a new one.
          
    Parameters
    ----------
    endpoint : str
        The Data Agent REST endpoint.
    message : str
        The question to send to the agent.
    thread_name : str, optional
        Name for the conversation thread. If None, generates a unique random name.
        Using the same thread_name maintains conversation history.
    """
    # Build OpenAI client
    client = _build_openai_client(endpoint.rstrip("/"))
    if client is None:
        return (
            "⚠️ **Authentication failed** — could not obtain a token.\n\n"
            "Ensure the App Service Managed Identity is enabled and has "
            "access to Fabric."
        )
    
    try:
        # 1 ─ Get bearer token
        bearer_token = _get_bearer_token()
        if bearer_token is None:
            return "⚠️ **Authentication failed** — could not obtain a token."
        
        # 2 ─ Create assistant (required by Fabric Data Agents even though model is not used)
        assistant = client.beta.assistants.create(model="not used")
        
        # 3 ─ Get existing thread or create new one using Fabric's private API
        thread_info = _get_existing_or_create_new_thread(endpoint, bearer_token, thread_name)
        thread_id = thread_info['id']

        # 4 ─ Check for any in-progress runs and wait for them to complete
        try:
            runs = client.beta.threads.runs.list(thread_id=thread_id, limit=5)
            for existing_run in runs.data:
                if existing_run.status in ["queued", "in_progress"]:
                    print(f"⏳ Waiting for existing run {existing_run.id} to complete...")
                    # Wait for the existing run to complete
                    wait_start = time.time()
                    while existing_run.status in ["queued", "in_progress"]:
                        if time.time() - wait_start > 30:  # Wait max 30 seconds for existing run
                            # Cancel the stuck run
                            try:
                                client.beta.threads.runs.cancel(thread_id=thread_id, run_id=existing_run.id)
                                print(f"⚠️ Cancelled stuck run {existing_run.id}")
                            except Exception as cancel_error:
                                print(f"⚠️ Could not cancel run: {cancel_error}")
                            break
                        time.sleep(2)
                        existing_run = client.beta.threads.runs.retrieve(
                            thread_id=thread_id,
                            run_id=existing_run.id
                        )
        except Exception as check_error:
            # If checking runs fails, log but continue - might be first run on thread
            print(f"⚠️ Could not check existing runs: {check_error}")

        # 5 ─ Post user message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message,
        )

        # 6 ─ Create run with the assistant we created
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant.id,
        )

        # 7 ─ Poll until terminal state
        terminal_states = {"completed", "failed", "cancelled", "requires_action"}
        poll_interval = 2
        timeout_seconds = 120
        start_time = time.time()

        while run.status not in terminal_states:
            if time.time() - start_time > timeout_seconds:
                # Try to cancel the run on timeout
                try:
                    client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run.id)
                    print(f"⚠️ Cancelled run {run.id} due to timeout")
                except Exception as cancel_error:
                    print(f"⚠️ Could not cancel run: {cancel_error}")
                return "⚠️ **Timeout** — the Data Agent did not respond within 2 minutes."
            time.sleep(poll_interval)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        if run.status != "completed":
            # Display detailed error information
            error_details = f"⚠️ **Data Agent run finished with status:** `{run.status}`\n\n"
            error_details += f"**Run ID:** `{run.id}`\n"
            error_details += f"**Thread ID:** `{thread_id}`\n"
            error_details += f"**Assistant ID:** `{assistant.id}`\n\n"
            
            if hasattr(run, 'last_error') and run.last_error:
                error_details += f"**Error Details:**\n"
                error_details += f"- **Code:** `{run.last_error.code if hasattr(run.last_error, 'code') else 'N/A'}`\n"
                error_details += f"- **Message:** {run.last_error.message if hasattr(run.last_error, 'message') else 'N/A'}\n"
            else:
                error_details += "**Error Details:** No error information available\n"
            
            return error_details

        # 8 ─ Read assistant reply
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
        )
        
        # Get the response - thread is kept alive for conversation history
        for msg in reversed(messages.data):
            if msg.role == "assistant" and msg.content:
                return msg.content[0].text.value

        return "⚠️ The Data Agent returned an empty response."

    except Exception as exc:
        # Display detailed exception information
        error_msg = f"⚠️ **Request failed**\n\n"
        error_msg += f"**Exception Type:** `{type(exc).__name__}`\n"
        error_msg += f"**Error Message:** {str(exc)}\n\n"
        error_msg += f"**Stack Trace:**\n```\n{traceback.format_exc()}\n```"
        return error_msg


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
    
    # Generate unique session-specific thread ID (one per browser session)
    thread_id_key = "_data_agent_session_id"
    if thread_id_key not in st.session_state:
        st.session_state[thread_id_key] = str(uuid.uuid4())
    
    # ── Check if ANY agent is processing (global lock with timeout) ──
    # Clear stale locks (older than 5 minutes) - happens when page navigation interrupts processing
    lock_timeout = 300  # 5 minutes in seconds
    lock_timestamp = st.session_state.get("agent_processing_timestamp", 0)
    if time.time() - lock_timestamp > lock_timeout:
        st.session_state["agent_processing"] = False
        st.session_state["processing_agent_name"] = ""
        st.session_state["agent_processing_timestamp"] = 0
    
    is_processing = st.session_state.get("agent_processing", False)
    processing_agent = st.session_state.get("processing_agent_name", "")

    # ── Layout: chat (left, wider) | suggested prompts (right) ──
    col_chat, col_prompts = st.columns([3, 1])

    # ── Suggested prompts (right column) ──────────────────
    selected_prompt = None
    with col_prompts:
        st.markdown("**💡 Suggested questions:**")
        if is_processing:
            st.info(f"⏳ **{processing_agent}** is processing...")
            # Show text placeholders instead of buttons when processing
            for i, prompt in enumerate(suggested_prompts):
                st.markdown(f"""
                    <div style="
                        padding: 0.5rem 1rem;
                        border: 1px solid #ddd;
                        border-radius: 0.5rem;
                        text-align: center;
                        background-color: #f0f0f0;
                        color: #999;
                        margin-bottom: 0.5rem;
                        opacity: 0.5;
                        cursor: not-allowed;
                    ">{prompt}</div>
                """, unsafe_allow_html=True)
        else:
            # Only render clickable buttons when NOT processing
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
        
        # Chat input at the bottom of the column
        user_input = st.chat_input(
            f"Ask {agent_name}…" if not is_processing else f"🔒 {processing_agent} is processing...",
            key=f"input_{agent_name.replace(' ', '_').lower()}",
            disabled=is_processing,
        )

        if user_input:
            # Double-check: if another agent started processing after input was submitted, ignore
            if st.session_state.get("agent_processing", False):
                st.warning(f"⏳ Please wait, **{st.session_state.get('processing_agent_name', 'another agent')}** is still processing...")
            else:
                # Set global processing lock IMMEDIATELY with timestamp
                st.session_state["agent_processing"] = True
                st.session_state["processing_agent_name"] = agent_name
                st.session_state["agent_processing_timestamp"] = time.time()
                
                # Store pending query instead of processing immediately
                pending_query_key = f"_pending_query_{agent_name.replace(' ', '_').lower()}"
                st.session_state[pending_query_key] = user_input
                
                # Rerun to show updated UI with lock state
                st.rerun()

    # Use suggested prompt if clicked
    if selected_prompt:
        # Double-check: if another agent started processing after button render, ignore
        if st.session_state.get("agent_processing", False):
            st.warning(f"⏳ Please wait, **{st.session_state.get('processing_agent_name', 'another agent')}** is still processing...")
            return
        
        # Set global processing lock IMMEDIATELY with timestamp
        st.session_state["agent_processing"] = True
        st.session_state["processing_agent_name"] = agent_name
        st.session_state["agent_processing_timestamp"] = time.time()
        
        # Store pending query instead of processing immediately
        # This allows UI to update (show placeholders) before API call blocks
        pending_query_key = f"_pending_query_{agent_name.replace(' ', '_').lower()}"
        st.session_state[pending_query_key] = selected_prompt
        
        # Rerun to show updated UI with lock state
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
    
    # Ensure session ID exists
    thread_id_key = "_data_agent_session_id"
    if thread_id_key not in st.session_state:
        st.session_state[thread_id_key] = str(uuid.uuid4())
    
    # Check if any agent is processing (with timeout check)
    lock_timeout = 300  # 5 minutes
    lock_timestamp = st.session_state.get("agent_processing_timestamp", 0)
    if time.time() - lock_timestamp > lock_timeout:
        st.session_state["agent_processing"] = False
        st.session_state["processing_agent_name"] = ""
        st.session_state["agent_processing_timestamp"] = 0
    
    is_processing = st.session_state.get("agent_processing", False)
    processing_agent = st.session_state.get("processing_agent_name", "")

    user_input = st.chat_input(
        f"Ask {agent_name}…" if not is_processing else f"🔒 {processing_agent} is processing...",
        key=f"input_{agent_name.replace(' ', '_').lower()}",
        disabled=is_processing,
    )

    if user_input:
        # Double-check: if another agent started processing after input was submitted, ignore
        if st.session_state.get("agent_processing", False):
            st.warning(f"⏳ Please wait, **{st.session_state.get('processing_agent_name', 'another agent')}** is still processing...")
            return
        
        # Set global processing lock IMMEDIATELY with timestamp
        st.session_state["agent_processing"] = True
        st.session_state["processing_agent_name"] = agent_name
        st.session_state["agent_processing_timestamp"] = time.time()
        
        # Store pending query instead of processing immediately
        pending_query_key = f"_pending_query_{agent_name.replace(' ', '_').lower()}"
        st.session_state[pending_query_key] = user_input
        
        # Rerun to show updated UI with lock state
        st.rerun()


def process_pending_queries() -> None:
    """
    Process any pending data agent queries.
    
    MUST be called at the end of the page after all agents have rendered.
    This ensures all agents show the locked state before any query processing begins.
    """
    # Check all possible agents for pending queries
    for key in list(st.session_state.keys()):
        if key.startswith("_pending_query_") and st.session_state.get(key):
            # Extract agent name from key
            agent_suffix = key.replace("_pending_query_", "")
            
            # Find the agent's details
            chat_key = f"chat_history_{agent_suffix}"
            pending_query = st.session_state[key]
            st.session_state[key] = None  # Clear pending query
            
            # Get agent name from processing_agent_name (set when lock was created)
            agent_name = st.session_state.get("processing_agent_name", "Agent")
            
            # Find endpoint by checking DATA_AGENTS config
            from config import DATA_AGENTS
            endpoint = None
            for agent_config in DATA_AGENTS.values():
                if agent_config["name"].replace(' ', '_').lower() == agent_suffix:
                    endpoint = agent_config["endpoint"]
                    break
            
            if not endpoint:
                st.error(f"Could not find endpoint for agent: {agent_name}")
                st.session_state["agent_processing"] = False
                st.session_state["processing_agent_name"] = ""
                st.session_state["agent_processing_timestamp"] = 0
                st.rerun()
                return
            
            # Process the query
            st.session_state[chat_key].append({"role": "user", "content": pending_query})
            
            try:
                with st.spinner(f"{agent_name} is thinking…"):
                    session_id = st.session_state.get("_data_agent_session_id", str(uuid.uuid4()))
                    thread_name = f"{agent_suffix}_session_{session_id}"
                    response = _call_data_agent(endpoint, pending_query, thread_name)
                
                st.session_state[chat_key].append({"role": "assistant", "content": response})
            except Exception as e:
                st.session_state[chat_key].append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
            finally:
                # Clear processing lock and timestamp
                st.session_state["agent_processing"] = False
                st.session_state["processing_agent_name"] = ""
                st.session_state["agent_processing_timestamp"] = 0
            
            # Rerun to show results
            st.rerun()
            return  # Only process one at a time
