# ADR-0001: Backend Framework — Python + FastAPI

**Status:** Accepted

## Decision

Use **Python with FastAPI** for the Backend API and all MCP servers.

## Context

Section 2 constrains the backend to Go, Python, or Rust. The backend needs
to host a LangGraph agent (ADR-0012), call an LLM API with streaming
responses, and expose/consume MCP tools — all of which have first-class,
actively maintained libraries in Python's AI/LLM ecosystem.

## Alternatives Considered

- **Go** — excellent performance and concurrency, but the LLM/agent
  ecosystem (LangChain, MCP SDKs, embedding libraries) is far less mature
  than Python's; would mean hand-rolling more integration code.
- **Rust** — best raw performance, but slowest development speed for this
  scope, and the AI/agent ecosystem is the least mature of the three
  options. A poor fit for a small team on a constrained timeline.

## Rationale

Python was chosen because the agentic/RAG ecosystem (LangChain/LangGraph,
MCP SDKs, embedding/reranking libraries, Qdrant/pgvector clients) is
built Python-first, minimizing custom integration work. FastAPI adds
native async support (needed for streaming responses and concurrent tool
calls) and automatic OpenAPI documentation, with a lower learning curve
than Go/Rust for a small team (Section 2 constraint).

## Consequences

- Positive: fastest path to a working agent given Python's ecosystem;
  consistent language across Backend API and all MCP servers simplifies
  the small team's cognitive load (Maintainability goal, Section 1.2).
- Negative: raw throughput/latency ceiling is lower than Go/Rust — accepted
  given Nova's expected scale (Section 1.2 capacity estimate) doesn't
  approach that ceiling.
