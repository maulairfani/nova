# ADR-0023: Analytics Data Model — Dimensional (Star) Schema per Business Unit

**Status:** Accepted

## Decision

Replace each business unit's flat 3-table analytics schema with a proper
**dimensional model** (dimension tables + fact tables, star-schema style),
scoped per unit:

- **`mcn_tv`**: dimensions `channels`, `programs`, `dma_regions`,
  `demographic_segments`, `advertisers`, `ad_campaigns`, `rate_cards`;
  facts `episodes`, `airings`, `nielsen_ratings`, `ad_slots`, `ad_revenue`.
  Ratings follow the real-world **Nielsen** audience-measurement model
  (rating %, share %, GRP, HUT, DMA, demographic segment, overnight vs.
  live+7 — see Rationale) rather than a single flat `rating` number.
- **`mcn_plus`**: dimensions `titles`, `seasons`, `episodes`,
  `subscription_plans`, `coin_packages`, `subscribers`, `devices`,
  `regions`, `licensors`; facts `engagement`, `subscriptions`,
  `subscription_transactions`, `coin_transactions`,
  `content_licensing_costs`, `revenue`.
- **`mcn_news`**: dimensions `desks`, `authors`, `platforms`,
  `ad_slot_types`; facts `articles`, `article_engagement`, `ad_revenue`,
  `corrections`.

Each unit's schema still lives in that unit's own hand-written Alembic
migrations (ADR-0016 unchanged) — this ADR only changes *what* is
migrated, not *how*.

## Context

The original phase-1/2 schema (`0001_initial_schema.py` per unit) was
intentionally minimal — 3 flat tables per unit (e.g. `mcn_tv`'s
`programs`/`viewership_ratings`/`ad_revenue`) — sized to prove the SQL
Analytics Tool's plumbing (read-only role, text-to-SQL, forbidden-keyword
guard), not to represent a real media company's data estate. The test
brief this project answers explicitly frames the PostgreSQL side as
**"big data ... the Single Source of Truth for creating Data Analytics
and derived Decision Making"** — a flat schema undersells that framing and
gives the SQL Analytics Tool nothing to reason about beyond trivial
single-table lookups.

A second, more concrete problem with the flat schema: `viewership_ratings`
had one `rating` column with no notion of *which* audience or *which*
market it was measured against. A media company can't actually act on
"the rating was 8.4" — real ad sales, scheduling, and programming
decisions all key off audience *segment* and *market*, which the flat
schema had no way to represent.

## Alternatives Considered

- **Keep the flat schema, just add more columns**: rejected — columns
  like `region` on `viewership_ratings` were already trying to be a
  dimension (a fixed, reusable set of regions) squeezed into a fact row as
  free text, with no referential integrity and no room to attach
  region-level attributes (e.g. Nielsen's per-DMA household universe
  estimate) without repeating them on every fact row.
- **A single denormalized "wide" analytics table per unit** (one row per
  measurement with every dimension attribute inlined): rejected — this is
  the OLAP-cube-export shape, not a source-of-truth OLTP shape; it would
  make the SQL Analytics Tool's generated `SELECT`s trivial but defeats
  the purpose of demonstrating a dimensional model a real analytics team
  would actually query, and re-introduces the same lack-of-referential-
  integrity problem as the flat schema.
- **A fully normalized 3NF schema with no fact/dimension distinction**
  (e.g. separate `ratings_measurements`, `ratings_methodology`, etc. with
  no designed grain): rejected — over-engineered for this project's scope
  and harder for the SQL Analytics Tool (and a human) to reason about than
  the well-known star-schema shape, which has an explicit, learnable
  vocabulary ("fact" = an event/measurement, "dimension" = the context it
  happened in).

## Rationale

**Star schema** (Kimball-style fact/dimension modeling) is the standard,
well-known framework for analytics data — the same "prefer well-known,
simple patterns over clever ones" principle this project already applies
to architecture (arc42/C4/ADR) and applies here to data modeling. It gives
each unit's SQL Analytics Tool (and semantic layer, ADR-0024) an explicit
grain per fact table and a bounded, reusable set of dimension values,
which is what makes text-to-SQL grounding tractable in the first place —
an LLM generating `SELECT`s against `nielsen_ratings` can be told exactly
which `dma_id`/`demographic_segment_id` values exist, instead of guessing
at free-text `region` strings.

**Nielsen's measurement model** was chosen for `mcn_tv` specifically
because it's the real, well-documented industry standard for TV audience
measurement (and the literal "currency" broadcasters and advertisers
negotiate ad rates against) — modeling `rating_pct`/`share_pct`/`grp`/
`hut_pct` per DMA per demographic segment per measurement type
(`overnight`/`live_plus_7`) is a concrete, externally-verifiable framework
to justify during review, rather than an invented metric. `ad_slots` and
`rate_cards` connect ratings directly to revenue (GRP-based ad pricing),
mirroring how real broadcast ad sales work.

`mcn_plus` and `mcn_news` follow the same dimensional discipline scaled to
their own domains: `mcn_plus` separates subscription (recurring, plan-based)
from coin (one-off, shorts-specific) monetization per ADR-0014's two-product
unit, and adds a subscriber/device/region dimension set for churn and
engagement analysis; `mcn_news` adds a `desks`/`authors` dimension set and
a `corrections` fact table reflecting the correction/retraction SOP
already in the knowledge base.

## Consequences

- Positive: each unit's analytics database now looks like a real,
  queryable data mart, not a toy — 12 tables (`mcn_tv`), 15 tables
  (`mcn_plus`), 8 tables (`mcn_news`), all connected by explicit foreign
  keys instead of free-text dimension columns.
- Positive: gives the semantic layer (ADR-0024) real relationships and
  business vocabulary to describe, instead of three flat tables with
  little to say about.
- Positive: `mcn_tv`'s Nielsen-shaped ratings and `mcn_plus`'s
  subscription/coin split are concrete, defensible domain modeling
  decisions, not arbitrary column choices.
- Negative: each unit's seed data generation is meaningfully more complex
  (dimension rows must exist before facts reference them) — addressed by
  moving seed data generation to one consolidated location (ADR-0025)
  rather than three independently-drifting per-unit scripts.
- Negative: `0001_initial_schema.py` per unit is superseded by a new
  `0002_dimensional_schema.py` migration (drops the old 3 tables, creates
  the new set) rather than hand-editing `0001` — consistent with Alembic's
  own discipline (never rewrite a migration once it could have run
  against a real database) and this project's "new ADR/migration, never
  silently edit an accepted one" convention.
- Negative: the SQL Analytics Tool's generated queries now need more
  joins for most non-trivial questions (e.g. "TV ratings for Adults
  18-49 in Jabodetabek" requires joining `nielsen_ratings` →
  `dma_regions` + `demographic_segments`) — mitigated by the semantic
  layer (ADR-0024) documenting these relationships explicitly rather than
  leaving the LLM to infer them from column names alone.
