"""MCP Client (TDD §5.2) — connects to every Business Unit + Shared MCP
server, wraps each tool call with the Redis cache (TDD §8).

Phase-1 simplification: langchain-mcp-adapters' HTTP headers are static per
client instance (no per-call dynamic headers yet), so a fresh client is
built per chat request, parameterized by that request's dummy identity
(see backend/CLAUDE.md). Tool *schemas* don't depend on identity, only the
authorization check inside each MCP server does, so this only costs a
cheap HTTP round-trip per request, not a new architecture.
"""
import json

from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.agent.cache import get_cached, set_cached
from app.core.config import settings

# Maps MCP server name -> business unit, for cache keying (TDD §8).
_SERVER_TO_BUSINESS_UNIT = {"mcp-tv": "tv", "mcp-plus": "plus", "mcp-news": "news"}

# The Shared MCP Server (web search, TDD §6.4) isn't owned by any single
# business unit, so it's kept separate from the map above: it's included
# for any caller with a recognized identity, not filtered by claimed unit.
_SHARED_SERVER_NAME = "mcp-shared"
_SHARED_LABEL = "shared"


def _extract_cache_query(kwargs: dict) -> str:
    return kwargs.get("query") or kwargs.get("question") or json.dumps(kwargs, sort_keys=True)


def _wrap_with_cache(tool: BaseTool, business_unit: str) -> BaseTool:
    """Wraps a tool with the Redis cache and renames it with a business-unit
    prefix (e.g. "tv_kb_search"). Every business unit MCP server exposes
    identically-named tools ("kb_search", "sql_analytics") — without the
    prefix, the agent's combined tool list would have name collisions across
    servers, and tool dispatch would be ambiguous about which unit a call
    actually reaches.

    Also catches any exception the underlying MCP call raises (auth denial,
    a downstream API failure, a network error) and returns it as tool
    content instead of letting it propagate. Found this the hard way: any
    MCP tool result with isError=true (not just auth mismatches) gets
    converted by langchain-mcp-adapters into a raised exception, and
    LangGraph's default tool-error handling re-raises it rather than
    turning it into a ToolMessage — crashing the entire agent invocation
    (and the SSE response) over a single failed tool call. This matters
    most for the Shared MCP Server's web_search, since an external API
    (Tavily) is far more likely to fail/rate-limit than our own servers."""
    original_coroutine = tool.coroutine

    async def cached_coroutine(**kwargs):
        query = _extract_cache_query(kwargs)
        cached = await get_cached(business_unit, tool.name, query)
        if cached is not None:
            return cached
        try:
            result = await original_coroutine(**kwargs)
        except Exception as exc:
            return f"Tool call failed: {exc}"
        await set_cached(business_unit, tool.name, query, result)
        return result

    return StructuredTool(
        name=f"{business_unit}_{tool.name}",
        description=f"[{business_unit.upper()}] {tool.description}",
        args_schema=tool.args_schema,
        coroutine=cached_coroutine,
    )


_SERVER_URLS = {
    "mcp-tv": lambda: settings.mcp_tv_url,
    "mcp-plus": lambda: settings.mcp_plus_url,
    "mcp-news": lambda: settings.mcp_news_url,
    "mcp-shared": lambda: settings.mcp_shared_url,
}


async def get_tools_for_identity(auth_headers: dict[str, str]) -> list[BaseTool]:
    """Only connects to the MCP server(s) matching the caller's claimed
    business units (X-Nova-Business-Units), not every server unconditionally.

    Exposing every business unit's tools regardless of identity was a real
    bug found during phase 2 testing: with 3 servers live, the agent's
    combined tool list let the LLM attempt tools on units the caller wasn't
    authorized for, and that server's auth denial surfaced as an unhandled
    exception that crashed the whole SSE response instead of failing
    gracefully. Scoping the tool list to the caller's own unit(s) up front
    avoids the failure case entirely (and is also the right shape for the
    future cross-business-unit flow, TDD §6.3, where the identity would
    legitimately claim more than one unit at once)."""
    claimed_units = {
        u.strip() for u in auth_headers.get("x-nova-business-units", "").split(",") if u.strip()
    }
    relevant_servers = {
        server_name: business_unit
        for server_name, business_unit in _SERVER_TO_BUSINESS_UNIT.items()
        if business_unit in claimed_units
    }
    if not relevant_servers:
        return []

    # The Shared MCP Server is available to any caller with a claimed
    # identity (not scoped to a single unit's data) — see mcp_servers/shared/auth.py.
    relevant_servers[_SHARED_SERVER_NAME] = _SHARED_LABEL

    client = MultiServerMCPClient(
        {
            server_name: {
                "transport": "streamable_http",
                "url": _SERVER_URLS[server_name](),
                "headers": auth_headers,
            }
            for server_name in relevant_servers
        }
    )
    all_tools = []
    for server_name, business_unit in relevant_servers.items():
        server_tools = await client.get_tools(server_name=server_name)
        all_tools.extend(_wrap_with_cache(tool, business_unit) for tool in server_tools)
    return all_tools
