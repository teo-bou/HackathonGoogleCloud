import geopandas as gpd
from .helpers import _sanitize_value, load_geojson_file, write_geojson_file, BUCKET_NAME
from typing import List, Dict, Any, Optional
import json
import os
from google.cloud import storage


def list_file_in_map_data_directory():
    """
    List all files in the GCS bucket.
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    files = [blob.name for blob in blobs]
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
        empty_geojson = {"type": "FeatureCollection", "features": []}
        try:
            output_path = write_geojson_file(empty_geojson, geojson_output_path)
            return {
                "status": "success",
                "message": f"Query resulted in no features. Empty GeoJSON file written to {output_path}",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"failed to write empty GeoJSON file: {e}",
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
        "message": f"Successfully applied query and saved result to {output_path}",
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
        # Upload PNG bytes to GCS bucket as well
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(BUCKET_NAME)
            blob = bucket.blob(filename)
            blob.upload_from_string(png_bytes, content_type="image/png")
            gcs_uri = f"gs://{BUCKET_NAME}/{filename}"
        except Exception as e:
            return {
                "status": "error",
                "message": f"failed to upload PNG to bucket: {e}",
            }

        return {
            "status": "success",
            "message": {
                "file saved as:": f"{gcs_uri}",
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


def folium_show_layers(
    layers: List[Dict[str, Any]],
    center: Optional[List[float]] = None,
    zoom_start: int = 7,
    tiles: str = "OpenStreetMap",
    outfile_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Display multiple geographic layers (GeoJSON) from GCS or local path on a Folium map,
    with customizable styles and tooltips, then save this map to a Google Cloud Storage bucket.

    The layer 'path' can be a local file path or a GCS URI (e.g., 'gs://bucket/file.geojson').
    The map will be centered and zoomed to the combined bounds of the provided layers.

    layers: list of dicts:
    - path: str (local path or GCS URI)
    - name: str
    - style: dict (fillColor, color, fillOpacity, weight, etc.)
    - tooltip_fields: list[str]
    - tooltip_aliases: list[str]

        Returns: dict with status, gcs_uri (html_path), and layers.
    """
    import folium
    import json
    import os
    from pathlib import Path
    from typing import List, Dict, Any, Optional

    # ADDED IMPORT FOR GCS CLIENT
    try:
        from google.cloud import storage
    except ImportError:
        return {
            "status": "error",
            "message": "Missing required library: google-cloud-storage. Please install it.",
        }

    # REQUIRED LIBRARIES FOR GEOPANDAS/FSSPEC
    try:
        import geopandas as gpd
        import fsspec
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Missing required libraries: {e}. Please install folium, geopandas, and fsspec/gcsfs.",
        }

    # Default center (Madagascar) if not provided
    if center is None:
        center = [-19.0, 47.0]

    m = folium.Map(location=center, zoom_start=zoom_start, tiles=tiles)
    bounds_list = []

    # --- 1. Process Layers (Read from GCS or local using fsspec) ---
    for layer in layers:
        raw_path = layer.get("path")
        if not raw_path:
            continue

        geojson_data = None
        try:
            # fsspec handles reading from local paths and GCS (gs://)
            with fsspec.open(
                f"gs://{BUCKET_NAME}/{raw_path}", "r", encoding="utf-8"
            ) as f:
                geojson_data = json.load(f)
        except FileNotFoundError:
            print(f"Skipping layer: File not found at path: {raw_path}")
            continue
        except Exception as e:
            print(
                f"Skipping layer: Failed to read/parse GeoJSON from {raw_path}. Error: {e}"
            )
            continue

        # Bounds Computation
        try:
            feats = (
                geojson_data.get("features") if isinstance(geojson_data, dict) else None
            )
            if feats:
                gdf = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
                if not gdf.empty:
                    minx, miny, maxx, maxy = map(float, gdf.total_bounds)
                    bounds_list.append((minx, miny, maxx, maxy))
        except Exception:
            pass

        # Folium Layer Creation
        style = layer.get("style") or {}
        default_name = Path(raw_path).stem if raw_path else "Layer"

        gj = folium.GeoJson(
            geojson_data,
            name=layer.get("name", default_name),
            style_function=(lambda f, s=style: s) if style else None,
        )

        tooltip_fields = layer.get("tooltip_fields")
        tooltip_aliases = layer.get("tooltip_aliases")
        if tooltip_fields:
            folium.GeoJsonTooltip(
                fields=tooltip_fields,
                aliases=tooltip_aliases or tooltip_fields,
                sticky=True,
            ).add_to(gj)

        gj.add_to(m)

    folium.LayerControl().add_to(m)

    # Fit Bounds Logic
    if bounds_list:
        try:
            minx = min(b[0] for b in bounds_list)
            miny = min(b[1] for b in bounds_list)
            maxx = max(b[2] for b in bounds_list)
            maxy = max(b[3] for b in bounds_list)

            if minx == maxx and miny == maxy:
                center_lat = (miny + maxy) / 2.0
                center_lon = (minx + maxx) / 2.0
                m.location = [center_lat, center_lon]
                m.zoom_start = zoom_start
            else:
                m.fit_bounds([[miny, minx], [maxy, maxx]])
        except Exception:
            pass

    # --- 2. Render and Upload to GCS Bucket ---

    # Determine output path for the HTML file (for use as blob name)
    outdir = Path("output")
    if not outfile_name:
        # Use a unique name if none is provided
        outfile_name = f"folium_map_{os.getpid()}.html"

    # Handle paths consistently to get the desired GCS blob name
    candidate = Path(outfile_name)
    if candidate.is_absolute():
        # If absolute, just use the filename
        outpath = candidate
    else:
        # If relative and starts with 'output/', keep it relative to CWD
        if len(candidate.parts) > 0 and candidate.parts[0] == outdir.name:
            outpath = Path.cwd() / candidate
        else:
            # Otherwise, put it in the 'output' directory
            outpath = outdir / candidate

    # Render the folium map to an HTML string
    try:
        rendered = m.get_root().render()
    except Exception as e:
        return {"status": "error", "message": f"Failed to render HTML: {e}"}

    # Upload the rendered HTML to the configured GCS bucket
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # Use a sensible blob name: use the relative path or just the filename if absolute
        blob_name = outpath.as_posix() if not outpath.is_absolute() else outpath.name

        blob = bucket.blob(blob_name)
        # Use upload_from_string for the in-memory HTML content
        blob.upload_from_string(rendered, content_type="text/html")
        gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to upload HTML to bucket '{BUCKET_NAME}': {e}",
        }

    return {"status": "success", "html_path": gcs_uri, "layers": layers}
