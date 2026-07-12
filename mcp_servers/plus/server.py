"""mcp-plus — MCN+'s Business Unit MCP Server (TDD §5.2).

Covers both MCN+ products (streaming and shorts — ADR-0014, one MCP server
for the whole business unit). Exposes KB Search + SQL Analytics tools,
behind MCN+'s own Authorization Middleware (ADR-0008 — callable-based,
per-unit).
"""
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from auth import check_plus_access
from common.auth import AuthContext
from tools.kb_search import kb_search as _kb_search
from tools.sql_analytics import sql_analytics as _sql_analytics

mcp = FastMCP("mcp-plus")


def _current_auth_context() -> AuthContext:
    """Phase-1 simplification: identity comes from a forwarded dummy header
    (X-Nova-User et al.), not a verified token. See mcp_servers/plus/CLAUDE.md."""
    headers = get_http_headers()
    user_id = headers.get("x-nova-user", "anonymous")
    business_units = headers.get("x-nova-business-units", "").split(",") if headers.get("x-nova-business-units") else []
    roles = headers.get("x-nova-roles", "").split(",") if headers.get("x-nova-roles") else []
    return AuthContext(user_id=user_id, business_units=business_units, roles=roles)


@mcp.tool
async def kb_search(query: str, top_k: int = 5) -> list[dict]:
    """Search MCN+'s internal knowledge base (SOPs, documentation, covering
    both streaming and shorts) for content relevant to `query`."""
    if not check_plus_access(_current_auth_context()):
        raise ToolError("Not authorized for MCN+'s data.")
    return await _kb_search(query, top_k)


@mcp.tool
async def sql_analytics(question: str) -> dict:
    """Answer an analytics question about MCN+'s titles, engagement, or
    revenue (streaming or shorts) via read-only SQL."""
    if not check_plus_access(_current_auth_context()):
        raise ToolError("Not authorized for MCN+'s data.")
    return await _sql_analytics(question)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9002, path="/mcp")
