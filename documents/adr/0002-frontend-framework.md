# ADR-0002: Frontend Framework — Next.js

**Status:** Accepted

## Decision

Use **Next.js (React)** for the Frontend.

## Context

Section 2 constrains the frontend to React or Next.js. The Frontend's job
is narrow: a chat UI that streams responses (Section 1.2 Usability
discussion — chat UIs are now a familiar, largely solved UX pattern).

## Alternatives Considered

- **Plain React (e.g. Vite + React)** — lighter weight, but Next.js's
  built-in routing, server components, and streaming support map directly
  onto "render a chat UI that streams tokens" with less boilerplate.

## Rationale

Next.js was chosen over plain React because it comes with streaming-aware
primitives out of the box (matching the Backend API's streamed responses,
Section 8) and because it's the more common default for internal tools
built quickly by a small team — less setup than assembling a React app
from scratch.

## Consequences

- Positive: fast to scaffold; built-in support for the streaming UX Nova
  needs.
- Negative: brings more framework surface area than a bare React app would
  need for a single-page chat UI — accepted as a low-cost trade-off.
