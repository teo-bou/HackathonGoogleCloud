import math
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd
import json
from google.cloud import storage

BUCKET_NAME = "reforestai-bucket"


def load_geojson_file(path: str):
    """
    Loads a geojson file from GCS.
    Args:
        path (str): The path within the bucket to load the file from.
    Returns:
        dict: The loaded GeoJSON data.
    """

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        # List blobs in the bucket and print their names
        for b in bucket.list_blobs():
            print(b.name)
        blob = bucket.blob(path)
        if blob.exists():
            content = blob.download_as_string()
            return json.loads(content)
    except Exception as e:
        print(e)
        raise e


def write_geojson_file(geojson: dict, path: str) -> str:
    """
    Writes a geojson file to a GCS bucket and returns a signed URL.
    Args:
        geojson (dict): The GeoJSON data to write.
        path (str): The path within the bucket to write the file to.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(path)

        # Upload the file
        blob.upload_from_string(json.dumps(geojson), content_type="application/json")

        # Generate a signed URL for the blob with a 5-hour expiration
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=5),
            method="GET",
        )
        return signed_url

    except Exception as e:
        print(e)
        raise e


def _sanitize_value(v):
    """Recursively replace NaN/inf with None and convert numpy/pandas types to native Python.

    This function is defensive: it converts numpy scalar types, pandas timestamps,
    numpy/pandas NA values to JSON-friendly Python types (None, str, int, float).
    """
    try:
        # numbers: catch nan and inf
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None

        # numpy scalar types have .item()
        if isinstance(v, (np.generic,)):
            return _sanitize_value(v.item())

        # pandas timestamp or python datetime/date -> ISO string
        if isinstance(v, (pd.Timestamp, datetime, date)):
            try:
                return v.isoformat()
            except Exception:
                return str(v)

        # dicts: recurse
        if isinstance(v, dict):
            return {k: _sanitize_value(val) for k, val in v.items()}

        # lists/tuples/sets: recurse
        if isinstance(v, (list, tuple, set)):
            return [_sanitize_value(i) for i in v]

        # pandas NA / numpy NaN detection
        try:
            if pd.isna(v):
                return None
        except Exception:
            pass

        # numpy arrays and other array-like: convert to list then sanitize
        if hasattr(v, "tolist") and not isinstance(v, (str, bytes)):
            try:
                return _sanitize_value(v.tolist())
            except Exception:
                pass

        return v
    except Exception:
        # On any unexpected error, return None for safety (so API payloads remain valid JSON)
        return None


def _sanitize_records(records):
    return [{k: _sanitize_value(v) for k, v in rec.items()} for rec in records]
