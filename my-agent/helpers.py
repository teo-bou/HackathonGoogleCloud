import math
import types


def register_tool(agent, name: str, func, description: str):
    """Register a tool on agent using whichever API exists.

    Tries, in order: agent.add_tool(...), agent.register_tool(...),
    agent.tools (dict/list), or falls back to attaching a simple
    `_tools` dict to the instance.
    """
    # Preferred method: add_tool
    try:
        add = getattr(agent, "add_tool")
        return add(name=name, func=func, description=description)
    except Exception:
        pass

    # Alternate method: register_tool
    try:
        reg = getattr(agent, "register_tool")
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
            tools_attr[name] = func
            return func
    except Exception:
        # fall through to final fallback
        pass

    # Final fallback: attach an _tools dict on the instance and return it
    if not hasattr(agent, "_tools"):
        setattr(agent, "_tools", {})

    agent._tools[name] = {"func": func, "description": description}
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
    """Recursively replace NaN/inf with None and convert numpy types to native Python."""
    try:
        # numbers: catch nan and inf
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        # numpy scalar types have .item()
        if hasattr(v, "item"):
            try:
                return _sanitize_value(v.item())
            except Exception:
                pass
        if isinstance(v, dict):
            return {k: _sanitize_value(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [_sanitize_value(i) for i in v]
        return v
    except Exception:
        return None
