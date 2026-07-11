# ADR-0008: MCP Server Framework — FastMCP

**Status:** Accepted

## Decision

Use **FastMCP** to implement every MCP server (the 4 Business Unit MCP
servers and the Shared MCP Server, Section 5).

## Context

Section 4/8 requires each MCP server to enforce its own authorization
rules, and Section 9 (ADR-0001) already commits the backend to Python —
the MCP server implementation should fit that ecosystem.

## Alternatives Considered

- **The official low-level MCP Python SDK** — full control, but requires
  hand-building the boilerplate (tool registration, transport handling,
  auth hooks) that FastMCP already provides.
- **Building a custom tool-calling layer outside the MCP spec** — rejected
  early; MCP was specifically chosen (Section 4) as the uniform
  tool-calling interface, so bypassing the protocol would undo that
  benefit.

## Rationale

FastMCP is the most established higher-level framework for building MCP
servers in Python, reducing boilerplate versus the low-level SDK. Its
authorization model is **callable-based**: each tool can be registered
with a check function that receives an `AuthContext` (the caller's token
and claims) and returns True/False, with multiple checks combining via
AND logic. This maps directly onto Nova's federated model (Section 8) —
each Business Unit MCP Server's Authorization Middleware (Section 5.2) is
one such check function, evaluating that unit's own role/claim rules
independently of the other three. This keeps 4 near-identical MCP servers
consistent and maintainable, since they all follow the same framework's
conventions and extension point.

## Consequences

- Positive: less boilerplate across 5 MCP server instances (4 business
  unit + 1 shared); a single, consistent authorization extension pattern
  (callable auth checks) that fits the federated governance model without
  a custom framework.
- Negative: each business unit's actual check function (its specific
  role/claim rules) still needs to be implemented and tested per unit —
  tracked as follow-up work in the TDD's Section 11, not a design gap.
