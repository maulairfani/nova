# frontend/ — Nova's Chat UI

Next.js (App Router) chat interface with a full app shell (sidebar +
conversation history + settings), styled to a warm editorial design
system matching MCN Group's brand (visual design authored in Claude
Design, implemented here as real components — no design-tool runtime
dependency). Talks directly to the Backend API over SSE (ADR-0017) — no
server-side proxy route, no server components hitting the backend (the
whole thing is a client component tree rooted at `ChatWindow`).

## Structure

```
app/
  page.tsx, layout.tsx        Root page/layout — renders ChatWindow; layout.tsx loads
                              Newsreader (display serif) + Figtree (body sans) via next/font
  login/page.tsx               Login form — email+password, no signup (ADR-0021); split-panel
                              layout (dark MCN Group brand panel + form card)
  globals.css                  Design tokens (--nova-*) for light/dark, both a
                              prefers-color-scheme fallback and an explicit
                              data-theme="light"/"dark" override (Settings' toggle)
components/
  ChatWindow.tsx              App shell orchestrator: owns claims/theme/sidebar-collapsed/
                              conversations/active thread/messages/liveSteps/view ("empty" |
                              "active" | "settings" | "documents") state; redirects to /login
                              if no valid token; shows the identity's business units as plain
                              read-only text (no manual unit picker — see below)
  Sidebar.tsx                  New chat, Manage documents nav item, search, conversations
                              grouped by recency (Today/Yesterday/Previous 7 days/Older),
                              inline rename, delete, collapse; account footer (Settings/Log out)
  SettingsView.tsx             Profile (read-only), Appearance (theme toggle), Session
                              (log out) — no "clear all history" (descoped, see below)
  DocumentsView.tsx             Manage Documents screen: per-unit tabs (only shown if the
                              caller has more than one accessible unit), search, upload
                              (admin-only, per `canManageUnit`), status pills, inline delete
                              confirm, and a preview trigger (click a row's title) — talks to
                              backend/app/api/v1/endpoints/documents.py
  DocumentPreviewModal.tsx      Renders a previewed document's content — Markdown via
                              NovaMarkdown, PDF via an <iframe> over a blob URL (useBlobUrl)
  MessageBubble.tsx            Renders one message (markdown via NovaMarkdown), a typing-dots
                              indicator while the last assistant message is still
                              empty/streaming, a tool-call steps trace (live while streaming,
                              collapsible once finished) via ToolSteps.tsx, any chart
                              images (ChartImage.tsx) the agent generated that turn, and a
                              "N sources" pill (opens SourcesPanel) when the turn retrieved
                              any kb_search/web_search citations — see Sources panel, below
  SourcesPanel.tsx              Slide-in panel (same fixed-overlay convention as the mobile
                              sidebar drawer) listing every citation card for a message —
                              opened via the "N sources" pill or an inline 【Title】 badge
                              (NovaMarkdown), the latter scrolling to/highlighting that
                              specific card; a kb card's "View document" opens the real
                              source in DocumentPreviewModal (via lib/documents.ts's
                              findDocumentByObjectKey)
  ChartImage.tsx                 Fetches a chart image (useBlobUrl) and renders it with a
                              Download link, reusing the already-fetched blob URL
  ToolSteps.tsx                 LiveSteps (open, per-step active/done icon, shown while
                              streaming) and StepsTrace (collapsed-by-default count that
                              expands, shown on a finished message or one reloaded from history)
  ChatInput.tsx                 Textarea + send button
  Sidebar/Header account menu   AccountMenu.tsx, NovaMark.tsx — small shared pieces
lib/
  auth.ts                      login()/logout(), stores the JWT in localStorage, decodes its
                              claims client-side for display only (the backend is what
                              actually verifies the signature, api/v1/deps.py)
  streamChat.ts                POST + manual SSE parsing, sends the JWT as `Authorization: Bearer`;
                              parses the token-delta `data:` frames and the `tool_start`/
                              `tool_end`/`chart`/`citations` SSE event types (matched by
                              run_id, chart by its own chart_id, citations by replacing the
                              whole running list each event) into onToolStart/onToolEnd/
                              onChart/onCitations
  conversations.ts             REST client for backend/app/api/v1/endpoints/conversations.py —
                              list/rename/delete + read a thread's stored message history
                              (each assistant message may carry `steps`, `charts`, and
                              `citations` arrays)
  documents.ts                  REST client for backend/app/api/v1/endpoints/documents.py —
                              list/upload (multipart)/delete
  authenticatedFetch.ts          Shared fetch wrapper for endpoints needing the caller's JWT —
                              `${BACKEND_URL}` + Authorization header + throw-on-non-OK
  useBlobUrl.ts                  Hook: fetches an authenticated endpoint as a Blob, exposes an
                              object URL for <img>/<iframe> (which can't carry auth headers
                              themselves) — shared by ChartImage.tsx and the PDF preview branch
  modalStyles.ts                 The app's one modal convention (dim overlay + centered card),
                              extracted out of DocumentsView.tsx so the preview modal follows it too
  businessUnits.ts               Shared BUSINESS_UNIT_LABELS map (tv/plus/news/group → display name)
  theme.ts                     get/apply the light/dark theme (localStorage, falls back to
                              prefers-color-scheme on first load)
  NovaMarkdown.tsx              Chat-bubble markdown via react-markdown + remark-gfm/remark-breaks
                              (see Markdown rendering, below) — not the old hand-rolled parser
```

## Tool-call steps and Manage Documents

Both additions came from a second Claude Design pass on the same Nova
Chat project (`Nova Chat.dc.html`) and are real, backend-verified
features, not visual-only additions:

- **Tool-call steps**: `ChatWindow` keeps a `liveSteps` ref+state pair
  updated by `streamChat`'s `onToolStart`/`onToolEnd` callbacks during a
  send; once the stream finishes, the accumulated steps are attached to
  the just-finished message (`message.steps`) so `MessageBubble` renders
  `StepsTrace` (collapsed) instead of `LiveSteps` (open) from then on —
  including after a page reload, since `getConversationMessages` returns
  `steps` per historical assistant message too.
- **Manage Documents**: `DocumentsView` computes which business units the
  caller can *view* (their JWT's `business_units`, or all three if
  `group`/`admin`) and which they can *manage* (`admin` tier in that
  specific unit, or `group`/`admin`) entirely from the already-decoded
  JWT claims — the backend independently re-checks the same rules on
  every request (`documents.py`'s `_require_view`/`_require_manage`), so
  the frontend's gating is a UX nicety, not the real authorization
  boundary. Non-admins can browse/search a unit's documents but see no
  upload button and no delete control on any row.
- **Document preview** (built later, once `NovaMarkdown` existed and a
  content endpoint was added — `GET /api/v1/documents/{id}/content`):
  clicking a row's title opens `DocumentPreviewModal`, rendering Markdown
  via `NovaMarkdown` or a PDF via an `<iframe>` over a blob URL
  (`useBlobUrl`). Gated on `_require_view` only (same as list), so any
  unit member can preview, not just admins — unlike upload/delete.

## Chart display (ADR-0026)

When the agent calls the Chart Generation Tool (`mcp-shared`,
matplotlib-rendered, stored in MinIO), the backend emits a `chart` SSE
event (`{chart_id, title, chart_type}`) alongside the existing
`tool_start`/`tool_end` pair. `ChatWindow` accumulates these into
`liveCharts` during a send (mirroring `liveSteps` exactly) and attaches
the finished list to `message.charts` once the turn completes;
`conversations.py`'s history reconstruction does the same from a
reloaded thread's stored `ToolMessage`s, so a chart shows identically
whether it just streamed in or was reloaded from a past conversation.
`MessageBubble` renders each via `ChartImage`, which fetches the image
through the authenticated Chart Endpoint (`GET /api/v1/charts/{chart_id}`)
as a Blob (same `useBlobUrl` hook the PDF preview uses) and offers a
Download link off the same already-fetched blob URL.

## Conversation history is real, not local-only

Unlike phase 1's throwaway `thread_id` (regenerated every page load),
conversations are now backed by a real `conversations` table
(`backend/app/models.py`'s `Conversation`) plus reads against the
LangGraph checkpointer's own stored state (`GET
/conversations/{id}/messages`) — selecting a past conversation from the
sidebar actually loads its prior messages, and deleting one purges both
the metadata row and the checkpointer's thread via `adelete_thread`.
`ChatWindow` still generates a `thread_id` client-side (`crypto.randomUUID()`)
for a brand new chat, same mechanism as before — it's just no longer
discarded on reload once a message has been sent under it.

**Deliberately not built**: the design mock's stat-grid cards on assistant
messages, and Settings' "clear all history" button — both explicitly
descoped during scoping for this pass, not a bug. (Citation chips *are*
now built — see Sources panel + inline citations, below.)

## Sources panel + inline citations (2026-07-18)

Every `kb_search`/`web_search` result the agent retrieves becomes a
citation card, shown two ways: a **"N sources" pill** under a finished
message (`MessageBubble.tsx`), and **inline numbered badges** wherever
the LLM actually cited a source in its answer text. Both open the same
`SourcesPanel.tsx`; clicking an inline badge additionally scrolls to and
highlights that specific card.

- **`lib/NovaMarkdown.tsx`**: the backend's SYSTEM_PROMPT instructs the
  model to mark a cited fact with the source's exact title wrapped in
  full-width brackets, e.g. `【Ad Slot Booking SOP — MCN TV】`
  (`CITATION_MARKER_RE`) - `preprocessCitationMarkers` rewrites each match
  into a markdown link (`[n](#nova-citation-i)`) before handing the text
  to `ReactMarkdown`, numbering by first appearance in the text (not
  retrieval order) so numbers always match what the reader sees
  top-to-bottom. The `a` component override renders that synthetic href
  as a clickable numbered badge instead of a real link.
  - **Real gotcha hit here**: the href was originally a custom scheme
    (`nova-citation:i`) - react-markdown's default `urlTransform` silently
    strips any href scheme outside `http`/`https`/`mailto`/`tel` (XSS
    hardening), so the link rendered with `href=""` and the citation
    logic never fired. Fixed by using a same-page anchor fragment
    (`#nova-citation-i`) instead, which passes through untouched -
    verified by inspecting the actual rendered DOM
    (`.innerHTML`) in a live headless-browser pass, not assumed from
    reading react-markdown's docs.
  - A marker whose title doesn't match any known citation (the model
    paraphrased instead of copying exactly) is dropped silently rather
    than rendered as a broken badge.
- **`ChatWindow.tsx`**: `liveCitations` ref+state pair mirrors
  `liveCharts` exactly - `streamChat`'s `onCitations` callback replaces
  the whole array each `event: citations` frame (the backend already
  dedupes/numbers it), attached to the finished message as
  `message.citations` once the turn completes, same lifecycle as
  `steps`/`charts` including surviving a page reload
  (`getConversationMessages` returns `citations` per historical message
  too - verified via a real reload of a live conversation, badges and
  numbering came back identical).
- **`SourcesPanel.tsx`**: one card per citation (icon by type, title,
  business-unit tag for `kb`, a real "Open source ↗" link for `web`),
  `highlightIndex` scrolls to and highlights the specific card an inline
  badge referenced. A `kb` card also gets a **"View document"** action -
  resolves the citation's `(unit, source_document)` to a real
  `documents` row via a new `GET /api/v1/documents/lookup` call
  (`lib/documents.ts`'s `findDocumentByObjectKey`, 404 → "Document no
  longer available" shown inline instead of an error) and opens the
  result in the same `DocumentPreviewModal` Manage Documents already
  uses, stacked over the panel - not a raw MinIO URL, since MinIO isn't
  public and this reuses the app's own auth instead of bypassing it.

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
## Markdown rendering

`lib/NovaMarkdown.tsx` renders assistant messages via **react-markdown +
remark-gfm + remark-breaks**, with a `components` map restyling every
element (headings, lists, task-list checkboxes, blockquotes, tables, hr,
links, fenced code blocks with a language label, inline code) to the
`--nova-*` design tokens instead of using react-markdown's unstyled
defaults. This replaced an earlier hand-rolled parser
(`lib/renderInlineMarkdown.tsx`, bold/italic/inline-code/headings/lists
only) once real usage showed the LLM's answers routinely hit markdown the
hand-rolled version didn't cover at all — fenced code blocks (the original
gap), plus tables, blockquotes, strikethrough, task lists, and links once
a broader QA pass was run against it. Re-implementing each of those by
hand would just mean re-discovering CommonMark/GFM edge cases one at a
time; a real parser gets them right in one shot.

- **remark-breaks** turns a single newline into a hard line break (`<br>`)
  instead of CommonMark's default soft-break-as-space — matches how the
  LLM actually formats replies (liberal single newlines, not
  double-newline paragraphs), and matches the old renderer's per-line
  behavior.
- **Known CommonMark/GFM quirk, not a bug**: a GFM table cannot interrupt
  a list item's lazy-continuation paragraph. If a line that reads as an
  ordered-list marker (e.g. `10) Table ...`) is immediately followed by a
  pipe table with no blank line in between, the table stays unparsed
  (swallowed as list-item text) — verified this is spec-correct behavior,
  matching GitHub's own renderer, not something specific to this
  implementation. A blank line before the table (or before any block-level
  element following a line that looks like a list marker) fixes it; this
  is a markdown-authoring issue in the source text, not something to work
  around in `NovaMarkdown.tsx`.
- The `ol` override must forward react-markdown's `start` prop — dropping
  it silently renumbers every ordered list to start at 1, which is easy to
  miss since it only shows up for lists that don't already start at 1.

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
