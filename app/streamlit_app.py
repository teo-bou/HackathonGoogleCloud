import streamlit as st
import requests
import json
import os
import uuid
import time
from pathlib import Path
# from .streamlit_test import make_folium_map, REPO_GEOJSON_DIR

import streamlit.components.v1 as components
from pathlib import Path
import json


# Set page config
st.set_page_config(
    page_title="ReforestAI Agent Chat", page_icon="🌲", layout="centered"
)

# Constants
API_BASE_URL = os.environ.get("API_BASE_URL", "http://reforestai_api:8000")
APP_NAME = "reforestAI-agent"
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Suggested questions defined at the top so the UI can take them from a single source
SUGGESTED_QUESTIONS = [
    "Who are you ?",
    "What is a Fokontany or Grevillea ?",
    "Show me a map of the Antavibe with grevillea patches on the Antavibe Fokonany.",
    "List me the Fokontanys.",
]

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_files" not in st.session_state:
    st.session_state.audio_files = []


def create_session():
    """
    Create a new session with the speaker agent.

    This function:
    1. Generates a unique session ID based on timestamp
    2. Sends a POST request to the ADK API to create a session
    3. Updates the session state variables if successful

    Returns:
        bool: True if session was created successfully, False otherwise

    API Endpoint:
        POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
    """
    session_id = f"session-{int(time.time())}"
    url = f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}"

    # Try a few times in case the API container isn't ready yet (common in compose)
    max_retries = 6
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({}),
                timeout=5,
            )
        except requests.exceptions.RequestException as e:
            # Connection refused or other network error — retry with backoff
            wait = attempt * 1
            st.warning(f"Attempt {attempt}/{max_retries}: API not reachable at {API_BASE_URL} (error: {e}). Retrying in {wait}s...")
            time.sleep(wait)
            continue


        if response.status_code == 200:
            st.session_state.session_id = session_id
            st.session_state.messages = []
            st.session_state.audio_files = []
            return True
        else:
            st.error(f"Failed to create session: {response.status_code} {response.text}")
            return False

    # If we exhausted retries
    st.error(f"Could not reach API at {API_BASE_URL} after {max_retries} attempts. Is the API container running and reachable from this Streamlit instance?")
    return False



def send_message(message):
    """
    Send a message to the speaker agent and process the response.
    ...
    """
    if not st.session_state.session_id:
        st.error("No active session. Please create a session first.")
        return False

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})

    # Send message to API
    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps(
            {
                "app_name": APP_NAME,
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "new_message": {"role": "user", "parts": [{"text": message}]},
            }
        ),
    )

    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False

    # Process the response
    events = response.json()

    # Extract assistant's text response
    assistant_message = None
    png_path = None  # ensure this variable always exists
    folium_html_path = None
    folium_layers_payload = None

    for event in events:
        content = event.get("content", {})
        parts = (
            content.get("parts", [])
            if isinstance(content.get("parts", []), list)
            else []
        )

        # Look for the final text response from the model
        if (
            content.get("role") == "model"
            and parts
            and isinstance(parts[0], dict)
            and "text" in parts[0]
        ):
            assistant_message = parts[0]["text"]
        # Look for functionResponse objects and extract known artifacts
        if parts and isinstance(parts[0], dict) and "functionResponse" in parts[0]:
            func_response = parts[0]["functionResponse"]
            # geojson_to_png (existing behaviour)
            if func_response.get("name") == "geojson_to_png":
                response_content = (
                    func_response.get("response", {})
                    .get("message", [])
                    .get("file saved as:", None)
                )
                if response_content:
                    png_path = response_content

            # folium_show_layers: agent returns an HTML map path and/or the layers payload
            if func_response.get("name") == "folium_show_layers":
                resp = func_response.get("response", {}) or {}
                # Try common locations for the html_path
                html_path = resp.get("html_path")
                if not html_path:
                    # sometimes nested under 'message' or 'data'
                    msg_part = resp.get("message")
                    if isinstance(msg_part, dict):
                        html_path = msg_part.get("html_path")
                    if not html_path and isinstance(resp.get("data"), dict):
                        html_path = resp.get("data", {}).get("html_path")

                folium_html_path = html_path
                # keep full layers payload as fallback (the agent may return layers)
                folium_layers_payload = resp.get("layers") or (
                    msg_part.get("layers") if isinstance(msg_part, dict) else None
                )

    # Add assistant response to chat (include png_path and folium info if present)
    if assistant_message:
        msg_entry = {
            "role": "assistant",
            "content": assistant_message,
            "png_path": png_path,
        }
        if folium_html_path:
            msg_entry["folium_html_path"] = folium_html_path
        if folium_layers_payload:
            # store payload so Streamlit can render locally if HTML file isn't available
            msg_entry["layers"] = folium_layers_payload
        st.session_state.messages.append(msg_entry)

    return True


# UI Components
st.title("🌲 ReforestAI Agent Chat")

# Sidebar for session management
with st.sidebar:
    st.header("Session Management")

    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session"):
            create_session()
    else:
        st.warning("No active session")
        if st.button("➕ Create Session"):
            create_session()

    st.divider()
    st.caption("This app interacts with the Speaker Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Chat interface
st.subheader("Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

            # Handle image if available
            if "png_path" in msg and msg["png_path"]:
                png_path = msg["png_path"]
                # Normalize into an absolute Path. If the agent returned a relative path
                # or a path inside the repo (e.g. "output/xxx.png"), resolve it against REPO_ROOT.
                p = Path(png_path)
                if not p.is_absolute():
                    p = REPO_ROOT / png_path
                # As a safety, also check inside the canonical OUTPUT_DIR
                if not p.exists():
                    p = OUTPUT_DIR / p.name

                if p.exists():
                    st.image(str(p))
                else:
                    st.warning(f"Image file not accessible: {p}")
            # Handle Folium HTML map if available
            if "folium_html_path" in msg and msg["folium_html_path"]:
                html_path = msg["folium_html_path"]
                p = Path(html_path)
                if not p.is_absolute():
                    p = REPO_ROOT / html_path
                if not p.exists():
                    p = OUTPUT_DIR / p.name

                if p.exists():
                    try:
                        html = p.read_text(encoding="utf-8")
                        components.html(html, height=700, scrolling=True)
                    except Exception as e:
                        st.error(f"Failed to read/display Folium HTML: {e}")
                else:
                    st.warning(f"Folium HTML file not accessible: {p}")
# Input for new messages
if st.session_state.session_id:  # Only show input if session exists
    # Suggested question buttons (take first 4 from the top-level array)
    with st.expander("Suggested questions", expanded=True):
        cols = st.columns(4)
        for i in range(4):
            try:
                q = SUGGESTED_QUESTIONS[i]
            except IndexError:
                q = None
            if q:
                if cols[i].button(q, key=f"suggest_{i}"):
                    send_message(q)
                    st.rerun()

    user_input = st.chat_input("Type your message...")
    if user_input:
        send_message(user_input)
        st.rerun()  # Rerun to update the UI with new messages
else:
    st.info("👈 Create a session to start chatting")
