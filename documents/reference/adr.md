# ADR — Architecture Decision Record (Reference)

Reference notes on Architecture Decision Records, used for
[Section 9](../technical-design-document.md) of the Technical Design
Document. Format originated by Michael Nygard (2011); this project uses a
lightly adapted version of his template.

## Big Idea

The knowledge that goes stale fastest on a project isn't the code — it's
the *reasoning* behind the code. Six months later, nobody remembers why
Postgres was chosen over MongoDB, and the question keeps getting re-litigated.
ADRs exist to make that reasoning a durable, timestamped artifact instead of
something that lives only in someone's memory or a Slack thread. The core
idea is: **decisions are cheap to write down at the moment they're made, and
expensive to reconstruct later** — so capture the context and trade-offs
once, immediately, and never delete that record even when the decision is
later reversed (write a new ADR that supersedes it instead).

## What it is

An ADR is a short document that captures **one significant architecture
decision**: what was decided, the context that led to it, what alternatives
were considered, and the consequences of the choice. It exists so that
future readers (including the original author, later) understand *why* a
decision was made, not just what the current state is.

- Short: typically one to two pages, often much less.
- One decision per record — don't bundle unrelated decisions.
- Immutable once accepted: if a decision changes later, write a **new** ADR
  that supersedes the old one, rather than editing history away.

## Nygard's original format

- **Title** — short noun phrase, e.g. "Use PostgreSQL as primary datastore"
- **Status** — Proposed / Accepted / Deprecated / Superseded (by ADR-00X)
- **Context** — the forces at play: technical, business, team constraints
  that make this decision necessary. Written objectively, not as
  justification.
- **Decision** — the actual choice, stated in active voice ("We will use
  ...").
- **Consequences** — the resulting effects, positive AND negative. A
  decision always has trade-offs; list them honestly.

## Adapted format used for this project

Per [CLAUDE.md](../../CLAUDE.md)'s design principle, this project's ADRs use
a variant with an explicit **Alternatives Considered** section (common in
many modern ADR templates), since the test explicitly requires showing
alternatives and rationale:

- **Title**
- **Status**
- **Decision** — the choice made, stated plainly
- **Context** — why this decision needed to be made, what constraints apply
- **Alternatives Considered** — other options evaluated, and why each was
  not chosen
- **Rationale** — why the chosen option best satisfies the context /
  quality goals (tie back to arc42 Section 1.2 Quality Goals where relevant)
- **Consequences** *(optional but encouraged)* — trade-offs accepted by
  making this choice

## Storage convention

- One ADR per file, numbered sequentially: `adr-001-xxx.md`,
  `adr-002-xxx.md`, etc.
- Kept together under `nova/documents/adr/` (or embedded as arc42 Section 9
  entries — decide when we get there).

## Notes for this project

- ADRs fill in arc42 Section 9 (Architecture Decisions) — see
  [arc42.md](arc42.md).
- Expected ADRs for this project (one each): backend language/framework,
  frontend framework, database, cache, async worker/queue, MCP server,
  LLM provider, web search integration. Not every minor choice needs an
  ADR — only decisions that are significant, hard to reverse, or
  non-obvious.

Sources:
- [ADR Templates | Architectural Decision Records](https://adr.github.io/adr-templates/)
- [Documenting Architecture Decisions - Cognitect.com](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [bliki: Architecture Decision Record - Martin Fowler](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)
