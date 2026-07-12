"""Integration test — hits a live docker-compose stack's Chat Endpoint
end-to-end (Frontend's HTTP contract, minus the browser): backend-api's
ReAct agent -> mcp-tv -> Qdrant/Postgres -> a real, grounded streamed
answer. Requires the stack to already be up with MCN TV migrated and
seeded (see .github/workflows/ci.yml's integration-test job, or run
locally against the dev docker-compose.yaml after the one-off setup steps
in the README).
"""
import os

import httpx
import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


@pytest.mark.integration
async def test_chat_endpoint_streams_a_grounded_tv_answer():
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            f"{BACKEND_URL}/api/v1/chat",
            json={
                "thread_id": "ci-integration-test-tv",
                "message": "How much lead time do I need to book a prime time ad slot?",
            },
            headers={"X-Nova-Business-Units": "tv"},
        ) as response:
            assert response.status_code == 200

            tokens = []
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    tokens.append(line)

    assert tokens, "expected at least one streamed SSE data frame"
    full_text = " ".join(tokens)
    assert "14" in full_text or "prime" in full_text.lower(), (
        "expected the answer to be grounded in the seeded ad-slot-booking SOP "
        f"(14-day lead time / mentions 'prime time'), got: {full_text[:500]}"
    )
