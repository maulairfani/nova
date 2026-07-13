# Nova

Nova is MCN Group's internal AI assistant. Employees ask it questions in
plain language and it answers by drawing on the company's internal
knowledge base (SOPs, documentation), each business unit's own data
(queried live, not from a warehouse copy), and the public web when
internal sources don't have the answer.

Full architecture and rationale: [`documents/technical-design-document.md`](documents/technical-design-document.md),
with every significant tech decision recorded as an ADR under
[`documents/adr/`](documents/adr/).

## Status: 3 business units + web search fallback live

All 3 of Nova's business units (MCN TV, MCN+, MCN News) plus a shared
web-search fallback run end-to-end. Concretely, running today:

- Employee picks a business unit in the chat UI and asks a question → Backend
  API's ReAct agent reasons about which tool to call → calls that unit's MCP
  server → which searches that unit's knowledge base (Qdrant) or queries its
  analytics data (PostgreSQL, read-only) → agent generates a grounded, cited
  answer → streamed back token-by-token.
- If internal sources don't have the answer, the agent falls back to the
  Shared MCP Server's web search tool (Tavily).
- Conversation history persists across sessions (LangGraph's Postgres
  checkpointer) and starts fresh whenever the employee switches business
  units.
- Repeated questions hit a Redis cache instead of re-querying tools.

**Not yet built** (see [`documents/technical-design-document.md`](documents/technical-design-document.md)
Section 11 and the TDD's runtime views, Section 6): cross-business-unit
question synthesis (TDD §6.3); the async document-ingestion pipeline
(MinIO + Celery) — each unit currently seeds its knowledge base via a
one-off script instead (see [`mcp_servers/tv/CLAUDE.md`](mcp_servers/tv/CLAUDE.md)
for why).

## Tech stack

| Layer | Choice | Why (ADR) |
|---|---|---|
| Backend API | Python, FastAPI | [ADR-0001](documents/adr/0001-backend-framework.md) |
| Frontend | Next.js (React), TypeScript | [ADR-0002](documents/adr/0002-frontend-framework.md) |
| Agent orchestration | LangChain/LangGraph `create_agent`, ReAct pattern | [ADR-0012](documents/adr/0012-agent-orchestration-framework.md), [ADR-0013](documents/adr/0013-agent-pattern.md) |
| MCP server framework | FastMCP (one server per business unit + one shared) | [ADR-0008](documents/adr/0008-mcp-server-framework.md) |
| Web search | Tavily, via the Shared MCP Server | [ADR-0010](documents/adr/0010-web-search-provider.md) |
| Relational DB | PostgreSQL — one instance per business unit + one shared for conversation state | [ADR-0003](documents/adr/0003-relational-database.md) |
| DB migrations | Alembic, owned per business-unit MCP server | [ADR-0016](documents/adr/0016-database-migrations-alembic.md) |
| Vector DB | Qdrant — one collection per business unit | [ADR-0004](documents/adr/0004-vector-database.md) |
| Cache / tool-result cache | Redis | [ADR-0006](documents/adr/0006-cache.md) |
| LLM + embeddings | OpenAI `gpt-5.4-nano` + `text-embedding-3-small`, both via OpenRouter | [ADR-0009](documents/adr/0009-llm-provider.md), [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md), [ADR-0018](documents/adr/0018-llm-model-change-gpt-5-4-nano.md) |
| Streaming transport | Server-Sent Events | [ADR-0017](documents/adr/0017-streaming-transport-sse.md) |
| Containerization | Docker + Docker Compose | [Technical constraint, TDD §2](documents/technical-design-document.md) |
| CI/CD | GitHub Actions → GHCR; SSH deploy to a VM behind Caddy (auto TLS) | [ADR-0019](documents/adr/0019-cicd-and-production-deployment.md) |

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
  plus/             MCN+'s MCP server (streaming + shorts, one merged unit)
  news/             MCN News's MCP server
  shared/           Web search MCP server (Tavily) — not owned by any unit
infrastructure/    Cross-cutting deployment config (not per-service migrations — those live in mcp_servers/<unit>/alembic/)
  docker-compose.prod.yml   Production compose — pulls GHCR images, adds Caddy (ADR-0019)
  Caddyfile                 Reverse proxy config — auto TLS for the two production domains
documents/         Technical Design Document, ADRs, company profile
docker-compose.yaml
```

Each service directory has its own `CLAUDE.md` explaining its internals and
any phase-1 simplifications: [`backend/CLAUDE.md`](backend/CLAUDE.md),
[`frontend/CLAUDE.md`](frontend/CLAUDE.md), [`mcp_servers/tv/CLAUDE.md`](mcp_servers/tv/CLAUDE.md),
[`mcp_servers/plus/CLAUDE.md`](mcp_servers/plus/CLAUDE.md),
[`mcp_servers/news/CLAUDE.md`](mcp_servers/news/CLAUDE.md),
[`mcp_servers/shared/CLAUDE.md`](mcp_servers/shared/CLAUDE.md). `plus/` and
`news/` are direct replications of `tv/`'s template — read `tv/CLAUDE.md`
first for the shared rationale. `shared/` is a different, simpler shape
(no database/Qdrant ownership) — read its own `CLAUDE.md`.

## Build and run

### Prerequisites

- Docker + Docker Compose
- An [OpenRouter](https://openrouter.ai) API key (covers both the LLM and embeddings, [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md))
- A [Tavily](https://tavily.com) API key (web search fallback, [ADR-0010](documents/adr/0010-web-search-provider.md))

### 1. Configure environment

```bash
cp .env.example .env
# edit .env: set OPENROUTER_API_KEY and TAVILY_API_KEY to real keys; change the *_PASSWORD placeholders
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
# Create each business unit's analytics schema + read-only role
docker compose run --rm mcp-tv alembic upgrade head
docker compose run --rm mcp-plus alembic upgrade head
docker compose run --rm mcp-news alembic upgrade head

# Seed each unit's dummy analytics data
docker compose run --rm mcp-tv python -m seed.seed_postgres
docker compose run --rm mcp-plus python -m seed.seed_postgres
docker compose run --rm mcp-news python -m seed.seed_postgres

# Embed each unit's dummy SOP documents into Qdrant
docker compose run --rm mcp-tv python -m seed.seed_qdrant
docker compose run --rm mcp-plus python -m seed.seed_qdrant
docker compose run --rm mcp-news python -m seed.seed_qdrant

# Create LangGraph's conversation-checkpoint tables
docker compose run --rm backend-api python setup_checkpointer.py
```

### 4. (Optional) Connect a DB client

Each Postgres instance is exposed on the host for tools like DBeaver/psql:
`localhost:5433` (`nova_core`), `5434` (`mcn_tv`), `5435` (`mcn_plus`), `5436`
(`mcn_news`) — credentials are the `*_DB_USER`/`*_DB_PASSWORD` values from
your `.env`.

### 5. Use it

Open [http://localhost:3000](http://localhost:3000), pick a business unit
from the dropdown in the header, and ask something like:

- **MCN TV**: *"How much lead time do I need to book a prime time ad slot?"*
- **MCN+**: *"How many days before a licensed title's expiry should we
  decide on renewal?"*
- **MCN News**: *"How often must a reporter post updates on a developing
  breaking news story?"*

## Testing

`.github/workflows/ci.yml` runs on every push/PR to `main`:

- Unit tests — `backend/tests/` and each `mcp_servers/<unit>/tests/`
  (`pytest`, no live infra needed; run locally with
  `docker compose run --rm <service> pytest tests/` after installing
  `requirements-test.txt`).
- One integration test — brings up the full stack, migrates/seeds MCN TV,
  and hits the real Chat Endpoint end-to-end
  (`backend/tests/test_chat_integration.py`).
- A build check for all 6 Dockerfiles (no push) and the frontend's
  `npm run build` (catches TypeScript regressions — this exact check
  caught a real Next.js/TypeScript incompatibility earlier in this
  project's history, see [`frontend/CLAUDE.md`](frontend/CLAUDE.md)).

## CI/CD & Production Deployment

`.github/workflows/release.yml` triggers on a pushed tag (`v0.1.0`, etc.):
builds and pushes all 6 images to GHCR, then copies
[`infrastructure/docker-compose.prod.yml`](infrastructure/docker-compose.prod.yml)
and [`infrastructure/Caddyfile`](infrastructure/Caddyfile) to the VM (flattened
into `VM_DEPLOY_PATH`) and deploys over SSH. **Caddy** routes internally
by domain to `frontend`/`backend-api` on host port `8081` — public
TLS/80/443 is owned by the VM's existing Nginx Proxy Manager (or
whatever reverse proxy already runs there), not by this stack. See
[ADR-0019](documents/adr/0019-cicd-and-production-deployment.md) and
[ADR-0020](documents/adr/0020-defer-public-tls-to-existing-reverse-proxy.md)
for the full rationale.

To enable this, add these **GitHub repository secrets**
(Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `VM_HOST` | The VM's IP address or hostname |
| `VM_USER` | SSH user with Docker access on the VM |
| `VM_SSH_KEY` | Private key for that user (public half added to the VM's `~/.ssh/authorized_keys`) |
| `VM_DEPLOY_PATH` | Directory on the VM where `docker-compose.prod.yml`/`Caddyfile` live (e.g. `/home/<user>/nova`) |
| `OPENROUTER_API_KEY` | Used by `ci.yml`'s integration test (a small real cost per CI run) |
| `TAVILY_API_KEY` | Same |
| `DOMAIN_API` | e.g. `api.nova.irfani.me` — baked into the frontend image at build time as `NEXT_PUBLIC_BACKEND_URL` (see below), since Next.js inlines `NEXT_PUBLIC_*` vars at build, not at container runtime |

Before the first deploy, on the VM itself:

1. Create `VM_DEPLOY_PATH` and, inside it, a `.env` file (copy
   `.env.example`, fill in **real** production values — `GHCR_OWNER`
   = your GitHub username/org, `DOMAIN_FRONTEND`/`DOMAIN_API`, DB
   passwords, `OPENROUTER_API_KEY`, `TAVILY_API_KEY`). This file is never
   generated or copied by CI/CD — it's a one-time manual step per VM.
2. Point DNS **A records** for `DOMAIN_FRONTEND` and `DOMAIN_API` at the
   VM's public IP.
3. In your reverse proxy's UI (e.g. Nginx Proxy Manager), add a Proxy Host
   for each domain, both forwarding to the VM's own address on port
   `8081` (Caddy) — enable SSL there, since that's what owns public
   TLS for this deployment, not Caddy (ADR-0020). Pick whatever host port
   is actually free on your VM; `8081` was chosen here because `8080` was
   already taken by another service.

Then push a tag: `git tag v0.1.0 && git push origin v0.1.0`. After the
first successful deploy, run the one-off setup commands (Section 3 above)
against the VM's stack — Alembic migrations run automatically on every
deploy, but Postgres/Qdrant seeding stays a manual first-time step, same
as local dev.

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
- **The test suite encodes real bugs, not padding** — `test_mcp_client.py`
  is a permanent regression test for two actual crashes found during
  manual verification (a cross-business-unit tool-scoping bug and a tool
  name collision), and `test_cache.py` regression-tests the tuple/list
  JSON round-trip bug mentioned above. Every new workflow/config file
  (`ci.yml`, `docker-compose.prod.yml`, `Caddyfile`) was validated locally
  before being trusted — the pytest suites were run directly via
  `docker compose run`, the compose file via `docker compose config`, and
  the Caddyfile via `caddy validate` — rather than assuming YAML written
  correctly on the first pass actually works.
