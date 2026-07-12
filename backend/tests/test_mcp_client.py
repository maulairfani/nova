"""Unit tests for get_tools_for_identity (app/agent/mcp_client.py).

Regression tests for two real bugs found during phase-2/shared-server
verification:

1. The agent's combined tool list must only include servers matching the
   caller's claimed business unit(s) — an earlier version connected to
   every business unit server unconditionally, and the LLM could attempt a
   tool on a unit the caller wasn't authorized for, whose auth denial then
   crashed the whole SSE response.
2. Every business unit server exposes identically-named tools (kb_search,
   sql_analytics), so each tool's exposed name must be prefixed with its
   business unit — without that, the combined tool list has name
   collisions and dispatch is ambiguous about which server a call reaches.

Uses a fake MultiServerMCPClient (no real network) so this runs as a pure
unit test.
"""
import app.agent.mcp_client as mcp_client_module
from app.agent.mcp_client import _extract_cache_query
from langchain_core.tools import tool


def test_extract_cache_query_prefers_query_kwarg():
    assert _extract_cache_query({"query": "hello", "top_k": 5}) == "hello"


def test_extract_cache_query_falls_back_to_question_kwarg():
    assert _extract_cache_query({"question": "how many programs?"}) == "how many programs?"


def test_extract_cache_query_falls_back_to_json_when_no_known_kwarg():
    result = _extract_cache_query({"a": 1, "b": 2})
    assert result == '{"a": 1, "b": 2}'


@tool
async def kb_search(query: str) -> str:
    """fake kb search tool"""
    return "fake result"


@tool
async def sql_analytics(question: str) -> str:
    """fake sql analytics tool"""
    return "fake rows"


@tool
async def web_search(query: str) -> str:
    """fake web search tool"""
    return "fake search result"


_SERVER_TOOLS = {
    "mcp-tv": [kb_search, sql_analytics],
    "mcp-plus": [kb_search, sql_analytics],
    "mcp-news": [kb_search, sql_analytics],
    "mcp-shared": [web_search],
}


class FakeMultiServerMCPClient:
    def __init__(self, connections: dict):
        self.connections = connections

    async def get_tools(self, server_name: str):
        return list(_SERVER_TOOLS[server_name])


async def test_only_connects_to_claimed_business_unit_server(monkeypatch):
    monkeypatch.setattr(mcp_client_module, "MultiServerMCPClient", FakeMultiServerMCPClient)

    tools = await mcp_client_module.get_tools_for_identity({"x-nova-business-units": "tv"})

    tool_names = {t.name for t in tools}
    assert tool_names == {"tv_kb_search", "tv_sql_analytics", "shared_web_search"}


async def test_does_not_connect_to_unclaimed_business_units(monkeypatch):
    captured = {}

    class RecordingFakeClient(FakeMultiServerMCPClient):
        def __init__(self, connections: dict):
            captured["connections"] = connections
            super().__init__(connections)

    monkeypatch.setattr(mcp_client_module, "MultiServerMCPClient", RecordingFakeClient)

    await mcp_client_module.get_tools_for_identity({"x-nova-business-units": "plus"})

    assert "mcp-tv" not in captured["connections"]
    assert "mcp-news" not in captured["connections"]
    assert "mcp-plus" in captured["connections"]


async def test_shared_server_always_included_regardless_of_claimed_unit(monkeypatch):
    monkeypatch.setattr(mcp_client_module, "MultiServerMCPClient", FakeMultiServerMCPClient)

    tools = await mcp_client_module.get_tools_for_identity({"x-nova-business-units": "news"})

    assert "shared_web_search" in {t.name for t in tools}


async def test_no_identity_returns_no_tools(monkeypatch):
    monkeypatch.setattr(mcp_client_module, "MultiServerMCPClient", FakeMultiServerMCPClient)

    tools = await mcp_client_module.get_tools_for_identity({})

    assert tools == []


async def test_tool_names_are_prefixed_per_business_unit_to_avoid_collisions(monkeypatch):
    monkeypatch.setattr(mcp_client_module, "MultiServerMCPClient", FakeMultiServerMCPClient)

    tools = await mcp_client_module.get_tools_for_identity({"x-nova-business-units": "tv,plus"})

    tool_names = [t.name for t in tools]
    # tv and plus both expose "kb_search"/"sql_analytics" — without prefixing
    # these would collide into indistinguishable duplicate names.
    assert "tv_kb_search" in tool_names
    assert "plus_kb_search" in tool_names
    assert len(tool_names) == len(set(tool_names)), "tool names must be unique"
