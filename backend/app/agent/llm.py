"""LLM Client (TDD §5.2) — the agent's model, via OpenRouter (ADR-0015/0018)."""
from langchain_openrouter import ChatOpenRouter

from app.core.config import settings


def get_llm() -> ChatOpenRouter:
    return ChatOpenRouter(
        model=settings.openrouter_llm_model,
        api_key=settings.openrouter_api_key,
        temperature=0,
        streaming=True,
    )
