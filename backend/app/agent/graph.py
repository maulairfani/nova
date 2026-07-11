"""ReAct Agent (TDD §5.2) — `create_agent` already implements the
reason -> act -> observe loop (ADR-0012/0013); no custom graph is
hand-built here."""
from langchain.agents import create_agent

from app.agent.llm import get_llm
from app.agent.mcp_client import get_tools_for_identity
from app.agent.prompts import SYSTEM_PROMPT


async def build_agent(auth_headers: dict[str, str], checkpointer):
    tools = await get_tools_for_identity(auth_headers)
    return create_agent(
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
