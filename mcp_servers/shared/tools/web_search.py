"""Web Search Tool (TDD §6.4) — fallback for questions internal sources
(KB, business unit data) can't answer, via Tavily (ADR-0010)."""
from tavily import AsyncTavilyClient

from config import settings

_client = AsyncTavilyClient(api_key=settings.tavily_api_key)


async def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the public web for `query`. Use only when the knowledge base
    and business unit analytics tools don't have the answer."""
    response = await _client.search(query, max_results=max_results)

    return [
        {
            "title": result["title"],
            "url": result["url"],
            "content": result["content"],
            "score": result["score"],
        }
        for result in response["results"]
    ]
