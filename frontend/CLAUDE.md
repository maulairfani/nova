# frontend/ — Nova's Chat UI

Minimal Next.js (App Router) chat interface. Talks directly to the Backend
API over SSE (ADR-0017) — no server-side proxy route, no server components
hitting the backend (the whole thing is a client component, `ChatWindow`).

## Structure

```
app/page.tsx, layout.tsx     Root page/layout
components/
  ChatWindow.tsx              Owns message state + thread_id; the identity header
  MessageBubble.tsx            Renders one message (minimal inline markdown)
  ChatInput.tsx                 Textarea + send button
lib/
  streamChat.ts                POST + manual SSE parsing
  renderInlineMarkdown.tsx      Bold/italic/code only — not a full markdown renderer
```

## Phase-1 simplifications

- **`BUSINESS_UNIT = "tv"` is hardcoded** in `ChatWindow.tsx`. No real
  identity/login exists yet (see `backend/CLAUDE.md`) — this is the
  dummy identity forwarded as `X-Nova-Business-Units`. Phase 2 (once
  MCN+ and MCN News exist) needs a real way to pick/authenticate identity
  here, not a hardcoded string.
- **No thread persistence across page reloads.** `thread_id` is generated
  once via `crypto.randomUUID()` in component state — refreshing the page
  starts a new conversation even though the backend's conversation history
  would still be there under the old thread_id. Not required for this
  phase's acceptance bar (TDD §6.1).
- **Minimal inline markdown only** (`lib/renderInlineMarkdown.tsx`) — bold,
  italic, inline code. No lists/headings/links rendering. Added because the
  LLM's answers use `**bold**` for emphasis and rendering it literally
  looked unpolished; a full markdown library was judged unnecessary for a
  single chat bubble's worth of formatting.

## Known toolchain issue (fixed, documented so it doesn't recur)

`typescript@7.x` (latest at the time of writing) crashes Next.js 16's
internal build-time TypeScript check with an opaque
`The "id" argument must be of type string. Received undefined` error —
even though `tsc --noEmit` itself passes cleanly. Root cause: Next's
internal tsconfig-handling code isn't yet compatible with TypeScript 7's
changed API surface (a very recent major version). Fix: pin
`typescript` to `5.9.3` (see `package.json`) — don't bump past TS 5.x
here until Next.js's own compatibility catches up.

Also: `baseUrl` in `tsconfig.json` was removed in TypeScript 7 and is
invalid even under 5.9.3's stricter validation in this project's
configuration — path aliases (`@/...`) aren't used here; everything
imports via relative paths instead, deliberately, to sidestep this class
of bundler/tsconfig alias-resolution issue entirely.

## Running locally without Docker

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_BACKEND_URL
npm run dev
```
