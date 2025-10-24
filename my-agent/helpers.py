import math
import types
import numpy as np
import pandas as pd
from datetime import datetime, date


def register_tool(agent, name: str, func, description: str, parameters: dict = None):
    """Register a tool on agent using whichever API exists.

    Tries, in order: agent.add_tool(...), agent.register_tool(...),
    agent.tools (dict/list), or falls back to attaching a simple
    `_tools` dict to the instance.
    """
    # Preferred method: add_tool
    try:
        add = getattr(agent, "add_tool")
        # Try to pass parameter schema if the API supports it
        try:
            return add(name=name, func=func, description=description, parameters=parameters)
        except TypeError:
            return add(name=name, func=func, description=description)
    except Exception:
        pass

    # Alternate method: register_tool
    try:
        reg = getattr(agent, "register_tool")
        try:
            return reg(name=name, func=func, description=description, parameters=parameters)
        except TypeError:
            return reg(name=name, func=func, description=description)
    except Exception:
        pass

    # Prefer to register the raw callable into agent.tools (a list), so the
    # ADK can later convert callables into FunctionTool via
    # _convert_tool_union_to_tools. Create agent.tools if missing.
    try:
        if not hasattr(agent, "tools") or getattr(agent, "tools") is None:
            setattr(agent, "tools", [])

        tools_attr = getattr(agent, "tools")
        if isinstance(tools_attr, list):
            tools_attr.append(func)
            return func
        if isinstance(tools_attr, dict):
            # keep backwards compatibility if tools is a mapping
            # store function and optional parameter schema
            tools_attr[name] = {"func": func, "parameters": parameters}
            return func
    except Exception:
        # fall through to final fallback
        pass

    # Final fallback: attach an _tools dict on the instance and return it
    if not hasattr(agent, "_tools"):
        setattr(agent, "_tools", {})

    agent._tools[name] = {"func": func, "description": description, "parameters": parameters}
    # expose a convenience method if needed: ensure add_tool appends to agent.tools
    if not hasattr(agent, "add_tool"):

        def _add_tool(self, **kwargs):
            if not hasattr(self, "tools") or self.tools is None:
                self.tools = []
            self.tools.append(kwargs.get("func"))
            if not hasattr(self, "_tools"):
                self._tools = {}
            self._tools[kwargs["name"]] = {
                "func": kwargs.get("func"),
                "description": kwargs.get("description"),
            }

        agent.add_tool = types.MethodType(_add_tool, agent)

    return agent._tools[name]


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
