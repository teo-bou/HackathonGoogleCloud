# Googl Cloud Hackathon – Geospatial Assistant ReforestAI

Streamlit app + an LLM agent (Google ADK) to analyze and visualize reforestation data in Madagascar. It works with GeoJSON layers for Fokontany boundaries, Grevillea plantations, and Reforestation areas.

## Features

- Interactive chat to run spatial queries and generate maps.
- Folium maps with default styling and a Stamen Terrain base map.
- Tools for attribute queries, spatial joins, geometry enrichment, and PNG/HTML exports.

## Repository Layout

- `app/streamlit_app.py` – Streamlit UI that talks to the agent over HTTP (ADK API).
- `reforestAI-agent/agent.py` – Agent definition and registered tools.
- `reforestAI-agent/tools.py` – Geospatial utilities (GeoPandas, Folium, etc.).
- `Map_Data/geojson/` – Sample GeoJSON datasets (`Fokontany.geojson`, `Grevillea.geojson`, `Reboisement.geojson`).
- `output/` – Generated artifacts (maps, images, exports).

## Prerequisites

- Python 3.10+ (3.12 recommended).
- Google API key for the LLM agent.
- GeoPandas/Fiona dependencies (already specified in `requirements.txt`).

## Setup

Create and activate a virtual environment, then install dependencies.

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure your API key:

1) Copy `reforestAI-agent/.env.example` to `reforestAI-agent/.env`  
2) Set `GOOGLE_API_KEY=<your_key>` (create one at https://aistudio.google.com/app/api-keys)

## Running

Start the ADK API server (it must listen on `http://localhost:8000` and expose the app name `reforestAI-agent`). Depending on your ADK setup, this can look like:

```bash
adk run reforestAI-agent
```

Launch the Streamlit app:

```bash
streamlit run app/streamlit_app.py
```

In the app sidebar, create a new session, then ask questions or click suggested prompts.



## Troubleshooting

- "Custom tiles must have an attribution" (Folium):
  - Use a known provider name (e.g., `CartoDB Positron`) or, if using a custom tile URL, also provide an attribution string.
- "The input token count exceeds the maximum" (400 INVALID_ARGUMENT):
  - Start a new session in Streamlit and avoid printing entire GeoJSON in responses. Ask the agent to save results to files and return only paths/summaries.
- Nothing appears on the map:
  - Check that input files exist in `Map_Data/geojson/` and that geometries are valid.


## Roadmap Ideas

- Aggregation tool for reforested area by Fokontany (year filters, CSV/choropleth export).
- Geometry validation/repair utilities.
- Richer legend/layer presets and additional basemaps.

