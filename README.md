# 🌳 ReforestAI – Geospatial Assistant  
### *Google Cloud Hackathon Project*

> 🛰️ A Streamlit app powered by an LLM Agent (Google ADK) to **analyze, query, and visualize reforestation data in Madagascar** using geospatial intelligence, in order to **support the NGO Interaide in their reforestation and sustainable development mission**.
---

## 🌍 Overview

ReforestAI combines **AI-powered geospatial reasoning** and **interactive mapping** to support reforestation analysis.  
It integrates:
- 🗺️ **GeoJSON layers** (Fokontany boundaries, Grevillea plantations, Reforestation zones)
- 🤖 **Google ADK Agent** for natural language queries
- 📊 **Folium maps** for beautiful visualizations

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

### Local (sans Docker)
- 🐍 **Python 3.10+** (3.12 recommandé)  
- 🔑 **Google API Key** pour l’agent LLM  
- 📦 Dépendances dans `requirements.txt` (GeoPandas, Fiona, Folium, etc.)

### Docker
- 🐳 **Docker** 20.10+  
- 🧩 **Docker Compose** v2+

> 💡 Sous Windows, utilise Docker Desktop ; sous Linux/macOS, installe Docker Engine + Compose Plugin.

---

## 🧰 Setup (Local)

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

1️⃣ Copier l’exemple d’environnement :
```bash
cp reforestAI-agent/.env.example reforestAI-agent/.env
```

2️⃣ Ajouter la clé :
```
GOOGLE_API_KEY=<your_key>
```
> Crée une clé sur [Google AI Studio](https://aistudio.google.com/app/api-keys)

---

## 🚀 Running (Local)

### 1) Lancer le serveur ADK
```bash
adk run reforestAI-agent
```
> Le serveur doit écouter `http://localhost:8000` et exposer l’app `reforestAI-agent`.

### 2) Lancer l’app Streamlit
```bash
streamlit run app/streamlit_app.py
```

Dans la sidebar, crée une session puis utilise les prompts proposés.

---

## 🐳 Running with Docker

### Structure fournie
Le dépôt inclut un `Dockerfile` (app) et un `docker-compose.yml` orchestrant :
- `agent` : le serveur Google ADK  
- `web` : l’interface Streamlit  
- un volume pour `output/` afin de récupérer les cartes exportées

> **Variables d’environnement** : assure-toi que `reforestAI-agent/.env` contient `GOOGLE_API_KEY`.

### 1) Build & Run
```bash
docker compose up --build
```

### 2) Accès à l’application
- Streamlit (web UI) : http://localhost:8501  

## 🧠 Example Queries

- “Show me a map of the Antavibe with grevillea patches on the Antavibe Fokonany.”  
- “Generate a map that includes only the 'Reboisement' and 'Grevillea' layers restricted to the Ambalona Fokontany region.”  
- “List me the Fokontanys in the Sandrohy Commune.”
- "Show me a map of Grevillea plantations where the surface area is greater than 5000 m²."  

---

## 🧩 Tech Stack

| Layer | Technology |
|------|------------|
| 🌐 Frontend | Streamlit |
| 🧠 Agent Framework | Google ADK |
| 🗺️ Geospatial | GeoPandas, Folium, Shapely, Fiona |
| 💾 Data | GeoJSON |
| 🔌 API | HTTP (Agent @ `:8000`) |
| 🐳 Runtime | Docker & Docker Compose |
| 🧰 Langage | Python 3.12 |

---

## 🌐 Online Deployment

The app is live and accessible online! 🚀  

You can explore the interactive interface and test the LLM agent directly here:  
👉 **[https://reforestai.streamlit.app]( https://reforestai-agent-front-396062328299.europe-west9.run.app/)** 

---

⭐ *If you like this project, give it a star on GitHub!* ⭐
