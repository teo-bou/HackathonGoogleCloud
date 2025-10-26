from google.adk.agents.llm_agent import Agent
from .prompts import instructions

from .tools import (
    query_geojson,
    combine_multiple_geojson,
    transform_geojson,
    geojson_to_png,
    list_file_in_map_data_directory,
    select_by_geometry,
    enrich_geometry_fields,
)


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="ReforestAI agent to assist with geospatial data analysis tasks.",
    instruction=instructions,
    tools=[
        geojson_to_png,
        combine_multiple_geojson,
        list_file_in_map_data_directory,
        transform_geojson,
        query_geojson,
        select_by_geometry,
        enrich_geometry_fields,
    ],
)
