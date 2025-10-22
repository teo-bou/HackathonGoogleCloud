from google.adk.agents.llm_agent import Agent
from .helpers import register_tool
from .tools import find_file_tool, geopandas_attributes_tool, geopandas_query_tool, geopandas_plot_tool


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="A helpful assistant for user questions.",
    instruction="Answer user questions to the best of your knowledge",
)


# register the tool so the agent can call it
register_tool(
    root_agent,
    name="find_file",
    func=find_file_tool,
    description=(
        "Search for files under a directory. Args: start_path(str, optional), "
        "filename_pattern(str, glob-style, optional), max_results(int, optional), recursive(bool, optional). "
        "Returns matching file paths and count."
    ),
)


# Register the tool with the agent using a defensive helper
register_tool(
    root_agent,
    name="geopandas_query",
    func=geopandas_query_tool,
    description=(
        "Execute an attribute query (pandas .query syntax) on a vector file and return GeoJSON. "
        "Args: shapefile_path(str), query(str), max_results(int, optional)."
    ),
)

register_tool(
    root_agent,
    name="geopandas_attributes",
    func=geopandas_attributes_tool,
    description=(
        "Read attribute schema and sample records from a vector file. "
        "Args: shapefile_path(str), max_sample_rows(int, optional). "
        "Returns columns, dtypes, crs, count, and sample records (geometry excluded)."
    ),
)

register_tool(
    root_agent,
    name="geopandas_plot",
    func=geopandas_plot_tool,
    description=(
        "Plot the geometries from one or more shapefiles and save the plot as a PNG image." 
        "Args: shapefile_paths(list[str]), output_image_path(str), title(str, optional)."
        "Returns the path to the saved image on success."
    ),
)
