"""Unit tests for the Cache Client (app/agent/cache.py).

Regression test for a real bug found during phase-1 verification: MCP tool
results can be a (content, artifact) tuple, and a JSON round-trip silently
turns that into a list — a different shape than what LangChain's
tool-calling code expects on a cache hit. Pickle preserves the exact type;
these tests assert that stays true.
"""
from app.agent.cache import get_cached, set_cached


async def test_cache_round_trip_preserves_tuple_type():
    """The core regression case: a (content, artifact) tuple must come back
    out of the cache as a tuple, not a list."""
    value = ("some grounded answer text", {"source": "01-doc.md"})

    await set_cached("tv", "kb_search", "test query", value)
    cached = await get_cached("tv", "kb_search", "test query")

    assert cached == value
    assert isinstance(cached, tuple), f"expected tuple, got {type(cached)}"


async def test_cache_miss_returns_none():
    cached = await get_cached("tv", "kb_search", "a query that was never cached")
    assert cached is None
