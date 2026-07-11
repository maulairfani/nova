"""Standalone test: confirms conversation state persists across two
separate process invocations using the same thread_id (real
AsyncPostgresSaver, not InMemorySaver). Not part of the app.

Usage: run twice in a row with the same THREAD_ID env var; second run
should show the agent recalling the first run's content.
"""
import asyncio
import os

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from app.agent.checkpointer import get_checkpointer_cm
from app.agent.llm import get_llm
from app.agent.mcp_client import get_tools_for_identity
from app.agent.prompts import SYSTEM_PROMPT

THREAD_ID = os.environ.get("THREAD_ID", "persistence-test-1")


async def main() -> None:
    tools = await get_tools_for_identity({"x-nova-business-units": "tv"})

    async with get_checkpointer_cm() as checkpointer:
        agent = create_agent(
            model=get_llm(),
            tools=tools,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )
        config = {"configurable": {"thread_id": THREAD_ID}}

        message = os.environ.get("MESSAGE", "What's the daypart with the cheapest ad rate?")
        result = await agent.ainvoke({"messages": [HumanMessage(content=message)]}, config=config)
        print(f"[thread_id={THREAD_ID}] Q: {message}")
        print(f"A: {result['messages'][-1].content}")
        print(f"(total messages in thread so far: {len(result['messages'])})")


if __name__ == "__main__":
    asyncio.run(main())
