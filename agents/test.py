import json
import requests
import os
import time
import uuid

# Constants
API_BASE_URL = os.getenv(
    "API_BASE_URL", "https://reforestai-agent-396062328299.europe-west9.run.app"
)
APP_NAME = os.getenv("APP_NAME", "reforestAI-agent")
BUCKET_NAME = "reforestai-bucket"

user_id = f"user-{uuid.uuid4()}"

session_id = f"session-{int(time.time())}"
response = requests.post(
    f"{API_BASE_URL}/apps/{APP_NAME}/users/{user_id}/sessions/{session_id}",
    headers={"Content-Type": "application/json"},
    data=json.dumps({}),
)
session_state = {}
if response.status_code == 200:
    session_state["session_id"] = session_id
    session_state["messages"] = []
    session_state["audio_files"] = []
    print("Session created successfully")
response = requests.post(
    f"{API_BASE_URL}/run",
    headers={"Content-Type": "application/json"},
    data=json.dumps(
        {
            "app_name": APP_NAME,
            "user_id": user_id,
            "session_id": session_state["session_id"],
            "new_message": {"role": "user", "parts": [{"text": "Hello, world!"}]},
        }
    ),
)
print(response.status_code)
print(response.text)
