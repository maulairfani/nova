"""OpenRouter embeddings client (ADR-0015) — a deliberate small duplicate of
mcp_servers/common/embeddings.py, not a shared import across that boundary
(see ADR-0022's Alternatives Considered). Must use the exact same model as
each business unit's KB Search Tool (query-time), or the vector space
won't match."""
from openai import OpenAI


class EmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]
