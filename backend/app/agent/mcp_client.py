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
# Phase 2 adds "mcp-plus": "plus", "mcp-news": "news" here.
_SERVER_TO_BUSINESS_UNIT = {"mcp-tv": "tv"}


def _extract_cache_query(kwargs: dict) -> str:
    return kwargs.get("query") or kwargs.get("question") or json.dumps(kwargs, sort_keys=True)


def _wrap_with_cache(tool: BaseTool, business_unit: str) -> BaseTool:
    original_coroutine = tool.coroutine

    async def cached_coroutine(**kwargs):
        query = _extract_cache_query(kwargs)
        cached = await get_cached(business_unit, tool.name, query)
        if cached is not None:
            return cached
        result = await original_coroutine(**kwargs)
        await set_cached(business_unit, tool.name, query, result)
        return result

    return StructuredTool(
        name=tool.name,
        description=tool.description,
        args_schema=tool.args_schema,
        coroutine=cached_coroutine,
    )


async def get_tools_for_identity(auth_headers: dict[str, str]) -> list[BaseTool]:
    client = MultiServerMCPClient(
        {
            "mcp-tv": {
                "transport": "streamable_http",
                "url": settings.mcp_tv_url,
                "headers": auth_headers,
            }
        }
    )
    all_tools = []
    for server_name, business_unit in _SERVER_TO_BUSINESS_UNIT.items():
        server_tools = await client.get_tools(server_name=server_name)
        all_tools.extend(_wrap_with_cache(tool, business_unit) for tool in server_tools)
    return all_tools
