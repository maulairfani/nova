# ADR-0015: LLM and Embedding Access via OpenRouter

**Status:** Accepted (the LLM model routed through this gateway changed
from Claude to OpenAI `gpt-5.4-nano` per ADR-0018 — the gateway decision
itself is unaffected, since OpenRouter fronts both providers identically)

## Decision

Access both the LLM (ADR-0009, later changed to `gpt-5.4-nano` by
ADR-0018) and the embedding model used by every business unit's KB Search
Tool through **OpenRouter** as a single gateway, rather than calling each
provider's API directly. Embedding model: **OpenAI `text-embedding-3-small`**
(via OpenRouter's `/embeddings` endpoint). LLM model: configurable via
`OPENROUTER_LLM_MODEL`, accessed through OpenRouter's OpenAI-compatible
`/chat/completions` endpoint.

## Context

ADR-0009 chose Anthropic Claude as Nova's LLM provider, but Anthropic has
no first-party embeddings API — the KB Search Tool (TDD Section 5.2) needs
an embedding model to turn queries and document chunks into vectors for
Qdrant, and this gap wasn't covered by any existing ADR. A provider had to
be chosen during Q2 implementation planning.

## Alternatives Considered

- **Direct Anthropic API for chat + a separate embeddings provider (Voyage
  AI or OpenAI directly)**: Voyage AI is Anthropic's recommended embeddings
  partner; OpenAI's embeddings are the most commonly used industry-wide.
  Rejected as the primary path because either choice adds a second vendor
  and a second API key/billing relationship on top of Anthropic — more
  operational surface for the small Platform/Engineering team (Section 2
  constraint) than necessary, for a build that already needs to manage
  Tavily (ADR-0010) as one more external dependency.
- **OpenAI directly for both chat and embeddings** (dropping Claude):
  rejected — ADR-0009's reasoning for choosing Claude as the LLM is
  unrelated to the embeddings gap and still holds; this ADR only needs to
  resolve the embeddings gap, not revisit ADR-0009.

## Rationale

OpenRouter provides a single OpenAI-compatible `/chat/completions` endpoint
that proxies models from any of its supported providers (Anthropic, OpenAI,
etc.), and a separate `/embeddings` endpoint that proxies OpenAI's
embedding models (confirmed against OpenRouter's own docs/API at
implementation time) — both reachable through **one API key**. This keeps
Nova's LLM-provider surface at a single gateway relationship regardless of
which underlying LLM model is chosen, which matters more for a small team
than calling each provider directly would — the model can even change
(ADR-0018) without touching this gateway decision. `text-embedding-3-small` is
OpenAI's cheaper/faster embedding tier, appropriate for a demo-scale build
per the Organizational constraint (Section 2: prefer lower-overhead
tooling where reasonable) — a larger embedding model can be swapped in
later via the same OpenRouter integration point without an architecture
change.

## Consequences

- Positive: a single `OPENROUTER_API_KEY` covers both chat and embeddings,
  simplifying `.env` management across the Backend API and all Business
  Unit MCP Servers (each of which needs the embedding model for its KB
  Search Tool).
- Positive: LLM access still goes through LangChain's model abstraction
  (ADR-0012) — only the underlying HTTP endpoint changes (OpenRouter's
  base URL instead of a provider's own), not the agent code shape.
- Negative: adds a dependency on OpenRouter's uptime/rate limits on top of
  the underlying provider's own — an extra hop versus calling the provider
  directly. Accepted for this build's scale; revisit if OpenRouter
  latency/availability becomes a measured problem (Section 11 follow-up).
- Negative: embedding vectors are now tied to OpenAI's `text-embedding-3-small`
  space — switching embedding models later requires re-embedding every
  business unit's Qdrant collection, not just a config change.
