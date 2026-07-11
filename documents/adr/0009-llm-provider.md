# ADR-0009: LLM Provider — Anthropic Claude

**Status:** Accepted (model changed to OpenAI `gpt-5.4-nano` by
[ADR-0018](0018-llm-model-change-gpt-5-4-nano.md) — this ADR's
tool-calling/long-context reasoning and its explicit anticipation that
provider swaps stay cheap thanks to LangChain's abstraction both still
hold, only the specific model changed)

## Decision

Use **Anthropic Claude** as the primary LLM provider for the agent's
reasoning and answer generation.

## Context

The agent (ADR-0012, ADR-0013) needs an LLM capable of reliable tool-
calling across multiple MCP servers, multi-step reasoning, and long-context
handling (retrieved KB chunks + conversation history). Section 2's
"prefer open-source/self-hosted" constraint doesn't practically extend to
the core LLM itself — self-hosting a frontier-quality model is well beyond
what a small Platform/Engineering team (Section 2) can operate, and Section
3 already models the LLM as a genuinely external system.

## Alternatives Considered

- **OpenAI (GPT models)** — comparable capability and tool-calling support;
  a reasonable alternative with similar trade-offs.
- **Self-hosted open-source models (e.g. Llama)** — would satisfy the
  self-hosted preference literally, but at meaningfully lower reasoning/
  tool-calling reliability for this use case, plus the GPU infrastructure
  and ops burden directly contradicts the small-team constraint.

## Rationale

Claude was chosen for strong, consistent tool-calling behavior (important
given Nova routes across multiple MCP servers per question, Section 6.3)
and long-context handling. Since LangChain/LangGraph (ADR-0012) abstracts
the LLM provider behind a common interface, this choice is low-risk to
change later if needed — swapping providers doesn't require re-architecting
the agent.

## Consequences

- Positive: reliable multi-tool orchestration; provider swap remains cheap
  thanks to LangChain's abstraction.
- Negative: introduces a paid, external dependency and associated cost —
  accepted as unavoidable for this class of capability at Nova's small-team
  scale.
