# Nova

Nova is MCN Group's internal AI assistant. Employees ask it questions in
plain language and it answers by drawing on the company's internal
knowledge base (SOPs, documentation), each business unit's own data
(queried live, not from a warehouse copy), and the public web when
internal sources don't have the answer.

Full architecture and rationale: [`documents/technical-design-document.md`](documents/technical-design-document.md),
with every significant tech decision recorded as an ADR under
[`documents/adr/`](documents/adr/).

## Status: Phase 1 vertical slice

This build implements **one business unit (MCN TV) and one flow (knowledge-base
question answering)** end-to-end, proving the architecture before replicating
it to MCN+ and MCN News. Concretely, running today:

- Employee asks a question in the chat UI → Backend API's ReAct agent reasons
  about which tool to call → calls MCN TV's MCP server → which searches
  MCN TV's knowledge base (Qdrant) or queries MCN TV's analytics data
  (PostgreSQL, read-only) → agent generates a grounded, cited answer →
  streamed back token-by-token.
- Conversation history persists across sessions (LangGraph's Postgres
  checkpointer).
- Repeated questions hit a Redis cache instead of re-querying tools.

**Not yet built** (tracked as phase 2, see [`documents/technical-design-document.md`](documents/technical-design-document.md)
Section 11 and the TDD's runtime views, Section 6): MCN+ and MCN News MCP
servers/databases; the shared web-search MCP server; cross-business-unit
question synthesis; the async document-ingestion pipeline (MinIO + Celery) —
phase 1 seeds the knowledge base via a one-off script instead (see
[`mcp_servers/tv/CLAUDE.md`](mcp_servers/tv/CLAUDE.md) for why).

## Tech stack

| Layer | Choice | Why (ADR) |
|---|---|---|
| Backend API | Python, FastAPI | [ADR-0001](documents/adr/0001-backend-framework.md) |
| Frontend | Next.js (React), TypeScript | [ADR-0002](documents/adr/0002-frontend-framework.md) |
| Agent orchestration | LangChain/LangGraph `create_agent`, ReAct pattern | [ADR-0012](documents/adr/0012-agent-orchestration-framework.md), [ADR-0013](documents/adr/0013-agent-pattern.md) |
| MCP server framework | FastMCP (one server per business unit) | [ADR-0008](documents/adr/0008-mcp-server-framework.md) |
| Relational DB | PostgreSQL — one instance per business unit + one shared for conversation state | [ADR-0003](documents/adr/0003-relational-database.md) |
| DB migrations | Alembic, owned per business-unit MCP server | [ADR-0016](documents/adr/0016-database-migrations-alembic.md) |
| Vector DB | Qdrant — one collection per business unit | [ADR-0004](documents/adr/0004-vector-database.md) |
| Cache / tool-result cache | Redis | [ADR-0006](documents/adr/0006-cache.md) |
| LLM + embeddings | OpenAI `gpt-5.4-nano` + `text-embedding-3-small`, both via OpenRouter | [ADR-0009](documents/adr/0009-llm-provider.md), [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md), [ADR-0018](documents/adr/0018-llm-model-change-gpt-5-4-nano.md) |
| Streaming transport | Server-Sent Events | [ADR-0017](documents/adr/0017-streaming-transport-sse.md) |
| Containerization | Docker + Docker Compose | [Technical constraint, TDD §2](documents/technical-design-document.md) |

Business unit boundaries: Nova has **3** business units (MCN TV, MCN+, MCN
News) — MCN+ covers both streaming and micro-drama products under one
Data Mesh domain, not two ([ADR-0014](documents/adr/0014-mcn-plus-unified-business-unit.md)).

## Repository structure

```
backend/           FastAPI app — the ReAct agent, chat endpoint
frontend/          Next.js chat UI
mcp_servers/
  common/          Shared code (auth shape, embeddings client, Qdrant helper)
  tv/               MCN TV's MCP server (KB search + SQL analytics tools)
infrastructure/    Cross-cutting deployment config (not per-service migrations — those live in mcp_servers/<unit>/alembic/)
documents/         Technical Design Document, ADRs, company profile
docker-compose.yaml
```

Each service directory has its own `CLAUDE.md` explaining its internals and
any phase-1 simplifications: [`backend/CLAUDE.md`](backend/CLAUDE.md),
[`frontend/CLAUDE.md`](frontend/CLAUDE.md), [`mcp_servers/tv/CLAUDE.md`](mcp_servers/tv/CLAUDE.md).

## Build and run

### Prerequisites

- Docker + Docker Compose
- An [OpenRouter](https://openrouter.ai) API key (covers both the LLM and embeddings, [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md))

### 1. Configure environment

```bash
cp .env.example .env
# edit .env: set OPENROUTER_API_KEY to a real key; change the *_PASSWORD placeholders
```

### 2. Bring up the stack

```bash
docker compose up -d --build
```

### 3. One-off setup (first run only, or after wiping volumes)

These are deliberately manual, one-off steps rather than automatic
container-start behavior — see [`mcp_servers/tv/CLAUDE.md`](mcp_servers/tv/CLAUDE.md)
for why (in short: phase 1 doesn't have the real ingestion pipeline yet).

```bash
# Create MCN TV's analytics schema + read-only role
docker compose run --rm mcp-tv alembic upgrade head

# Seed MCN TV's dummy analytics data (programs, ratings, ad revenue)
docker compose run --rm mcp-tv python -m seed.seed_postgres

# Embed MCN TV's dummy SOP documents into Qdrant
docker compose run --rm mcp-tv python -m seed.seed_qdrant

# Create LangGraph's conversation-checkpoint tables
docker compose run --rm backend-api python setup_checkpointer.py
```

### 4. Use it

Open [http://localhost:3000](http://localhost:3000) and ask something like
*"How much lead time do I need to book a prime time ad slot?"* or *"What's
the average viewership rating across MCN TV's programs?"*

## How this was built with Claude Code

This project was built using Claude Code end-to-end — from the Technical
Design Document (Q1) through this implementation (Q2). Notably:

- **Every architecture decision is recorded as an ADR** (`documents/adr/`),
  including ones discovered/changed *during* implementation (e.g.
  [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md) for the
  OpenRouter gateway, [ADR-0016](documents/adr/0016-database-migrations-alembic.md)
  for Alembic, [ADR-0018](documents/adr/0018-llm-model-change-gpt-5-4-nano.md)
  for the LLM model) — the discipline of "new ADR, never silently edit an
  accepted one" was followed throughout, not just in the design phase.
- **Nested `CLAUDE.md` files** per service (`backend/`, `frontend/`,
  `mcp_servers/tv/`) document that service's internals and any phase-1
  shortcuts, so the next session (or a reviewer) doesn't have to
  reverse-engineer intent from code alone.
- **Every third-party API/package claim was verified before being used** —
  package versions were checked against PyPI/npm, not guessed; unfamiliar
  APIs (FastMCP's HTTP header access, LangChain's `create_agent` signature,
  the exact OpenRouter model slugs) were checked against live docs (via the
  `docs-langchain` and `docs-fastmcp` MCP servers configured in `.mcp.json`,
  or web search) before being written into code.
- **Each component was tested in isolation before integration** — `mcp-tv`
  was verified standalone (tool calls, auth allow/deny) before wiring it
  into the agent; the agent was tested with an in-memory checkpointer before
  swapping in the real Postgres one; the Redis cache was verified with a
  dedicated script that caught a real bug (a tuple/list type mismatch
  across a JSON round-trip, fixed by switching the cache to `pickle` —
  see the comment in `backend/app/agent/cache.py`) before being trusted.
- **Project-scoped Claude Code skills** (`.claude/skills/`) were installed
  for the frameworks actually in use (FastAPI, LangChain/LangGraph, frontend
  design) rather than left at defaults.
