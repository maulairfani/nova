"""Standalone test: agent loop correctness, isolated from the Postgres
checkpointer and the HTTP layer. Not part of the app; delete before
shipping if not useful as a dev script."""
import asyncio

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.llm import get_llm
from app.agent.mcp_client import get_tools_for_identity
from app.agent.prompts import SYSTEM_PROMPT


async def main() -> None:
    tools = await get_tools_for_identity({"x-nova-business-units": "tv"})
    print(f"Loaded {len(tools)} tools: {[t.name for t in tools]}")

    agent = create_agent(
        model=get_llm(),
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )

    config = {"configurable": {"thread_id": "test-thread-1"}}
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="How much lead time do I need to book a prime time ad slot?")]},
        config=config,
    )
    print("\n--- Final answer ---")
    print(result["messages"][-1].content)

    print("\n--- Tool calls made ---")
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  called: {tc['name']}({tc['args']})")


if __name__ == "__main__":
    asyncio.run(main())
