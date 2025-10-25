from google.adk.agents.llm_agent import Agent
from .prompts import instructions

from .tools import (
    query_geojson,
    combine_multiple_geojson,
    shapefile_to_geojson,
    geojson_to_png,
    list_file_in_map_data_directory,
)


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="ReforestAI agent to assist with geospatial data analysis tasks.",
    instruction=instructions,
    tools=[
        shapefile_to_geojson,
        geojson_to_png,
        combine_multiple_geojson,
        list_file_in_map_data_directory,
        query_geojson,
    ],
)
