# 🌳 ReforestAI – Geospatial Assistant

### _Google Cloud Hackathon Project_

> 🛰️ A Streamlit app powered by an LLM Agent (Google ADK) to **analyze, query, and visualize reforestation data in Madagascar**, in order to **support the NGO Interaide in their reforestation and sustainable development mission**.

---

## 🌍 Overview

ReforestAI combines **AI-powered geospatial reasoning** and **interactive mapping** to support reforestation analysis.  
It integrates:

- 🗺️ **GeoJSON layers** (Fokontany boundaries, Grevillea plantations, Reforestation zones)
- 🤖 **Google ADK Agent** for natural language queries
- 📊 **Folium maps** for beautiful visualizations

---

## 🎬 Demo

Watch a quick demo of the ReforestAI agent in action.
See the demo at `demo.mp4`

---

## ✨ Features

✅ Interactive **chat interface** to run spatial and attribute queries  
✅ **Dynamic Folium maps** with Stamen Terrain base layer  
✅ Tools for:

- Spatial joins & geometry enrichment
- Attribute filtering
- Map export to PNG/HTML

---

## 🗂️ Repository Structure

```plaintext
📦 ReforestAI
 ┣ 📂 app/
 ┃ ┗ 📜 streamlit_app.py        → Streamlit frontend (UI + API calls)
 ┣ 📂 reforestAI-agent/
 ┃ ┣ 📜 agent.py                → LLM Agent definition (Google ADK)
 ┃ ┗ 📜 tools.py                → Geospatial utilities (GeoPandas, Folium)
 ┣ 📂 Map_Data/geojson/         → Sample GeoJSON datasets
 ┃ ┣ 📜 Fokontany.geojson
 ┃ ┣ 📜 Grevillea.geojson
 ┃ ┗ 📜 Reboisement.geojson
 ┣ 📂 output/                   → Generated maps & exports
 ┣ 📜 requirements.txt
 ┗ 📜 README.md
```

---

## ⚙️ Prerequisites

### Local (without Docker)

- 🐍 **Python 3.10+** (3.12 recommended)
- 🔑 **Google API Key** for the LLM agent
- 📦 Dependencies listed in `requirements.txt` (GeoPandas, Fiona, Folium, etc.)

### Docker

- 🐳 **Docker** 20.10+
- 🧩 **Docker Compose** v2+

> 💡 On Windows, use Docker Desktop. On Linux/macOS, install Docker Engine + Compose Plugin.

---

## 🧰 Local Setup

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🔐 API Configuration

1️⃣ Copy the example environment file:

```bash
cp reforestAI-agent/.env.example reforestAI-agent/.env
```

2️⃣ Add your API key:

```
GOOGLE_API_KEY=<your_key>
```

> You can create an API key at [Google AI Studio](https://aistudio.google.com/app/api-keys)

---

## 🚀 Running (Local)

### 1) Start the ADK server

```bash
adk api_server
```

> The server must listen on `http://localhost:8000` and expose the app `reforestAI-agent`.

### 2) Launch the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

In the sidebar, create a session and start exploring spatial data through chat prompts.

---

## 🐳 Running with Docker

### Provided structure

The repository includes a `Dockerfile` (for the app) and a `docker-compose.yml` orchestrating:

- `agent` : Google ADK server
- `web` : Streamlit web interface
- A volume for `output/` to retrieve exported maps

> **Environment variables**: ensure `reforestAI-agent/.env` contains your `GOOGLE_API_KEY`.

### 1) Build & Run

```bash
docker compose up --build
```

### 2) Access the application

- Streamlit (Web UI): http://localhost:8501

## 🧠 Example Queries

- “Show me a map of the Antavibe with grevillea patches on the Antavibe Fokonany.”
- “Generate a map that includes only the 'Reboisement' and 'Grevillea' layers restricted to the Ambalona Fokontany region.”
- “List me the Fokontanys in the Sandrohy Commune.”
- "Show me a map of Grevillea plantations where the surface area is greater than 5000 m²."

---

## 🧩 Tech Stack

| Layer              | Technology                        |
| ------------------ | --------------------------------- |
| 🌐 Frontend        | Streamlit                         |
| 🧠 Agent Framework | Google ADK                        |
| 🗺️ Geospatial      | GeoPandas, Folium, Shapely, Fiona |
| 💾 Data            | GeoJSON                           |
| 🔌 API             | HTTP (Agent @ `:8000`)            |
| 🐳 Runtime         | Docker & Docker Compose           |
| 🧰 Language        | Python 3.12                       |

---

## 🌐 Online Deployment

The app is live and accessible online! 🚀

You can explore the interactive interface and test the LLM agent directly here:  
👉 **[https://reforestai-agent-front-396062328299.europe-west9.run.app/](https://reforestai-agent-front-396062328299.europe-west9.run.app/)**

> 💡 The online version uses the same ADK Agent backend and geospatial datasets but may have limited export capabilities.

---

⭐ _If you like this project, give it a star on GitHub!_ ⭐
