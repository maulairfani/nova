"""Shared OpenRouter embeddings client (ADR-0015).

Used by both each business unit's KB Search Tool (query-time) and its
Qdrant seed script (index-time) — both must use the exact same model to
keep the vector space consistent.
"""
from openai import OpenAI


class EmbeddingClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]
