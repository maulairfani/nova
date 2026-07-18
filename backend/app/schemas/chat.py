from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    # Features the employee explicitly turned on via the chat input's "+"
    # menu (frontend ChatInput.tsx) - these tools are always available to
    # the agent regardless (see mcp_client.py); this only forces their use
    # for this one message, via a system prompt addition (agent/prompts.py).
    force_tools: list[Literal["chart", "web_search"]] = Field(default_factory=list)
