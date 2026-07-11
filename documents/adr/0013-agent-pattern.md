# ADR-0013: Agent Pattern — ReAct via `langchain.agents.create_agent`

**Status:** Accepted

## Decision

Implement Nova's agent as a **ReAct** agent (reason → act → observe,
looping until an answer is ready), using `langchain.agents.create_agent`
— **not** the deprecated `langgraph.prebuilt.create_react_agent`.

## Context

Given LangGraph as the orchestration framework (ADR-0012), a specific
agent pattern still needs to be chosen. LangGraph 0.x's
`create_react_agent` was initially considered but confirmed deprecated as
of LangGraph v1, in favor of `langchain.agents.create_agent` (equivalent
ReAct-style behavior, plus a middleware system); the old function remains
supported only until LangGraph 0.x's maintenance window ends (December
2026).

## Alternatives Considered

- **DeepAgents-style planner/sub-agent architecture** — designed for
  long-horizon tasks (deep research, complex multi-step work) using
  planning tools, sub-agent delegation, and virtual-filesystem context
  offloading. Rejected: Nova's questions are shallow (Section 1.1) —
  typically one or two tool calls per question — so the extra planning
  overhead would hurt the Performance Efficiency goal (Section 1.2) for
  work Nova doesn't actually need to do.
- **Fully custom agent loop** — rejected per the same reasoning as
  ADR-0012: reinvents infrastructure a well-known pattern already solves,
  against `nova/CLAUDE.md`'s "prefer well-known, simple patterns" working
  convention.

## Rationale

ReAct's reason/act/observe loop matches the actual shape of Nova's task —
pick a tool (or a few, per Section 6.3's cross-business-unit case), observe
the result, decide whether more tool calls are needed, then answer. It's
simple enough to reason about and debug (Maintainability goal), and keeps
latency down by not incurring planning overhead a more elaborate
architecture would add. `create_agent` (not the deprecated
`create_react_agent`) is used specifically to avoid building on an API
already scheduled for removal, and its middleware system leaves room to
later hook in per-tool authorization checks (Section 8) without changing
the core agent logic.

## Consequences

- Positive: simple, debuggable, latency-appropriate for Nova's actual task
  shape; avoids building on a deprecated API.
- Negative: if Nova's scope later grows to genuinely long-horizon tasks
  (e.g. multi-step report generation), this pattern would need to be
  revisited — not a concern for the current functional scope (Section
  1.1).
