import geopandas as gpd
import pandas as pd
from pathlib import Path
import fnmatch
import json
from typing import Optional
from .helpers import _sanitize_value


def _geojson_from_gdf(gdf):
    """Return a GeoJSON string from a GeoDataFrame with sanitized properties."""
    # Use __geo_interface__ to get a GeoJSON-like dict, then sanitize
    geo = gdf.__geo_interface__
    features = geo.get("features", [])
    for feat in features:
        props = feat.get("properties", {})
        feat["properties"] = {k: _sanitize_value(v) for k, v in props.items()}
        # Ensure geometry coords are native types
        geom = feat.get("geometry")
        if geom is None and "geometry" in feat:
            feat["geometry"] = None
    return json.dumps(geo, ensure_ascii=False)


def geopandas_attributes_tool(shapefile_path: str, max_sample_rows: int = 10):
    """
    Read attribute schema and sample records from a vector file using geopandas.
    Returns a dict with 'columns', 'dtypes', 'crs', 'count', and 'sample' on success,
    or {'error': str} on failure.
    """
    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        return {"error": f"failed to read file: {e}"}

    try:
        columns = list(gdf.columns)
        dtypes = {col: str(gdf[col].dtype) for col in columns}
        crs = str(gdf.crs) if gdf.crs is not None else None
        count = len(gdf)

        # Provide sample attribute rows (exclude geometry column if present)
        sample_df = gdf.drop(columns="geometry", errors="ignore").head(max_sample_rows)
        # Replace NaN/NA with None so JSON serialization doesn't include invalid NaN tokens
        sample_df = sample_df.where(pd.notnull(sample_df), None)
        sample = sample_df.to_dict(orient="records")
    except Exception as e:
        return {"error": f"failed to inspect attributes: {e}"}

    return {
        "columns": columns,
        "dtypes": dtypes,
        "crs": crs,
        "count": count,
        "sample": sample,
    }


def geopandas_query_tool(shapefile_path: str, query: str, max_results: int = 100):
    """
    Execute a pandas-style query on a vector file (shapefile/geojson/etc.) using geopandas.
    Returns a dict with either 'geojson' and 'count' on success, or 'error' on failure.
    """

    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception as e:
        return {"error": f"failed to read file: {e}"}

    try:
        result = gdf.query(query)
    except Exception as e:
        return {"error": f"failed to execute query: {e}"}

    if result.empty:
        return {
            "geojson": json.dumps({"type": "FeatureCollection", "features": []}),
            "count": 0,
        }

    # Limit results
    result = result.head(max_results)

    # --- FIX 1: Convert to WGS84 (EPSG:4326) for standardized GeoJSON output ---
    try:
        res_for_json = result.to_crs(epsg=4326)
    except Exception:
        # If conversion fails (e.g., no CRS defined), use the original result
        res_for_json = result

    # --- FIX 2: Use the existing and robust _geojson_from_gdf helper for serialization ---
    # This helper handles:
    # 1. NaN/inf replacement with None/null.
    # 2. Ensures standard Python types from numpy types.
    # This is more reliable than to_json() for agent responses.
    try:
        geojson = _geojson_from_gdf(res_for_json)
    except Exception as e:
        return {"error": f"failed to serialize results to GeoJSON: {e}"}

    # Note: No need for manual NaN/NA replacement via .where() because _geojson_from_gdf does it.

    return {"geojson": geojson, "count": len(result)}


def find_file_tool(
    start_path: str = ".",
    filename_pattern: str = "*",
    max_results: int = 50,
    recursive: bool = True,
):
    """
    Search for files under start_path that match filename_pattern.
    - start_path: directory to start searching from.
    - filename_pattern: a glob-style pattern (e.g. '*.shp', 'data_*.geojson', or exact name).
    - max_results: maximum number of matches to return.
    - recursive: if True, search subdirectories; otherwise only the top directory.

    Returns {"paths": [str,...], "count": int} on success or {"error": str} on failure.
    """
    try:
        base = Path(start_path or ".")
    except Exception as e:
        return {"error": f"invalid start_path: {e}"}

    if not base.exists():
        return {"error": f"start_path does not exist: {start_path}"}
    if not base.is_dir():
        return {"error": f"start_path is not a directory: {start_path}"}

    matches = []
    try:
        if recursive:
            iterator = base.rglob("*")
        else:
            iterator = base.glob("*")

        for p in iterator:
            if not p.is_file():
                continue
            # fnmatch supports glob patterns; perform case-insensitive matching
            if fnmatch.fnmatch(p.name.lower(), filename_pattern.lower()):
                matches.append(str(p.resolve()))
                if len(matches) >= max_results:
                    break
    except Exception as e:
        return {"error": f"search failed: {e}"}
    print(
        f"find_file_tool: found {len(matches)} matches for pattern '{filename_pattern}' under '{start_path}'"
    )
    return {"paths": matches, "count": len(matches)}


def geopandas_plot_tool(shapefile_paths: list[str], output_image_path: str, title: Optional[str] = None):
    """
    Plot the geometries from one or more shapefiles and save the plot as a PNG image.
    - shapefile_paths: A list of paths to the shapefiles to plot.
    - output_image_path: Path where the output PNG image will be saved.
    - title: Optional title for the plot.

    Returns {'image_path': str} on success or {'error': str} on failure.
    """
    try:
        import matplotlib.pyplot as plt
        # Create a single axis for all plots
        fig, ax = plt.subplots(1, 1)
        
        for shapefile_path in shapefile_paths:
            gdf = gpd.read_file(shapefile_path)
            gdf.plot(ax=ax, legend=True, alpha=0.7) # Plot each shapefile on the same axis
        
        if title:
            ax.set_title(title)
        ax.set_axis_off()
        plt.savefig(output_image_path)
        plt.close(fig)  # Close the plot to free up memory
    except Exception as e:
        return {"error": f"failed to plot or save image: {e}"}

    return {"image_path": output_image_path}