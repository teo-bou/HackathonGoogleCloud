import geopandas as gpd
from .helpers import _sanitize_value, load_geojson_file, write_geojson_file
from typing import List, Dict, Any, Optional
import json
import os


def list_file_in_map_data_directory():
    """
    List all files in the 'Map_Data' directory.
    """
    import os

    base_path = "map_data/geojson"
    files = []
    for entry in os.scandir(base_path):
        if entry.is_file():
            files.append(entry.name)
    return {"status": "success", "files": files}


def combine_multiple_geojson(geojson_list: List[str], filename: str):
    """
    Combine multiple GeoJSON Files into a single GeoJSON File.
    Args:
        geojson_list: the list of path for the file to be combined
        filename: the filename of the geojson file to be created
    Returns:
        dict: the path of the geojson file created
    """
    if geojson_list is None:
        return {"status": "error", "message": "geojson_list is None"}

    if not isinstance(geojson_list, list):
        return {"status": "error", "message": "expected geojson_list to be a list"}

    combined_features = []
    for geojson_path in geojson_list:
        geojson = load_geojson_file(geojson_path)
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

    output_path = write_geojson_file(combined_geojson, filename)

    return {
        "status": "success",
        "message": f"GeoJSON files combined successfully in {output_path}",
    }


def query_geojson(geojson_path: str, query: str):
    """
    Execute a pandas-style query on a GeoJSON FeatureCollection using geopandas.
    Args:
        geojson_path (str): path of the GeoJSON FeatureCollection.
        query (str): Geopandas-style query string.
    Returns:
        dict: path to the file written.
    """
    geojson = load_geojson_file(geojson_path)
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


def transform_geojson(geojson_path: str, query: str, geojson_output_path: str):
    """
    Execute a pandas-style query on a GeoJSON FeatureCollection using geopandas.
    Args:
        geojson_path (str): path of the GeoJSON FeatureCollection.
        query (str): Geopandas-style query string.
        geojson_output_path (str) : path to write the goejson output to
    Returns:
        dict: Resulting GeoJSON FeatureCollection after applying the query.
    """
    geojson = load_geojson_file(geojson_path)
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
        output_path = write_geojson_file(geojson_dict, geojson_output_path)
    except Exception as e:
        return {
            "status": "error",
            "message": f"failed to serialize results to GeoJSON: {e}",
        }

    return {
        "status": "success",
        "message": f"Successfully operating the query to {output_path}",
    }


def read_geojson_attributes(geojson_path: str):
    """
    Return the attributes of a geojson file.
    Args:
        geojson_path (str): path to the geojson file.
    """
    geojson = load_geojson_file(geojson_path)
    try:
        if not isinstance(geojson, dict) or geojson.get("type") != "FeatureCollection":
            return {"status": "error", "message": "invalid GeoJSON FeatureCollection"}

        features = geojson.get("features", [])
    except Exception as e:
        return {"status": "error", "message": f"failed to read geojson: {e}"}

    if not features:
        return {"status": "success", "data": {"feature_count": 0, "attributes": {}}}

    attr_info: Dict[str, Dict[str, Any]] = {}
    for feat in features:
        if not isinstance(feat, dict):
            continue
        props = feat.get("properties", {}) or {}
        for k, v in props.items():
            info = attr_info.setdefault(
                k, {"types": set(), "examples": [], "count_non_null": 0}
            )
            if v is None:
                info["types"].add("null")
            else:
                info["types"].add(type(v).__name__)
                info["count_non_null"] += 1
                if v not in info["examples"] and len(info["examples"]) < 5:
                    info["examples"].append(v)

    # Convert sets to lists and prepare final structure
    attributes: Dict[str, Any] = {}
    for k, v in attr_info.items():
        attributes[k] = {
            "types": sorted(list(v["types"])),
            "examples": v["examples"],
            "count_non_null": v["count_non_null"],
        }

    result = {"feature_count": len(features), "attributes": attributes}
    return {"status": "success", "data": _sanitize_value(result)}


def geojson_to_png(geojson_path: str, filename: str = "output.png"):
    """
    Render a GeoJSON FeatureCollection to a PNG image (in-memory) using geopandas and matplotlib
    and return a dict with the PNG bytes suitable for further processing or saving.
    Args:
        geojson_path (str): path to the GeoJSON FeatureCollection.
        filename (str): Filename to use when saving the PNG (for reference).
    Returns:
        dict: Result with either an error or an 'artifact' containing filename, mime_type and raw PNG bytes.

    Make sure to save the PNG bytes as an artifact using the provided CallbackContext and tool.
    """
    import matplotlib.pyplot as plt
    import io

    # Read GeoJSON into a GeoDataFrame
    try:
        geojson = load_geojson_file(geojson_path)
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


def select_by_geometry(
    source_geojson_path: str,
    target_geojson_path: str,
    predicate: str = "intersects",
    output_path: Optional[str] = None,
):
    """
    Select features from `source_geojson_path` that satisfy a spatial predicate
    with any feature in `target_geojson_path`.

    Args:
        source_geojson_path: path to the source GeoJSON file (features to filter)
        target_geojson_path: path to the target GeoJSON file (features to test against)
        predicate: one of shapely/geopandas spatial predicates: 'intersects',
                   'contains', 'within', 'touches', 'crosses', 'overlaps'
        output_path: optional path to write resulting GeoJSON

    Returns:
        dict: {'status': 'success', 'data': FeatureCollection} or an error dict.
    """
    try:
        src = load_geojson_file(source_geojson_path)
        tgt = load_geojson_file(target_geojson_path)
        gdf_src = gpd.GeoDataFrame.from_features(src.get("features", []))
        gdf_tgt = gpd.GeoDataFrame.from_features(tgt.get("features", []))
    except Exception as e:
        return {"status": "error", "message": f"failed to read GeoJSON: {e}"}

    if gdf_src.empty or gdf_tgt.empty:
        return {
            "status": "success",
            "data": {"type": "FeatureCollection", "features": []},
        }

    # Ensure geometry column exists
    try:
        # try modern predicate argument first
        try:
            joined = gpd.sjoin(gdf_src, gdf_tgt, how="inner", predicate=predicate)
        except TypeError:
            # older geopandas versions used 'op' instead of 'predicate'
            joined = gpd.sjoin(gdf_src, gdf_tgt, how="inner", op=predicate)
    except Exception:
        # As a fallback, do pairwise testing using shapely geometry methods
        try:
            mask = []
            for geom in gdf_src.geometry:
                ok = False
                for other in gdf_tgt.geometry:
                    try:
                        fn = getattr(geom, predicate)
                        if fn(other):
                            ok = True
                            break
                    except Exception:
                        # predicate not available on this geometry
                        continue
                mask.append(ok)
            result = gdf_src.loc[[i for i, m in enumerate(mask) if m]]
            if result.empty:
                return {
                    "status": "success",
                    "data": {"type": "FeatureCollection", "features": []},
                }
            geojson_str = result.to_json()
            geojson_dict = json.loads(geojson_str)
            if output_path:
                write_geojson_file(geojson_dict, output_path)
            return {"status": "success", "data": _sanitize_value(geojson_dict)}
        except Exception:
            return {"status": "error", "message": "spatial join failed"}

    if joined.empty:
        return {
            "status": "success",
            "data": {"type": "FeatureCollection", "features": []},
        }

    # joined contains columns from both; get unique left features
    left_index = joined.index.unique()
    try:
        result = gdf_src.loc[left_index]
        geojson_str = result.to_json()
        geojson_dict = json.loads(geojson_str)
        if output_path:
            write_geojson_file(geojson_dict, output_path)
        return {"status": "success", "data": _sanitize_value(geojson_dict)}
    except Exception as e:
        return {"status": "error", "message": f"failed to serialize results: {e}"}


def enrich_geometry_fields(
    geojson_path: str,
    output_path: Optional[str] = None,
    add_centroid: bool = True,
    add_area_m2: bool = False,
):
    """
    Add geometry-derived attributes to each feature: centroid (as WKT) and
    optionally area in square meters. Area calculation will reproject to
    EPSG:3857 (meters) if possible to provide approximate metric areas.

    Args:
        geojson_path: path to GeoJSON file to enrich
        output_path: optional path to write enriched GeoJSON
        add_centroid: whether to add a 'centroid_wkt' property
        add_area_m2: whether to add an 'area_m2' property (requires reprojection)

    Returns:
        dict: {'status': 'success', 'data': FeatureCollection} or an error dict.
    """
    try:
        geojson = load_geojson_file(geojson_path)
        gdf = gpd.GeoDataFrame.from_features(geojson.get("features", []))
    except Exception as e:
        return {"status": "error", "message": f"failed to read GeoJSON: {e}"}

    if gdf.empty:
        return {
            "status": "success",
            "data": {"type": "FeatureCollection", "features": []},
        }

    # Add centroid WKT
    try:
        if add_centroid:
            gdf["centroid_wkt"] = gdf.geometry.centroid.apply(
                lambda p: p.wkt if p is not None else None
            )
    except Exception as e:
        return {"status": "error", "message": f"failed to compute centroids: {e}"}

    # Add area in square meters by reprojecting to EPSG:3857 where units are meters
    if add_area_m2:
        try:
            # make a copy to avoid mutating original CRS
            gdf_area = gdf.copy()
            if gdf_area.crs is None:
                # assume WGS84 if not provided
                gdf_area.set_crs(epsg=4326, inplace=True)
            gdf_area = gdf_area.to_crs(epsg=3857)
            gdf["area_m2"] = gdf_area.geometry.area
        except Exception as e:
            # don't fail the whole operation for area calc errors; return a partial result
            gdf["area_m2"] = None

    try:
        geojson_str = gdf.to_json()
        geojson_dict = json.loads(geojson_str)
        if output_path:
            write_geojson_file(geojson_dict, output_path)
        return {"status": "success", "data": _sanitize_value(geojson_dict)}
    except Exception as e:
        return {
            "status": "error",
            "message": f"failed to serialize enriched GeoJSON: {e}",
        }
