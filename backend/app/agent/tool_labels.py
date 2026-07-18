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


def parse_citations(tool_name: str, raw_content) -> list[dict] | None:
    """Pulls citation cards out of a kb_search or web_search tool call's
    result (chunk-level - a single call can return several) for the
    Sources panel, or None for any other tool or any parse failure - same
    "malformed result just means nothing to show" discipline as
    parse_chart_result. Unlike that dict-shaped result, kb_search/
    web_search return a *list*, which FastMCP wraps as
    `structured_content["result"]` (verified directly against a live MCP
    call, not assumed - the wrapping differs from a dict-returning tool's
    `structured_content` being the dict itself)."""
    is_kb = tool_name.endswith("_kb_search")
    is_web = tool_name.endswith("_web_search")
    if not (is_kb or is_web):
        return None
    try:
        parsed = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
        results = parsed[1]["structured_content"]["result"]
        if is_kb:
            unit = tool_name[: -len("_kb_search")]
            return [
                {
                    "type": "kb",
                    "unit": unit,
                    "title": r["title"],
                    "snippet": r["text"][:280],
                    "source_document": r["source_document"],
                }
                for r in results
            ]
        return [{"type": "web", "title": r["title"], "snippet": r["content"][:280], "url": r["url"]} for r in results]
    except Exception:
        return None


def _citation_key(citation: dict) -> tuple:
    return (citation["type"], citation.get("source_document") or citation.get("url"))


def merge_citations(citations: list[dict], new_raw: list[dict] | None) -> list[dict]:
    """Appends newly-retrieved citations to a turn's running list, merging
    by (type, source_document/url) so the same document (cited via
    several chunks, or re-retrieved by a later tool call) gets one entry -
    its position in this list (1-based) is its citation number, shared by
    the live SSE stream and history reconstruction so both number
    identically. The LLM never sees or tracks this number itself (see
    SYSTEM_PROMPT) - it cites by title, which the frontend matches back to
    an entry here."""
    if not new_raw:
        return citations
    seen = {_citation_key(c) for c in citations}
    merged = list(citations)
    for c in new_raw:
        key = _citation_key(c)
        if key not in seen:
            seen.add(key)
            merged.append(c)
    return merged


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
