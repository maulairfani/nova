# ADR-0010: Web Search Provider — Tavily

**Status:** Accepted

## Decision

Use **Tavily** as the Web Search Service (Section 3, Section 5's Shared
MCP Server).

## Context

Web search is an explicit functional requirement (Section 1.1, user story
3), used as a fallback when internal sources (KB, business unit data)
don't have an answer.

## Alternatives Considered

- **Bing Search API / Google Custom Search** — general-purpose search APIs,
  return raw search results (snippets/links) that would need extra
  post-processing before an LLM can use them cleanly.
- **SerpAPI** — similar general-purpose scraping-based approach, comparable
  trade-offs to Bing/Google.

## Rationale

Tavily was chosen because it's built specifically for LLM agent use cases —
it returns cleaned, summarized results designed to be consumed directly by
an LLM, reducing the amount of post-processing the Shared MCP Server's Web
Search Tool needs to do, and improving the quality of what the agent
grounds its answer in (Groundedness/Accuracy goal, Section 1.2).

## Consequences

- Positive: less integration work; results are already LLM-consumption-
  ready.
- Negative: another external paid dependency; less general-purpose than
  Bing/Google if Nova's web search needs expand beyond simple Q&A lookups
  later.
