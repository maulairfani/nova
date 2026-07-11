# ADR-0018: LLM Model Change — OpenAI GPT-5.4 nano (amends ADR-0009)

**Status:** Accepted (amends ADR-0009 — provider changes from Anthropic
Claude to OpenAI, model: `openai/gpt-5.4-nano`, both accessed via the
OpenRouter gateway from ADR-0015)

## Decision

Use **OpenAI's `gpt-5.4-nano`** (via OpenRouter, ADR-0015) as the agent's
LLM, in place of Anthropic Claude (ADR-0009).

## Context

ADR-0009 chose Claude and explicitly named OpenAI as a considered
alternative with "comparable capability and tool-calling support," and
noted the choice was "low-risk to change later if needed" because
LangChain's model abstraction (ADR-0012) decouples the agent's code from
any specific provider. This phase-1 implementation switches to OpenAI's
nano tier, made during Q2 build-out.

## Alternatives Considered

- **Keep Claude (ADR-0009's original choice)**: still a valid option per
  ADR-0009's own rationale; not chosen for this build.
- **A larger/non-nano OpenAI tier** (`gpt-5.4-mini`, `gpt-5.4`, `gpt-5.4-pro`):
  stronger reasoning, but higher cost/latency than justified for a
  demo-scale vertical slice.

## Rationale

Since LangChain's model abstraction (ADR-0012) and OpenRouter (ADR-0015)
already decouple the agent's code from a specific provider/model, changing
the underlying LLM is a configuration change (`OPENROUTER_LLM_MODEL`), not
an architecture change — exactly the flexibility ADR-0009 anticipated.
`gpt-5.4-nano` is OpenAI's smallest/cheapest tier, appropriate for keeping
cost and latency low during this build.

## Consequences

- Positive: no code changes needed elsewhere — the Backend API's LLM
  Client and mcp-tv's SQL Analytics Tool both read the model name from
  settings (`OPENROUTER_LLM_MODEL`), not a hardcoded provider SDK call.
- Negative: nano-tier models trade off reasoning depth for cost/speed —
  worth monitoring against the Groundedness/Accuracy quality goal
  (Section 1.2) and the agent's tool-selection correctness (does it
  reliably choose the right tool per question, Section 6). If evaluation
  shows the nano tier under-performs on multi-tool reasoning (Section 6.3
  cross-business-unit questions especially), upgrading to `gpt-5.4-mini`
  or reverting to Claude is a config-only change, not a rebuild.
- ADR-0009's own Status line is updated to point here, per this project's
  rule of amending via a new ADR rather than silently editing an accepted
  one.
