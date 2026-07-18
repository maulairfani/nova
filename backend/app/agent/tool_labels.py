"""Maps a tool's exposed, business-unit-prefixed name (mcp_client.py's
_wrap_with_cache, e.g. "tv_kb_search") to a human-readable step for the
chat UI's tool-call trace - shared by the live SSE stream (chat.py) and
by reconstructing steps for a reloaded conversation's history
(conversations.py), so both stay consistent."""
import json

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
    if tool_name.endswith("_generate_chart"):
        return {"type": "chart", "label": "Generated a chart"}
    return {"type": "kb", "label": f"Used {tool_name}"}


def parse_chart_result(tool_name: str, raw_content) -> dict | None:
    """Pulls {chart_id, title, chart_type} out of a generate_chart tool
    call's result for the chart SSE event / history reconstruction, or
    None for any non-chart tool or any parse failure - a malformed or
    error-shaped result (ADR-0026) just means "no chart to show", not a
    crash. `raw_content` is a ToolMessage's .content - for an MCP tool
    this is a JSON string shaped like `[content_blocks, {"structured_content":
    {...}}]` (langchain-mcp-adapters' (content, artifact) tuple,
    JSON-serialized), verified directly against a live tool call rather
    than assumed."""
    if not tool_name.endswith("_generate_chart"):
        return None
    try:
        parsed = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        structured = parsed[1]["structured_content"]
        return {
            "chart_id": structured["chart_id"],
            "title": structured["title"],
            "chart_type": structured["chart_type"],
        }
    except Exception:
        return None
