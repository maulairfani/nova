# ADR-0024: Semantic Layer for the SQL Analytics Tool

**Status:** Accepted

## Decision

Give each business unit's SQL Analytics Tool a **semantic layer**: a
hand-written YAML data dictionary
(`mcp_servers/<unit>/semantic/schema.yaml`) describing, for that unit's
now-dimensional schema (ADR-0023):

- **Per table**: its business purpose in plain language, and per column —
  type, meaning, allowed enum values, units (e.g. "IDR", "percentage of
  0-100"), and foreign-key relationships.
- **A business glossary**: definitions of domain terms an LLM can't infer
  from a column name alone (e.g. `DMA`, `GRP`, `HUT`, `completion_rate`,
  `churn`, `ARPU`).
- **Derived metrics**: named formulas for values that aren't a raw column
  but a well-known calculation over one or more tables (e.g. how GRP
  relates to rating and frequency, how churn rate is computed from
  `subscriptions`).
- **Canonical example questions → SQL**: a handful of representative
  natural-language questions paired with the correct query, covering the
  schema's trickiest joins (e.g. Nielsen ratings by DMA + demographic
  segment).

A shared loader, `mcp_servers/common/semantic_layer.py`, parses a unit's
YAML file into a single prompt-ready text block. Each unit's `db.py`
loads its own file at import time and exposes it as `SCHEMA_DESCRIPTION`
— the exact name `sql_analytics.py` already consumed for its system
prompt — so no call-site changes were needed beyond the load itself.

## Context

TDD §5.2's SQL Analytics Tool works by asking an LLM to translate a
natural-language question into a `SELECT` statement against a schema
description string, then executing it read-only. Through phase 1/2, that
description was three lines of `table(col, col, ...)` signatures — enough
for 3 flat tables with self-explanatory column names, but two problems
grow sharply worse now that each unit's schema is a 8-15 table dimensional
model (ADR-0023):

1. **Column names alone don't carry business meaning.** `rating_pct` could
   plausibly be confused with a 0-1 fraction, a 0-100 score, or something
   else entirely; `grp` (Gross Rating Points) has no meaning at all
   without the Nielsen-domain glossary behind it. An LLM asked to
   translate "how many GRPs did we deliver against Adults 18-49 last
   month" has nothing to ground `grp` in without an explicit definition.
2. **Joins are no longer optional.** Answering almost any real question
   against the new schema requires joining a fact table to 2-3
   dimensions (e.g. `nielsen_ratings` → `airings` → `episodes` →
   `programs`, plus `dma_regions` and `demographic_segments`). A bare
   list of table signatures gives the LLM no signal about *which* joins
   are the intended, meaningful ones versus which are structurally
   possible but nonsensical.

Both failure modes are exactly the "halu"/misinterpretation risk this ADR
exists to close — an LLM that can query but doesn't understand the schema
will produce SQL that runs successfully and returns a plausible-looking
but wrong answer, which is worse than an obvious failure.

## Alternatives Considered

- **Live schema introspection** (`information_schema` at request time,
  optionally with `COMMENT ON COLUMN`): rejected as the sole mechanism —
  it can supply types and (with effort) column comments, but has no place
  to put a glossary, cross-table metric formulas, or example queries;
  Postgres comments are also awkward to keep in sync with a fast-moving
  schema during development (comments live in DDL, reviewed far less
  carefully than application code). Not rejected as *useless* — the
  approach could be layered under the YAML file later if schema drift
  becomes a real risk (Consequences, below).
- **A dbt Semantic Layer / Cube.js-style metrics service**: rejected as
  disproportionate to this project's scale — both stand up a real service
  with its own metric-definition language, API, and deployment footprint,
  aimed at powering multiple downstream BI consumers (dashboards, notebooks,
  a metrics API). Nova has exactly one consumer of this metadata (one
  LLM prompt per business unit's SQL Analytics Tool); a YAML file the tool
  loads directly is the same idea (structured, named metric/dimension
  definitions external to raw SQL) at the complexity level this actually
  warrants — matching this project's general bias toward well-known,
  simple patterns over heavier infrastructure it doesn't yet need.
- **RAG over a documentation corpus** (embed a written data dictionary
  into Qdrant, retrieve relevant chunks per question): rejected — the
  entire schema description for one business unit is small enough (a few
  KB) to include in full on every call; chunked retrieval would risk
  silently dropping a relevant table or the one glossary term a given
  question actually needed, trading a solved problem (prompt-size budget
  is not a real constraint here) for a new one (retrieval recall).
- **Folding the semantic layer into each unit's Alembic migration as SQL
  comments**: rejected — couples business-facing documentation to DDL
  history (every wording tweak would need a migration), and migrations
  are reviewed as schema changes, not documentation changes — the wrong
  place to iterate on prompt wording.

## Rationale

A YAML data dictionary is the simplest mechanism that can hold everything
the SQL Analytics Tool actually needs — structured schema facts *and*
free-form business context (glossary, metric formulas, example
Q&A) — in one place, versioned as a normal file in the same repo and
reviewed like any other change. Keeping it in
`mcp_servers/<unit>/semantic/`, one file per unit, matches the project's
existing "each Business Unit MCP Server owns everything about its own
domain" shape (same reasoning as each unit owning its own Alembic
migrations, ADR-0016) rather than centralizing all units' semantics into
one shared file that would need per-unit conditionals.

The shared loader (`mcp_servers/common/semantic_layer.py`) exists for the
same reason `common/embeddings.py` and `common/qdrant_client.py` do: the
*parsing/rendering* logic is identical across units even though the
*content* isn't — one rendering function, three data files.

## Consequences

- Positive: `sql_analytics.py`'s generated SQL can now cite the right
  join path and the right business meaning for ambiguous terms (GRP, DMA,
  churn, ARPU) instead of guessing from column names alone.
- Positive: the example-questions section doubles as executable
  documentation of the schema's intended query patterns — useful both to
  the LLM and to a human reviewer trying to understand what the schema is
  for.
- Positive: adding a table or column is a two-file change (the Alembic
  migration + the YAML entry), not a hunt through a monolithic hardcoded
  prompt string.
- Negative: the YAML file can drift from the actual schema (a renamed
  column, a new table) since nothing enforces the two stay in sync —
  accepted for this project's scale; a future hardening step would be a
  CI check that every column referenced by a migration also appears in
  that unit's `semantic/schema.yaml` (not built here — no such check
  exists yet).
- Negative: adds `PyYAML` as a new dependency to each Business Unit MCP
  Server.
- Negative: the rendered prompt is now materially longer per SQL
  Analytics Tool call (full glossary + metrics + examples on every
  question, not just table signatures) — accepted; token cost is small
  relative to answer quality on a schema this size, and `gpt-5.4-nano`'s
  context window has ample headroom for it (ADR-0018).
