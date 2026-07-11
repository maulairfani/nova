# ADR-0017: Streaming Transport — Server-Sent Events

**Status:** Accepted

## Decision

Use **Server-Sent Events (SSE)** for Frontend ↔ Backend API streaming
(TDD Section 8 left this open: "Server-Sent Events or WebSocket").

## Context

Nova's Chat Endpoint (TDD Section 5.2) streams the agent's answer back to
the Frontend token-by-token. The TDD explicitly deferred the exact
transport choice to implementation time.

## Alternatives Considered

- **WebSocket**: bidirectional, supports server-initiated push without a
  new request. Rejected for this phase — the flow is unidirectional per
  turn (client sends one message, server streams one response), so
  WebSocket's extra complexity (connection lifecycle, reconnect handling)
  buys nothing yet. Worth revisiting if phase 2's async ingestion pipeline
  needs to push status updates to an open client session without a new
  request.

## Rationale

FastAPI's `StreamingResponse` with `text/event-stream` maps directly onto
LangGraph's `astream_events()` async generator — no protocol translation
layer needed. On the Next.js side, since the request is a `POST` (not a
`GET`), the native `EventSource` API doesn't apply (it only supports GET);
the Frontend reads the response body as a stream via `fetch()` and a
manual `ReadableStream` reader instead — a standard, well-documented
pattern for POST+SSE, not a workaround unique to this project.

## Consequences

- Positive: no extra library on either side (FastAPI's built-in streaming
  response type; the browser's built-in `fetch`/`ReadableStream`).
- Positive: matches the request/response, one-shot-per-turn shape of the
  chat flow exactly — no unused bidirectional capability sitting idle.
- Negative: if a future feature needs the server to push data outside of
  an active request/response cycle (e.g. ingestion-status notifications,
  TDD Section 6.5), SSE alone won't cover it — would need a second
  mechanism (polling, or a WebSocket added specifically for that feature)
  rather than reusing this one.
