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
  plus one shared `nova_core` instance for conversation state — [ADR-0003](documents/adr/0003-relational-database.md)
- **Vector DB**: Qdrant — one shared deployment, one collection per business
  unit — [ADR-0004](documents/adr/0004-vector-database.md)
- **Cache / broker**: Redis — [ADR-0006](documents/adr/0006-cache.md)
- **Async worker**: Celery (+ Redis broker) — document ingestion pipeline,
  triggered by a real MinIO webhook, shared across business units —
  [ADR-0007](documents/adr/0007-async-worker-queue.md), [ADR-0022](documents/adr/0022-document-ingestion-pipeline.md)
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
against the live SSE endpoint, and a real headless-browser pass (screenshot + zero console errors). 3 new tech decisions surfaced during this phase and
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

**GitHub Actions CI/CD + production deployment — complete and verified
locally (ADR-0019)**: this project's first test suite (`ci.yml`) covers
unit tests for `backend/` and all 4 `mcp_servers/*/` (24 + 10 tests,
including permanent regression tests for the two real bugs found during
phase 2/shared-server work — tool-scoping crash and tool name collisions)
plus one real integration test hitting a live chat request end-to-end. All
tests run and pass locally before being wired into workflow YAML.
`release.yml` (tag-triggered `v*.*.*`) builds and pushes all 6 images to
GHCR, then deploys over SSH to the user's own VM behind **Caddy**
(automatic TLS for a real domain) via `docker-compose.prod.yml`. Both
`docker-compose.prod.yml` and the `Caddyfile` were validated locally
(`docker compose config`, `caddy validate`) — the SSH/DNS parts can't be
verified from here and depend on the user adding GitHub secrets
(`VM_HOST`, `VM_USER`, `VM_SSH_KEY`, `VM_DEPLOY_PATH`,
`OPENROUTER_API_KEY`, `TAVILY_API_KEY`) and DNS A records for
`DOMAIN_FRONTEND`/`DOMAIN_API`. TDD §7 (deployment view), §9 (ADR index),
and §11 (risks) updated accordingly.

**`nova_kb` renamed to `nova_core`** (its actual scope: identity, auth,
conversation state - not just KB metadata) plus a new identity/access
schema (ADR-0021): `users`, `business_units` (now including a virtual
`group` entry for MCN Group corporate-level claims), `business_unit_roles`
(`employee`/`finance`/`admin` - a unit-agnostic permission tier, not a
unit-prefixed role name), and `user_business_units` (the single
membership+tier claim table covering both unit-specific and MCN
Group-level access). `backend/` gained its own Alembic setup
(`app/models.py` as the SQLAlchemy source of truth, migrations generated
via autogenerate rather than hand-written like the per-unit MCP servers'),
with an `include_object` filter so autogenerate never touches LangGraph's
own checkpoint tables. This is prep work, not auth itself - phase 1's
unverified-header identity (`backend/CLAUDE.md`) is unchanged until the
real login/JWT work lands.

**Real authentication — complete and verified end-to-end**: `POST
/api/v1/auth/login` (email+password against `users`, no signup - accounts
are seeded via `backend/seed_users.py`, see `backend/SEED_USERS.md`)
issues a JWT with `business_units`/`role` claims embedded at login time.
`api/v1/deps.py` verifies that JWT on every Chat Endpoint request and
derives the `X-Nova-*` header shape each MCP server's `AuthContext`
already expected — replacing phase 1's unverified header pass-through
entirely (not just documenting it as a known gap anymore). Two real bugs
surfaced in `mcp_client.py` while wiring this up (an identity with no
business-unit claim got zero tools including web search; `group_admin`
never actually got cross-unit access despite each unit's own auth check
allowing it), both fixed and covered by regression tests
(`backend/tests/test_mcp_client.py`, `test_auth.py`) — see
`backend/CLAUDE.md` for details. The Frontend gained a login page
(`app/login/page.tsx`, `lib/auth.ts`) and lost its manual business-unit
dropdown entirely — which unit(s) an identity can access is now purely a
function of the JWT's claims, with `ChatWindow` showing them read-only.
Verified via curl (login + chat with the issued token, for `tv/employee`,
`group/employee`, `group/admin`, and a two-unit membership) and a real
browser pass (login → chat → logout) before and after fixing a Dockerfile
`ARG`-default-value bug the browser test surfaced (documented in
`frontend/CLAUDE.md`).

**Document ingestion pipeline — complete and verified end-to-end
(ADR-0022)**: a real MinIO bucket-notification webhook (not polling or a
manual trigger) now drives ingestion, matching TDD §6.5's original design
rather than each unit's `seed_qdrant.py` bypass (left in place as a fast
local-bootstrap path, not retired). New top-level `worker/` runs two
processes from one image/codebase: `ingestion-webhook` (a small FastAPI
Celery producer MinIO's webhook POSTs to) and `worker` (the Celery
consumer that downloads the object from MinIO, parses it — Markdown via
header-split, PDF via `pypdf` + paragraph-grouped chunking — embeds each
chunk, upserts into that business unit's Qdrant collection, and
records/updates a row in a new `documents` table in `nova_core`, owned by
`backend/`'s existing Alembic setup but written to by `worker/` using the
same trusted internal credentials). One-off setup:
`docker compose run --rm worker python bootstrap_buckets.py` (creates the
3 buckets, subscribes each to the webhook). Verified by uploading a real
seeded MCN TV SOP (Markdown) and a freshly-generated test PDF directly via
MinIO — both triggered ingestion automatically end-to-end with no manual
step, and a live chat question against the PDF's content came back
correctly grounded and cited before the test artifacts were cleaned up.

**Frontend redesign + real conversation history — complete and verified
end-to-end**: the chat UI was redesigned to a warm editorial visual
system matching MCN Group's brand (design authored in Claude Design,
implemented as real Next.js/React components — see `frontend/CLAUDE.md`)
and gained a proper app shell: a sidebar with searchable conversation
history grouped by recency, inline rename/delete, and a Settings view
(profile, light/dark theme toggle, log out). This required real backend
work, not just a frontend restyle: phase 1's `thread_id` was regenerated
on every page load with nothing to list, so a new `Conversation` model +
migration (`backend/app/models.py`, sidebar metadata only - title,
owner, recency) plus a new `conversations.py` endpoint (list/rename/
delete, and a read of a thread's message history straight from the
LangGraph checkpointer's stored state rather than rebuilding the whole
agent) now back the sidebar for real. `chat.py` upserts that row's title
(from the first message) and `updated_at` on every message. Deleting a
conversation purges both the metadata row and the checkpointer's own
thread via `adelete_thread` - leaving only one would either orphan
unlistable LangGraph state or leave a sidebar entry pointing at nothing.
Deliberately descoped from the design mock: citation chips and stat-grid
cards on assistant messages (the backend's chat SSE stream only emits
token deltas today, no structured citation metadata to render) and
Settings' "clear all history" control. Verified via the full backend
unit suite (17/17, no regressions), the new Alembic migration applied
against a real `nova_core`, a clean Next.js production build, and a live
`docker compose` stack exercised end-to-end via curl: login → send a
message → conversation appears in the list with an auto-derived title →
rename → fetch its full message history (both turns, correctly
persisted) → delete (row and checkpointer thread both gone).

**Visible tool-call steps + Manage Documents — complete and verified
end-to-end**: a second Claude Design pass on the Nova Chat project added
two features, both implemented as real functionality rather than just
UI. (1) The chat UI now shows which tools the agent called for each
answer (e.g. "Searched MCN TV knowledge base") as a collapsible trace -
`chat.py`'s SSE stream forwards `on_tool_start`/`on_tool_end` events
(new `tool_start`/`tool_end` event types alongside the existing token
deltas), mapped to human-readable labels by a name convention already in
place (`tv_kb_search` → "Searched MCN TV knowledge base") in a new
`app/agent/tool_labels.py`, shared with `conversations.py`'s history
reconstruction so a reloaded past conversation shows the same steps a
live one did. (2) A "Manage documents" sidebar item opens a real CRUD
screen for each business unit's knowledge base source files
(`backend/app/api/v1/endpoints/documents.py`) - this is the first real
use of `business_unit_roles`' `admin` tier anywhere in the codebase
(stored since ADR-0021, never enforced until now): unit admins manage
only their own unit, `group_admin` manages every unit, everyone else
gets read-only browsing. Upload writes directly into the real ingestion
pipeline's MinIO bucket (ADR-0022) rather than a parallel path - the
existing webhook → Celery → parse/embed/upsert flow runs unchanged, with
one addition: the endpoint pre-creates the `documents` row with a
caller-chosen title before the object lands, and `worker/db.py`'s
`insert_pending`/`mark_ingested` were changed to get-or-create by
`(business_unit_code, object_key)` (new unique constraint, migration
`0004`) and never clobber a human-provided title with the parser's
extracted one. Delete removes the Qdrant points, the MinIO object, and
the database row, in that order. Verified against the live stack: a
real chat request's tool-step SSE events and their reconstruction from a
reloaded conversation; an employee getting 403 on upload but a normal
list; a `group_admin` uploading with a custom title, watching it fail
ingestion with a real error (empty test file - confirming the get-or-create
path and title preservation on the failure branch), then succeeding with
real content (title preserved through `mark_ingested`, 2 chunks embedded),
then deleting it cleanly.

**KB seeding moved onto the real ingestion pipeline — the old
direct-to-Qdrant bypass is gone**: `mcp_servers/{tv,plus,news}/seed/seed_qdrant.py`
(and their `seed/documents/` markdown files) were retired, per that
script's own long-standing note that it should be retired once the real
pipeline existed, not kept alongside it — now that Manage Documents
exposed the gap concretely (seed-bypassed docs never had a `documents`
row, so they were invisible in that screen despite being searchable).
The project's dummy SOP docs now live at `documents/kb/<unit>/` (repo
root, one shared location instead of duplicated per MCP server) — mostly
PDF now, one Markdown file per unit, to exercise both of `worker/`'s
parser paths with real content. The 6 that changed format were
regenerated as real, text-extractable PDFs (not scanned images) from
their original Markdown. A new `worker/seed_documents.py` uploads them
into each unit's MinIO bucket, the same real path (webhook → Celery →
parse/embed/upsert) any other upload takes — no code path in the
codebase writes to Qdrant directly anymore. `README.md` and CI
(`.github/workflows/ci.yml`) were updated to match, including a new CI
step that polls the `documents` table for `ingested` status before
running the integration test, since ingestion is now asynchronous where
the old bypass was synchronous.

Seeding 9 documents at once (3 per unit, concurrently) surfaced two real
bugs in `worker/` that single-file testing never had — both fixed and
documented rather than silently patched: (1) `ensure_collection`'s
`collection_exists` → `create_collection` was never atomic, so two
Celery tasks racing to create the same not-yet-existing collection had
the loser crash on Qdrant's `409 Conflict` instead of treating "already
exists" as success — fixed in both the live copy
(`worker/qdrant_helper.py`) and the now-dead duplicate
(`mcp_servers/common/qdrant_client.py`, which lost its only caller when
`seed_qdrant.py` was deleted and had its own `ensure_collection` removed
outright rather than fixed-and-left-unused). (2) `mark_ingested` never
cleared a prior `error_message` on a successful retry, so a document
that failed once and later succeeded still showed a stale error in
Manage Documents despite `status: ingested`.

**Still outstanding**: `business_unit_roles`' `finance` tier and the
`admin` tier's enforcement in each MCP server's SQL Analytics Tool are
stored and forwarded but not enforced (ADR-0021's Consequences) - every
unit member currently gets the same *data-query* access regardless of
tier (the `admin` tier is now enforced for document management, above -
a separate authorization surface, not the same gap). Also still pending:
the cross-business-unit synthesis flow (TDD §6.3, now practical to build
with real multi-unit identities like `fajar.nugroho@mcngroup.example`);
the design mock's inline document preview (Markdown/PDF viewer) was
descoped from the Manage Documents build.
