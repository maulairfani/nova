# CLAUDE.md

Guidance for Claude Code (or any AI coding agent) working in this repository.

## Project

**Nova** is an internal AI assistant for **MCN Group**, a media &
entertainment conglomerate. Nova answers employee questions by drawing on:

1. **Internal knowledge base** — documents (company info, SOPs,
   documentation) — retrieved via RAG.
2. **Company data**, owned per business unit — queried live via
   text-to-SQL, no consolidated warehouse (see Data Mesh note below).
3. **Web search** — for external knowledge not covered by internal sources.

Full architecture and rationale: [`documents/technical-design-document.md`](documents/technical-design-document.md)
and the ADRs under [`documents/adr/`](documents/adr/) — read those before
making any non-trivial change here, since they're the source of truth for
*why* the system is shaped this way.

## About MCN Group

MCN Group is a fictional media & entertainment conglomerate with three
business units:

1. **MCN TV** — Free-to-Air (FTA) broadcasting
2. **MCN+** — one business unit spanning two products: OTT streaming and
   MCN+ Shorts (micro-drama / vertical short-form video) — see ADR-0014
3. **MCN News** — news media division

All company details, documents, and data in this repo are fictional dummy
content created for Nova's knowledge base and analytics demos. Nothing here
represents a real company.

**Data Mesh architecture:** each business unit owns its own analytics data
and documents, exposed through its own MCP server — there is no
centralized data warehouse. See ADR-0005 for the full rationale. This is
the single most important architectural fact about Nova; most of the
system's shape follows from it.

## Repository structure

```
backend/           # API server
frontend/          # Web UI
mcp_servers/       # one FastMCP server per business unit + one shared — each
                   # owns its own Alembic migrations (ADR-0016), colocated
                   # since only that server ever connects to its database
infrastructure/    # cross-cutting deployment config (docker-compose is at
                   # root; this is for anything else infra-level, not
                   # per-service schema migrations — those live in
                   # mcp_servers/<unit>/alembic/)
documents/          # Technical Design Document + business overview docs
docker-compose.yaml
README.md          # short description, tech stack rationale, build/run steps
```

## Tech stack

Decided via ADRs under [`documents/adr/`](documents/adr/) — this is a
summary, not the source of truth:

- **Backend**: Python (FastAPI) — [ADR-0001](documents/adr/0001-backend-framework.md)
- **Frontend**: Next.js (React) — [ADR-0002](documents/adr/0002-frontend-framework.md)
- **Relational DB**: PostgreSQL — one instance per business unit (domain-owned)
  plus one shared `nova_kb` instance for conversation state — [ADR-0003](documents/adr/0003-relational-database.md)
- **Vector DB**: Qdrant — one shared deployment, one collection per business
  unit — [ADR-0004](documents/adr/0004-vector-database.md)
- **Cache / broker**: Redis — [ADR-0006](documents/adr/0006-cache.md)
- **Async worker**: Celery (+ Redis broker) — document ingestion pipeline,
  shared across business units — [ADR-0007](documents/adr/0007-async-worker-queue.md)
- **MCP server framework**: FastMCP — one MCP server per business unit
  (KB search + SQL analytics tools) plus one shared MCP server (web search)
  — [ADR-0008](documents/adr/0008-mcp-server-framework.md)
- **LLM**: OpenAI `gpt-5.4-nano` via OpenRouter — [ADR-0009](documents/adr/0009-llm-provider.md),
  [ADR-0015](documents/adr/0015-llm-embedding-gateway-openrouter.md),
  [ADR-0018](documents/adr/0018-llm-model-change-gpt-5-4-nano.md)
- **Web search provider**: Tavily — [ADR-0010](documents/adr/0010-web-search-provider.md)
- **Object storage**: MinIO — one shared deployment, one bucket per business
  unit — [ADR-0011](documents/adr/0011-object-storage.md)
- **Agent framework**: LangChain/LangGraph, ReAct pattern via
  `langchain.agents.create_agent` — [ADR-0012](documents/adr/0012-agent-orchestration-framework.md),
  [ADR-0013](documents/adr/0013-agent-pattern.md)
- **Containerization**: Docker + docker-compose — single host for this
  build (Section 7 of the TDD)

If a choice changes during implementation, update the corresponding ADR
(new ADR that supersedes it — never silently edit an accepted one) and
this summary.

## Working conventions

- **All design work must be framework-based, not ad-hoc.** Pick or state the
  framework being used before designing, so reasoning stays structured and
  defensible: architecture docs/diagrams follow **arc42** (structure) + **C4
  Model** (diagrams: Context → Container → Component); significant tech
  choices are recorded as **ADRs** (Decision / Context / Alternatives
  Considered / Rationale). Apply the same discipline to other design work
  (data model, API design, etc.) — state the framework, then design within it.
- Every architectural decision must be explainable: prefer well-known,
  simple patterns over clever ones.
- Use dummy/synthetic data for the knowledge base and PostgreSQL tables.
- Keep the root README.md current: short description, tech stack
  explanation, and how to build/run via docker-compose.
- No secrets committed. Use `.env.example` files for required environment
  variables.

## Status

Technical Design Document complete and ready for review
(`documents/technical-design-document.md`, 14 ADRs under `documents/adr/`).
No open design questions remain — FastMCP's authorization mechanism
(ADR-0008) is resolved: callable-based auth checks, one check function per
business unit MCP server. Remaining authorization work is
implementation-level only (writing/testing each unit's actual rules, see
TDD Section 11), not a design gap.

**Business-unit count corrected from 4 to 3** (ADR-0014): MCN+ and MCN+
Shorts are one business unit with two products, not two separate units —
they share one MCP server, one database, one Qdrant collection. This
correction was made during Q2 planning, before any code was written; the
TDD and company profile have been updated accordingly.

**Q2 implementation — phase 1 vertical slice complete and verified
end-to-end**: MCN TV + the knowledge-base question flow (TDD §6.1) runs
fully through `docker compose up` — chat UI → Backend API's ReAct agent →
`mcp-tv` → Qdrant/Postgres → grounded, streamed, cited answer. Verified via
real MCP protocol calls, a standalone agent-loop check, Postgres-checkpointer
persistence across separate process runs, a Redis cache-hit check, `curl`
against the live SSE endpoint, and a real headless-browser pass (screenshot
+ zero console errors). 3 new tech decisions surfaced during this phase and
got their own ADRs rather than silent edits: OpenRouter as the LLM/embedding
gateway (ADR-0015), Alembic for schema migrations (ADR-0016), SSE for
streaming (ADR-0017), and a mid-build LLM model change to `gpt-5.4-nano`
(ADR-0018).

**Phase 2 — replicated to all 3 business units, complete and verified
end-to-end**: `mcp_servers/plus/` (MCN+, streaming + shorts merged per
ADR-0014) and `mcp_servers/news/` (MCN News) were built as direct
replications of `mcp_servers/tv/`'s template — same file shape, same
KB Search + SQL Analytics tools, own Postgres DB/readonly role/Alembic
migration/Qdrant collection/3 seeded SOP docs each. Backend's `mcp_client.py` now connects to the caller's claimed business
unit's server(s); two real bugs surfaced here during verification, both
caught by re-checking logs after the browser pass rather than assuming
success from a clean-looking UI: (1) every server exposes
identically-named tools (`kb_search`, `sql_analytics`), so the agent's
combined tool list had name collisions across business units, causing
wrong-server tool calls — fixed by prefixing each tool's exposed name with
its business unit (e.g. `tv_kb_search`, `plus_kb_search`); (2) the tool
list was being built from *every* business unit server regardless of which
single unit the caller was actually authorized for, so the LLM could
attempt a tool on a unit it had no claim to, and that server's auth denial
surfaced as an unhandled exception that crashed the whole SSE
response — fixed by scoping `get_tools_for_identity` to only connect to
server(s) matching the caller's claimed business unit(s) (also the correct
shape for the future cross-unit flow, TDD §6.3, where an identity would
legitimately claim more than one unit). The frontend's `ChatWindow.tsx` gained a
business-unit selector (previously a hardcoded `"tv"` constant) — switching
units starts a fresh conversation thread. Verified via the same discipline
as phase 1: each new MCP server checked standalone (tool calls + auth
allow/deny) before wiring into the backend, the agent checked against each
unit individually, then a full clean-state `docker compose down -v` →
`up -d` → migrate/seed all 3 units → real headless-browser pass asking a
unit-specific question per business unit, confirming grounded answers and a
fresh thread on unit switch. See root `README.md`, `backend/CLAUDE.md`,
`frontend/CLAUDE.md`, and each `mcp_servers/<unit>/CLAUDE.md` for details.

**Shared MCP Server (web search) — complete and verified end-to-end**:
`mcp_servers/shared/` exposes a single `web_search` tool via Tavily
(ADR-0010), used as a fallback when internal sources don't have the
answer (TDD §6.4). Unlike the business unit servers it owns no
database/Qdrant collection — its authorization check
(`check_shared_access`) is intentionally permissive (any caller with a
recognized identity), since results aren't scoped to any unit's data.
Wired into `mcp_client.py` as an always-included server (not filtered by
claimed business unit, unlike `tv`/`plus`/`news`) since web search isn't
unit-owned. A second real bug surfaced here, more general than phase 2's:
`langchain-mcp-adapters` converts *any* MCP tool error (not just auth
denials — an invalid API key, a rate limit, any downstream failure) into
a raised exception, and LangGraph's default tool-error handling re-raises
it, crashing the whole SSE response over one failed tool call. This
mattered specifically for web search because an external API is far more
likely to fail than our own servers. Fixed by having `_wrap_with_cache`
catch any exception from a tool call and return it as tool content
instead — the agent then reports the failure gracefully instead of the
whole request crashing. Verified via raw MCP calls (auth denial, a
deliberate invalid-key failure, then a real Tavily search after the user
added their key), a standalone agent-loop check exercising the failure
path, and a full browser pass asking a live weather question — grounded,
cited, streamed answer — alongside a re-run of all 3 business units
confirming no regression. Also exposed each business-unit Postgres on the
host (`5433`–`5436`) for direct DB-client access (e.g. DBeaver).

**Next**: the cross-business-unit synthesis flow (TDD §6.3, now
practical to build since 2+ live business units and the shared server both
exist), the real MinIO+Celery ingestion pipeline (each unit currently
bypasses it with a one-off seed script), and GitHub Actions CI/CD (see TDD
§11 and the "Not yet built" section of the README).
