import geopandas as gpd
from .helpers import _sanitize_value
from typing import List, Dict, Any
import base64
import json
import os


def shapefile_to_geojson(shapefile_path: str):
    """
    Convert a shapefile to GeoJSON format.
    Returns a dict with either 'geojson' on success, or 'error' on failure.
    """
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        return {"status": "error", "message": f"failed to read shapefile: {e}"}

    try:
        geojson_str = gdf.to_json()
        geojson_dict = json.loads(geojson_str)
    except Exception as e:
        return {
            "status": "error",
            "message": f"failed to serialize to GeoJSON: {e}",
        }

    return {"status": "success", "data": _sanitize_value(geojson_dict)}


def list_file_in_map_data_directory():
    """
    List all files in the 'Map_Data' directory.
    """
    import os

    base_path = "map_data"
    files = []
    for entry in os.scandir(base_path):
        if entry.is_file():
            files.append(entry.name)
    return {"status": "success", "files": files}


def combine_multiple_geojson(geojson_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine multiple GeoJSON FeatureCollections into a single FeatureCollection.
    Args:
        geojson_list (list[dict]): List of GeoJSON dicts to combine.
    Returns:
        dict: Combined GeoJSON FeatureCollection.
    """
    if geojson_list is None:
        return {"status": "error", "message": "geojson_list is None"}

    if not isinstance(geojson_list, list):
        return {"status": "error", "message": "expected geojson_list to be a list"}

    combined_features = []
    for geojson in geojson_list:
        if (
            isinstance(geojson, dict)
            and geojson.get("type") == "FeatureCollection"
            and "features" in geojson
        ):
            combined_features.extend(geojson["features"])

    combined_geojson = {
        "type": "FeatureCollection",
        "features": combined_features,
    }
    return {"status": "success", "data": combined_geojson}


def query_geojson(geojson: dict, query: str):
    """
    Execute a pandas-style query on a GeoJSON FeatureCollection using geopandas.
    Args:
        geojson (dict): GeoJSON FeatureCollection as a dict.
        query (str): Geopandas-style query string.
    Returns:
        dict: Resulting GeoJSON FeatureCollection after applying the query.
    """
    try:
        gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    except Exception as e:
        return {"status": "error", "message": f"failed to read GeoJSON: {e}"}

    try:
        result = gdf.query(query)
    except Exception as e:
        return {"status": "error", "message": f"failed to execute query: {e}"}

    if result.empty:
        return {
            "status": "success",
            "data": {"type": "FeatureCollection", "features": []},
        }

    try:
        geojson_str = result.to_json()
        geojson_dict = json.loads(geojson_str)
    except Exception as e:
        return {
            "status": "error",
            "message": f"failed to serialize results to GeoJSON: {e}",
        }

    return {"status": "success", "data": _sanitize_value(geojson_dict)}


def geojson_to_png(geojson: dict, filename: str = "output.png"):
    """
    Render a GeoJSON FeatureCollection to a PNG image (in-memory) using geopandas and matplotlib
    and return a dict with the PNG bytes suitable for further processing or saving.
    Args:
        geojson (dict): GeoJSON FeatureCollection as a dict.
        filename (str): Filename to use when saving the PNG (for reference).
    Returns:
        dict: Result with either an error or an 'artifact' containing filename, mime_type and raw PNG bytes.

    Make sure to save the PNG bytes as an artifact using the provided CallbackContext and tool.
    """
    import matplotlib.pyplot as plt
    import io

    # Read GeoJSON into a GeoDataFrame
    try:
        features = geojson.get("features", [])
        gdf = gpd.GeoDataFrame.from_features(features)
    except Exception as e:
        return {"status": "error", "message": f"failed to read GeoJSON: {e}"}

    if gdf.empty:
        return {
            "status": "success",
            "data": {"type": "FeatureCollection", "features": []},
        }

    # Render the GeoDataFrame to an in-memory PNG
    try:
        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(ax=ax, color="blue", edgecolor="black")
        ax.axis("off")
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)

        buffer.seek(0)
        png_bytes = buffer.getvalue()

        # Save the file in a directory for debug
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, filename), "wb") as f:
            f.write(png_bytes)
        return {
            "status": "success",
            "message": {
                "file saved as:": f"{filename}",
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"failed to render PNG: {e}"}
