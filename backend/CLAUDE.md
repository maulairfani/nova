# backend/ — Nova's Backend API

FastAPI service implementing the Chat Endpoint and ReAct Agent (TDD §5.2).
Read [`documents/technical-design-document.md`](../documents/technical-design-document.md)
and the ADRs under `documents/adr/` before making non-trivial changes here —
they're the source of truth for *why* this is shaped this way.

## Structure

```
app/
  main.py              FastAPI app + lifespan (opens the Postgres checkpointer once)
  core/config.py        pydantic-settings, reads .env
  api/v1/endpoints/chat.py   Chat Endpoint — SSE (ADR-0017)
  agent/
    graph.py            create_agent wiring — the ReAct Agent itself
    llm.py              LLM Client — OpenRouter (ADR-0015/0018)
    mcp_client.py        MCP Client — MultiServerMCPClient + Redis tool-result cache wrapper
    checkpointer.py       Postgres checkpointer factory (nova_kb)
    cache.py             Cache Client (Redis, pickle-serialized — see note below)
    prompts.py
```

## Phase-1 simplifications (documented, not silent)

- **No real authentication.** The Chat Endpoint forwards whatever
  `X-Nova-User` / `X-Nova-Business-Units` / `X-Nova-Roles` headers the
  Frontend sends, unverified, into the `AuthContext` claims passed to each
  MCP server. This exists so `mcp-tv`'s authorization check has *something*
  real to evaluate (Quality Scenario 4, TDD §10.2), not because it's a real
  auth system. Replace with real identity/session handling before this goes
  anywhere near production.
- **A fresh `MultiServerMCPClient` per chat request.** `langchain-mcp-adapters`'
  HTTP headers are static per client instance (no per-call dynamic header
  injection as of this writing) — since the dummy identity varies per
  request, a new client is built per request rather than once at startup.
  Tool *schemas* don't depend on identity, so this only costs a cheap
  connection per request, not a re-architecture. Revisit if this becomes a
  real latency concern at higher traffic (not observed in phase 1).
- **Tool-result cache uses `pickle`, not JSON.** MCP tool results returned
  by `langchain-mcp-adapters` can be a `(content, artifact)` tuple, and a
  JSON round-trip silently turns that into a list — a different shape than
  what LangChain's tool-calling code expects, which caused a real bug
  during testing (a cache hit returned a differently-typed result than a
  cache miss). `pickle` preserves the exact type. Safe here because this
  cache only ever stores data the app itself wrote (never user input) and
  isn't reachable outside the Docker network.

## Dev/verification scripts (not part of the running app)

`test_agent_standalone.py`, `test_checkpointer_persistence.py`, and
`test_cache.py` are one-off scripts used to verify the agent loop, Postgres
checkpointer persistence, and Redis caching independently before wiring
them into the HTTP layer — kept as a record of what was verified and how,
and as a quick way to re-verify after a change. Run via
`docker compose run --rm backend-api python <script>.py`.

## Verifying anything you change here

Prefer testing at the layer you changed, same pattern as above: agent
logic → `test_agent_standalone.py`; checkpointer → `test_checkpointer_persistence.py`
(run twice with the same `THREAD_ID` env var); cache → `test_cache.py`;
HTTP layer → `curl -N -X POST localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"thread_id":"...","message":"..."}'`.
