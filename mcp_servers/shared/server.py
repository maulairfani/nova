"""mcp-shared — Nova's Shared MCP Server (TDD §5.2/§6.4).

Exposes the Web Search Tool, behind a permissive Authorization Middleware
(ADR-0008 — callable-based) since results aren't scoped to any single
business unit.
"""
from typing import Literal

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers

from auth import check_shared_access
from common.auth import AuthContext
from tools.generate_chart import ChartSeries, generate_chart as _generate_chart
from tools.web_search import web_search as _web_search

mcp = FastMCP("mcp-shared")


def _current_auth_context() -> AuthContext:
    """Phase-1 simplification: identity comes from a forwarded dummy header
    (X-Nova-User et al.), not a verified token. See mcp_servers/shared/CLAUDE.md."""
    headers = get_http_headers()
    user_id = headers.get("x-nova-user", "anonymous")
    business_units = headers.get("x-nova-business-units", "").split(",") if headers.get("x-nova-business-units") else []
    roles = headers.get("x-nova-roles", "").split(",") if headers.get("x-nova-roles") else []
    return AuthContext(user_id=user_id, business_units=business_units, roles=roles)


@mcp.tool
async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the public web for content relevant to `query`. Use only when
    the knowledge base and business unit analytics tools don't have the
    answer."""
    if not check_shared_access(_current_auth_context()):
        raise ToolError("Not authorized to use Nova.")
    return await _web_search(query, max_results)


@mcp.tool
async def generate_chart(
    title: str,
    chart_type: Literal["bar", "line", "pie"],
    labels: list[str],
    series: list[ChartSeries],
    x_label: str = "",
    y_label: str = "",
) -> dict:
    """Render `title` as a chart image so the employee can read data more
    easily than a table of numbers. Call this with data you already have
    from a prior business-unit analytics tool result in this same turn —
    `labels` are the category/x-axis values (e.g. months, DMAs, segments)
    and each `series` is one line/set of bars sharing those labels (e.g.
    one series per demographic segment or metric). Use "pie" only for a
    single series showing parts of a whole. Never try to describe the
    image itself in your reply — just mention a chart was generated; it
    is shown to the employee automatically, you don't need to link it."""
    if not check_shared_access(_current_auth_context()):
        raise ToolError("Not authorized to use Nova.")
    return await _generate_chart(title, chart_type, labels, series, x_label, y_label)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=9004, path="/mcp")
