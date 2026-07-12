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
- **`get_tools_for_identity` only connects to the caller's claimed business
  unit's server(s)**, not every business unit unconditionally. Found this
  the hard way in phase 2: with 3 servers live, an unscoped tool list let
  the LLM attempt tools on a unit the caller wasn't authorized for, and
  that server's auth denial came back as an unhandled exception that
  crashed the whole SSE response rather than failing gracefully. Every
  server also exposes identically-named tools (`kb_search`,
  `sql_analytics`), so each tool's exposed name is prefixed with its
  business unit (e.g. `tv_kb_search`) — without that, the combined tool
  list would have name collisions and dispatch would be ambiguous about
  which server a call actually reaches.
- **The Shared MCP Server (`mcp-shared`, web search) is always included**,
  unlike `tv`/`plus`/`news` — it isn't owned by any single business unit,
  so it isn't filtered by the caller's claimed unit(s).
- **Tool calls that fail are caught and returned as content, not raised.**
  `langchain-mcp-adapters` converts *any* MCP tool error (not just an auth
  mismatch — an invalid API key, a rate limit, any downstream failure)
  into a raised exception, and LangGraph's default tool-error handling
  re-raises it, crashing the whole SSE response over one failed tool call.
  This surfaced concretely with the web search tool (an external API is
  far more likely to fail than our own servers). `_wrap_with_cache` now
  catches any exception from the underlying tool call and returns it as a
  string instead — the agent sees a failed tool result and can respond
  gracefully (per `prompts.py`'s existing instruction not to guess an
  answer), rather than the whole request crashing.
- **Tool-result cache uses `pickle`, not JSON.** MCP tool results returned
  by `langchain-mcp-adapters` can be a `(content, artifact)` tuple, and a
  JSON round-trip silently turns that into a list — a different shape than
  what LangChain's tool-calling code expects, which caused a real bug
  during testing (a cache hit returned a differently-typed result than a
  cache miss). `pickle` preserves the exact type. Safe here because this
  cache only ever stores data the app itself wrote (never user input) and
  isn't reachable outside the Docker network.

## Verifying anything you change here

No standing test suite exists yet (phase 1/2 scope, see the CI/CD bonus
item in the outer workspace's tracking doc). Verify at the layer you
changed by running a short one-off script via
`docker compose run --rm backend-api python -c "..."` (or a scratch
`.py` file, deleted after use — don't commit ad-hoc verification
scripts): agent logic → build the agent via `get_tools_for_identity` +
`create_agent` and `ainvoke` a test message; checkpointer → run the same
`thread_id` twice and confirm history persists; cache → call a tool twice
and confirm the second call is a cache hit; HTTP layer →
`curl -N -X POST localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"thread_id":"...","message":"..."}'`.
