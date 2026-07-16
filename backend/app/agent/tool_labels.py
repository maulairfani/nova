"""Maps a tool's exposed, business-unit-prefixed name (mcp_client.py's
_wrap_with_cache, e.g. "tv_kb_search") to a human-readable step for the
chat UI's tool-call trace - shared by the live SSE stream (chat.py) and
by reconstructing steps for a reloaded conversation's history
(conversations.py), so both stay consistent."""

_UNIT_LABELS = {"tv": "MCN TV", "plus": "MCN+", "news": "MCN News"}


def map_tool_step(tool_name: str) -> dict[str, str]:
    if tool_name.endswith("_kb_search"):
        unit = tool_name[: -len("_kb_search")]
        return {"type": "kb", "label": f"Searched {_UNIT_LABELS.get(unit, unit)} knowledge base"}
    if tool_name.endswith("_sql_analytics"):
        unit = tool_name[: -len("_sql_analytics")]
        return {"type": "data", "label": f"Queried {_UNIT_LABELS.get(unit, unit)} business data"}
    if tool_name.endswith("_web_search"):
        return {"type": "web", "label": "Searched the web"}
    return {"type": "kb", "label": f"Used {tool_name}"}
