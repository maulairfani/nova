"""Standalone test: confirms the Redis tool-result cache actually short-
circuits a repeated identical tool call. Not part of the app."""
import asyncio
import time

from app.agent.cache import get_redis
from app.agent.mcp_client import get_tools_for_identity


async def main() -> None:
    tools = await get_tools_for_identity({"x-nova-business-units": "tv"})
    kb_search = next(t for t in tools if t.name == "kb_search")

    query = "what is the classification for adult content"

    redis = get_redis()
    await redis.flushdb()

    t0 = time.perf_counter()
    result1 = await kb_search.coroutine(query=query, top_k=5)
    t1 = time.perf_counter()
    print(f"1st call (expect cache MISS): {t1 - t0:.3f}s")

    keys = await redis.keys("toolcache:*")
    print(f"Redis keys after 1st call: {keys}")

    t2 = time.perf_counter()
    result2 = await kb_search.coroutine(query=query, top_k=5)
    t3 = time.perf_counter()
    print(f"2nd call (expect cache HIT):  {t3 - t2:.3f}s")

    print(f"Results identical: {result1 == result2}")
    print(f"Speedup: {(t1 - t0) / (t3 - t2):.1f}x")


if __name__ == "__main__":
    asyncio.run(main())
