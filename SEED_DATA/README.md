# SEED_DATA/ — Consolidated Dummy Analytics Data

Generates dummy data for all 3 business-unit analytics databases
(`mcn_tv`, `mcn_plus`, `mcn_news`) against their new dimensional schema
(ADR-0023). See [ADR-0025](../documents/adr/0025-consolidated-seed-data-location.md)
for why this replaced the old per-unit `mcp_servers/<unit>/seed/` scripts.

## Structure

```
db_utils.py     Shared mechanics: idempotency check, bulk insert with ordered RETURNING ids
tv_data.py       mcn_tv generator — channels, programs, episodes, DMAs, demographic
                segments, advertisers/campaigns, rate cards, then ~6 months of
                airings, Nielsen ratings, ad slots, and daily ad revenue
plus_data.py     mcn_plus generator — titles/seasons/episodes (streaming + shorts),
                subscription plans, coin packages, subscribers, devices, regions,
                licensors, then subscriptions/billing, coin transactions, content
                licensing costs, engagement, and daily revenue
news_data.py     mcn_news generator — desks, authors, platforms, ad slot types,
                then ~150 articles with per-platform engagement, daily ad revenue,
                and a subset of corrections/retractions
seed_all.py      Orchestrator — connects to all 3 databases and runs each generator
```

Each `<unit>_data.py`'s `seed(engine)` is idempotent — a no-op if that
unit's primary table already has rows, same guarantee the old per-unit
scripts made, so re-running `seed_all.py` against an already-seeded stack
does nothing.

## Running it

Requires each unit's schema to already exist (`alembic upgrade head` run
against `postgres-tv`/`postgres-plus`/`postgres-news` first — see root
`README.md`'s one-off setup steps):

```bash
docker compose run --rm seed-data python seed_all.py
```

This is a separate Compose service, not attached to any business unit
MCP server's own image — it only needs `sqlalchemy` + `psycopg2` (no
FastMCP/Qdrant/OpenRouter dependencies), and connects to all 3 Postgres
instances using the same admin credentials each unit's own Alembic setup
already uses.

## Regenerating with different volume/content

Each generator's dimension lists (`PROGRAMS`, `TITLES`, `DESKS`, etc.) and
`SEED_DAYS` constant are plain Python at the top of that unit's
`<unit>_data.py` — edit and re-run against a wiped volume
(`docker compose down -v` then redo the migrate/seed steps) to regenerate
with different volume or content. There's no template/config layer beyond
that; keeping it as plain Python matches this project's existing seed
script style (see the retired scripts' git history) rather than
introducing a data-generation DSL for a one-off dummy dataset.
