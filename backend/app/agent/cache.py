"""Cache Client (TDD §5.2) — Redis, keyed on (business_unit, tool_name, normalized_query)
per TDD §8, short TTL (data changes; stale answers cost more than a cache miss).

Uses pickle rather than JSON: MCP tool results returned by langchain-mcp-
adapters can be a (content, artifact) tuple, not just plain dicts/lists —
JSON round-tripping silently turns that tuple into a list, which is a
different shape than what LangChain's tool-calling machinery expects on a
cache hit vs. a fresh call. Pickle preserves the exact Python type. This
cache is internal-only (never touches user-supplied data, not reachable
outside the Docker network), so pickle's arbitrary-code-on-deserialize risk
doesn't apply here.
"""
import hashlib
import pickle

import redis.asyncio as redis

from app.core.config import settings

_TTL_SECONDS = 120

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=False)
    return _client


def _cache_key(business_unit: str, tool_name: str, query: str) -> str:
    normalized = query.strip().lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"toolcache:{business_unit}:{tool_name}:{digest}"


async def get_cached(business_unit: str, tool_name: str, query: str):
    raw = await get_redis().get(_cache_key(business_unit, tool_name, query))
    return pickle.loads(raw) if raw else None


async def set_cached(business_unit: str, tool_name: str, query: str, result) -> None:
    await get_redis().set(_cache_key(business_unit, tool_name, query), pickle.dumps(result), ex=_TTL_SECONDS)
