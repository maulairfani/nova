# frontend/ — Nova's Chat UI

Minimal Next.js (App Router) chat interface. Talks directly to the Backend
API over SSE (ADR-0017) — no server-side proxy route, no server components
hitting the backend (the whole thing is a client component, `ChatWindow`).

## Structure

```
app/
  page.tsx, layout.tsx        Root page/layout — renders ChatWindow
  login/page.tsx               Login form — email+password, no signup (ADR-0021)
components/
  ChatWindow.tsx              Owns message state + thread_id; redirects to /login if no
                              valid token; shows the identity's business units read-only
                              (no manual unit picker — see below)
  MessageBubble.tsx            Renders one message (minimal inline markdown)
  ChatInput.tsx                 Textarea + send button
lib/
  auth.ts                      login()/logout(), stores the JWT in localStorage, decodes its
                              claims client-side for display only (the backend is what
                              actually verifies the signature, api/v1/deps.py)
  streamChat.ts                POST + manual SSE parsing, sends the JWT as `Authorization: Bearer`
  renderInlineMarkdown.tsx      Bold/italic/code only — not a full markdown renderer
```

## Auth (ADR-0021)

No signup — accounts are seeded on the backend (`backend/seed_users.py`,
`backend/SEED_USERS.md`). `login()` posts to `/api/v1/auth/login` and
stores the returned JWT in `localStorage`; `ChatWindow` redirects to
`/login` if `getClaims()` finds no valid (unexpired) token. There is
**no manual business-unit selector anymore** — which unit(s) an identity
can access is entirely a function of the JWT's `business_units` claims,
decoded client-side just to render a read-only badge
(`"Andi Wijaya · MCN TV"`). A 401 from `/chat` (expired/invalid token,
`streamChat.ts`'s `UnauthorizedError`) also redirects to `/login`.

## Other simplifications

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

## NEXT_PUBLIC_BACKEND_URL is a build-time value, not a runtime one

`NEXT_PUBLIC_*` env vars are inlined into the client JS bundle by
`npm run build` — setting `NEXT_PUBLIC_BACKEND_URL` as a container
`environment:` entry (e.g. in `docker-compose.prod.yml`) has no effect,
since the bundle was already built without it. In production this is
passed as a Docker **build-arg** instead (`ARG`/`ENV` pair in
`Dockerfile`, supplied by `release.yml` via the `DOMAIN_API` GitHub
secret) so `https://api.<domain>` gets baked in before `npm run build`
runs. First deploy shipped without this and the browser tried (and
CORS-failed) to reach the `http://localhost:8000` fallback in
`lib/streamChat.ts` from a public HTTPS page.

**Gotcha found afterward:** a Dockerfile `ARG NAME` with no default value
resolves to an **empty string**, not `undefined` — and
`process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"`'s `??`
only falls back on `null`/`undefined`, not `""`. Adding the build-arg
plumbing above without giving the `ARG` a default silently broke local
dev builds (no `--build-arg` passed there): the bundle baked in `""`
instead of the intended fallback, so every backend request became a
same-origin relative URL, 404ing against the frontend's own server
instead of reaching the backend. Fixed by giving the `ARG` an explicit
default (`ARG NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`) matching
the app code's own fallback, and by changing `lib/auth.ts`/`lib/streamChat.ts`
to `||` instead of `??` as a second line of defense.

## Running locally without Docker

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_BACKEND_URL
npm run dev
```
