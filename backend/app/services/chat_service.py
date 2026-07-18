"""Chat business logic - building the agent's SSE event stream (TDD §5.2,
ADR-0017). app/api/v1/endpoints/chat.py stays a thin HTTP adapter around
this: it wires up dependencies and returns the StreamingResponse."""
import json

from langchain_core.messages import HumanMessage

from app.agent.graph import build_agent
from app.agent.tool_labels import map_tool_step, merge_citations, parse_chart_result, parse_citations
from app.services.conversation_service import touch_conversation

__all__ = ["touch_conversation", "stream_chat_events"]


async def stream_chat_events(auth_headers: dict[str, str], checkpointer, thread_id: str, message: str, force_tools):
    agent = await build_agent(auth_headers, checkpointer, force_tools)
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=message)]}
    citations: list[dict] = []

    async for event in agent.astream_events(inputs, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if chunk.content:
                yield f"data: {json.dumps({'token': chunk.content})}\n\n"
        elif event["event"] == "on_tool_start":
            step = map_tool_step(event["name"])
            yield f"event: tool_start\ndata: {json.dumps({'id': str(event['run_id']), **step})}\n\n"
        elif event["event"] == "on_tool_end":
            yield f"event: tool_end\ndata: {json.dumps({'id': str(event['run_id'])})}\n\n"
            output_content = event["data"]["output"].content
            chart = parse_chart_result(event["name"], output_content)
            if chart is not None:
                yield f"event: chart\ndata: {json.dumps(chart)}\n\n"
            updated = merge_citations(citations, parse_citations(event["name"], output_content))
            if len(updated) != len(citations):
                citations = updated
                yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

    yield "event: done\ndata: {}\n\n"
