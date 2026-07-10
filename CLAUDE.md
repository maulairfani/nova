# CLAUDE.md

Guidance for Claude Code (or any AI coding agent) working in this repository.

## Project

**Nova** is an internal AI assistant for **MCN Group**, a media &
entertainment conglomerate. Nova answers employee questions by drawing on:

1. **Internal knowledge base** — Markdown documents (company info, SOPs,
   documentation) — retrieved via RAG.
2. **Company data in PostgreSQL** — the single source of truth for analytics
   and decision-making, queried via a data/analytics tool.
3. **Web search** — for external knowledge not covered by internal sources.

## About MCN Group

MCN Group is a fictional media & entertainment conglomerate with four
business units:

1. **MCN TV** — Free-to-Air (FTA) broadcasting
2. **MCN+** — OTT streaming platform
3. **MCN+ Shorts** — micro-drama / vertical short-form video
4. **MCN News** — news media division

All company details, documents, and data in this repo are fictional dummy
content created for Nova's knowledge base and analytics demos. Nothing here
represents a real company.

## Repository structure

```
backend/           # API server
frontend/          # Web UI
infrastructure/    # IaC / deployment configs (Docker, migrations, etc.)
documents/          # Technical Design Document + business overview docs
docker-compose.yaml
README.md          # short description, tech stack rationale, build/run steps
```

## Tech stack (current plan)

- **Backend**: Python (FastAPI) — strong RAG/LLM ecosystem, async support.
- **Frontend**: Next.js (React) — chat UI, streaming responses.
- **Database**: PostgreSQL (+ pgvector for embeddings) — doubles as the
  analytics source of truth and the vector store for RAG.
- **Cache**: Redis — response/session cache, also usable as a broker.
- **Async worker / queue**: Redis + Celery (or arq) — for document ingestion,
  embedding jobs, and long-running web search calls.
- **MCP server**: expose internal tools (KB search, SQL analytics, web
  search) as MCP tools so Nova's LLM agent calls them uniformly.
- **Containerization**: Docker + docker-compose for local orchestration.

Treat this list as a working default — update it (and `documents/`) if a
choice changes.

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

Not yet scaffolded. Next: business overview document, then the Technical
Design Document, then implementation.
