import math
from datetime import date, datetime
import numpy as np
import pandas as pd
import json


def load_geojson_file(path: str):
    """
    Loads a geojson file
    """
    # Open and parse the GeoJSON file. Use json.load to parse directly from
    # the file-like object (previous code accidentally passed the file object
    # to f.read, causing a TypeError).
    with open(path, "r") as f:
        geojson = json.load(f)
    return geojson


def write_geojson_file(geojson: dict, path: str) -> str:
    """
    Writes a geojson file
    """
    # Ensure parent directory exists (helps on Windows where '/tmp' may not exist)
    from pathlib import Path

    p = Path(path)
    if not p.parent.exists():
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If we cannot create the parent, raise a clear error
            raise

    # Write JSON with UTF-8 encoding and ensure_ascii=False for readability
    with open(p, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False)
    return str(p)


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
