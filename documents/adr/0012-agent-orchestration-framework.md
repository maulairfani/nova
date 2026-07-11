# ADR-0012: Agent Orchestration Framework — LangChain/LangGraph

**Status:** Accepted

## Decision

Use **LangChain/LangGraph** (`langchain.agents.create_agent`, running on
LangGraph) as the agent orchestration framework in the Backend API.

## Context

Section 4 commits to an "agentic tool-calling" architectural pattern: an
LLM that reasons about which MCP tool(s) to call per question. This needs
to be implemented with some orchestration framework rather than a fully
custom loop.

## Alternatives Considered

- **Raw LLM provider SDK with a hand-rolled tool-calling loop** — full
  control, but reimplements state management, conversation persistence,
  and retry/streaming handling that LangGraph already provides —
  contradicts the "prefer well-known, simple patterns" working convention
  (`nova/CLAUDE.md`) by adding unnecessary custom infrastructure.
- **LlamaIndex** — strong for RAG-focused pipelines specifically, but less
  suited than LangGraph for the general multi-tool, multi-MCP-server agent
  orchestration Nova needs (Section 5).
- **A different orchestration layer built directly around the MCP SDK**
  — would still need to reimplement agent state/looping logic that
  LangGraph provides out of the box.

## Rationale

LangChain/LangGraph was chosen primarily for the author's existing
expertise (faster, more reliable implementation within the project
timeline) and its observability tooling (LangSmith, Section 8), which
gives visibility into the agent's reasoning and tool-selection decisions —
directly useful for debugging the Groundedness/Accuracy quality goal
(Section 1.2). It also ships a Postgres-backed checkpointer, letting Nova
reuse its existing PostgreSQL investment (`nova_kb`) for conversation state
instead of adding a separate session store (Maintainability goal).

## Consequences

- Positive: fast implementation given existing expertise; strong
  observability; conversation state persistence solved without new
  infrastructure.
- Negative: ties the Backend API to LangChain's abstractions and their
  upgrade/deprecation cycle — already encountered once during this
  project (`create_react_agent` deprecated in favor of `create_agent`,
  see ADR-0013) — accepted as a normal cost of depending on a fast-moving
  ecosystem.
