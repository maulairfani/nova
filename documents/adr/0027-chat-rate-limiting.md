# ADR-0027: Chat Rate Limiting

**Status:** Accepted

## Decision

Enforce a per-user rate limit of **30 requests per rolling 5-hour window** on
`POST /api/v1/chat` only, uniformly for every user with no exemptions. It's
implemented as a Redis-backed fixed-window counter (`INCR` + `EXPIRE ... NX`),
exposed as a FastAPI dependency (`check_rate_limit`, `app/api/v1/deps.py`)
raising `HTTPException(429)` with `Retry-After`/`X-RateLimit-*` headers when
exceeded. Clients can also read `X-RateLimit-*` headers off every successful
chat response, and a dedicated read-only `GET /api/v1/usage` endpoint exposes
the same status for the frontend's Settings view — polling it never itself
consumes quota.

## Context

`/chat` is the only endpoint that incurs real cost: every request drives an
LLM call through OpenRouter (ADR-0009/0015/0018). Before this, any
authenticated user could send unlimited messages, with no per-user cost or
abuse control. Other endpoints (conversation listing, document management,
settings) are metadata/CRUD against Nova's own databases — not cost-bearing —
so the limit is deliberately scoped to chat only, not applied as blanket API
middleware. Redis is already deployed as Nova's cache and Celery broker
(ADR-0006), so this adds no new infrastructure.

## Alternatives Considered

- **Sliding-window log** (`ZADD`/`ZREMRANGEBYSCORE` per request) — more
  precise at the boundary, but more Redis operations and memory per user
  than this guardrail needs.
- **Token bucket** — smoother request pacing, but harder to present as the
  simple "used X of 30, resets in Xh Ym" progress bar the product requires;
  a fixed window with a visible reset point was the actual requirement, not
  smoothing.
- **Global ASGI middleware** instead of a route-scoped FastAPI dependency —
  would still need the same "only /chat" branching, and breaks from this
  codebase's existing per-route `Depends()` convention for cross-cutting
  concerns (`get_current_user_id`, `get_auth_headers`).
- **In-process/in-memory counter** — doesn't survive a backend restart and
  wouldn't be consistent across multiple `backend-api` replicas, a case
  Redis-backed state avoids for free.
- **Client-side-only enforcement** — trivially bypassed (curl, devtools);
  the frontend's proactive composer-disable is a UX layer on top of the
  real server-side boundary, not a substitute for it.
- **Postgres-backed counter** (`nova_core`) — works, but adds write load for
  a purely ephemeral, self-expiring value, and would need a cleanup job
  Redis's native TTL provides for free.
- **`INCR` + `EXPIRE ... NX`** (chosen) **vs. `SET key 1 EX ... NX`** (a
  `GET`-then-conditional-write has a real TOCTOU race window under
  concurrent sends) **vs. a Lua script** (would be the only Lua in this
  codebase — no precedent, and an unfamiliar debugging surface for a
  problem `INCR`+`EXPIRE NX` already solves atomically). `INCR` is atomic
  under Redis's single-threaded command execution; calling `EXPIRE ... NX`
  unconditionally after every increment arms the window exactly once and
  self-heals a key that ever ended up without a TTL.

## Rationale

Fits existing infrastructure with zero new services. Matches the codebase's
established `Depends()`-based dependency convention exactly (no custom
exception classes — a plain `HTTPException` with a `headers` dict, same as
every other error path in this codebase). Atomic and race-free under
concurrent requests from the same user. Self-expiring, needing no cleanup
job. Small new surface: one core module, one dependency, one read-only
status endpoint, two lines of CORS config.

## Consequences

- Positive: guards LLM spend with minimal new code; simple mental model for
  users ("22/30 used, resets in 2h 15m"); would keep working correctly if
  `backend-api` ever ran multiple replicas, since the counter lives in
  shared Redis rather than per-process memory.
- Negative: a fixed (non-sliding) window has the standard boundary-burst
  characteristic — a user could in principle send close to 60 requests
  straddling a reset instant. Accepted, since a fixed, non-calendar-aligned
  window (reset 5 hours after a user's *own* first request, not a shared
  clock-aligned boundary) was the actual requirement, not a stricter
  sliding guarantee.
- Negative: `business_unit_roles`' `admin`/`finance` tiers (ADR-0021) get no
  special treatment here — the limit is genuinely uniform per user, as
  specified. A future tiered limit (e.g. higher quota for `admin`) would be
  a new ADR, not a silent edit to this one.
