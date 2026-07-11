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
infrastructure/    # IaC / deployment configs (Docker, migrations, etc.)
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
- **LLM provider**: Anthropic Claude — [ADR-0009](documents/adr/0009-llm-provider.md)
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

Not yet scaffolded otherwise — next is implementation: `backend/`,
`frontend/`, `infrastructure/`, `docker-compose.yaml`.
