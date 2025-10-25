import streamlit as st
import requests
import json
import os
import uuid
import time
from pathlib import Path


# Set page config
st.set_page_config(
    page_title="ReforestAI Agent Chat", page_icon="🌲", layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "reforestAI-agent"
REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    response = requests.post(
        f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({}),
    )

    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        st.session_state.audio_files = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
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
        # Look for geojson_to_png function response to extract image file path
        if parts and isinstance(parts[0], dict) and "functionResponse" in parts[0]:
            func_response = parts[0]["functionResponse"]
            if func_response.get("name") == "geojson_to_png":
                response_content = (
                    func_response.get("response", {})
                    .get("message", [])
                    .get("file saved as:", None)
                )
                if response_content:
                    png_path = response_content

    # Add assistant response to chat (include png_path even if None)
    if assistant_message:
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_message, "png_path": png_path}
        )

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
# Input for new messages
if st.session_state.session_id:  # Only show input if session exists
    user_input = st.chat_input("Type your message...")
    if user_input:
        send_message(user_input)
        st.rerun()  # Rerun to update the UI with new messages
else:
    st.info("👈 Create a session to start chatting")
