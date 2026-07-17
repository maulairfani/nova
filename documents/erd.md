# Entity Relationship Diagrams

Nova follows a **Data Mesh** architecture (ADR-0005): there is no single
consolidated database. Each business unit owns its own PostgreSQL instance,
plus one shared `nova_core` instance for identity, access, and conversation
state (ADR-0021, ADR-0022). Because these databases never share foreign
keys across instances, they are documented as four separate ERDs rather
than one combined diagram.

| Database | Owner | Purpose |
|---|---|---|
| `nova_core` | `backend/` | Identity & access, conversations, document ingestion metadata |
| `mcn_tv` | `mcp_servers/tv/` | MCN TV analytics — Nielsen-style dimensional model (ADR-0023) |
| `mcn_plus` | `mcp_servers/plus/` | MCN+ analytics — streaming + shorts dimensional model (ADR-0023) |
| `mcn_news` | `mcp_servers/news/` | MCN News analytics — dimensional model (ADR-0023) |

Each business unit's analytics schema is a **dimensional (star) model**
(dimension + fact tables), not the flat 3-table schema of earlier phases —
see [ADR-0023](adr/0023-analytics-dimensional-data-model.md) for why, and
each unit's `semantic/schema.yaml` (ADR-0024) for the full business-meaning
writeup behind every table/column shown below.

## 1. `nova_core` — Identity, Access & Conversation State

```mermaid
erDiagram
    USERS {
        uuid id PK
        text email UK
        text password_hash
        text display_name
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    BUSINESS_UNITS {
        text code PK
        text name
    }

    BUSINESS_UNIT_ROLES {
        text code PK
        text name
    }

    USER_BUSINESS_UNITS {
        uuid user_id PK, FK
        text business_unit_code PK, FK
        text role_code FK
    }

    CONVERSATIONS {
        text id PK
        uuid user_id FK
        text title
        timestamptz created_at
        timestamptz updated_at
    }

    DOCUMENTS {
        uuid id PK
        text business_unit_code FK
        text object_key
        text title
        text format
        text status
        integer chunk_count
        text error_message
        timestamptz created_at
        timestamptz ingested_at
    }

    USERS ||--o{ USER_BUSINESS_UNITS : "has membership"
    BUSINESS_UNITS ||--o{ USER_BUSINESS_UNITS : "has member"
    BUSINESS_UNIT_ROLES ||--o{ USER_BUSINESS_UNITS : "grants tier"
    USERS ||--o{ CONVERSATIONS : "owns"
    BUSINESS_UNITS ||--o{ DOCUMENTS : "owns"
```

Notes:
- `USER_BUSINESS_UNITS` is the single membership+role claim table: one row
  per (user, business unit), carrying that unit's permission tier
  (`employee` / `finance` / `admin`).
- `BUSINESS_UNITS` includes a virtual `"group"` entry for MCN Group
  corporate-level claims (e.g. `group_admin`), not a real per-unit MCP
  server.
- `CONVERSATIONS` is sidebar metadata only (title, owner, recency) — actual
  message content and agent state live in LangGraph's own checkpoint
  tables, which are intentionally not modeled here (owned by the
  checkpointer, not Alembic).
- `DOCUMENTS` tracks knowledge-base source files through the ingestion
  pipeline (MinIO → Celery → Qdrant); `(business_unit_code, object_key)` is
  unique.

## 2. `mcn_tv` — MCN TV Analytics (Nielsen-style dimensional model)

```mermaid
erDiagram
    CHANNELS {
        int id PK
        text code UK
        text name
        text coverage_type
    }

    PROGRAMS {
        int id PK
        text title
        text genre
        text format
        text production_type
        date premiere_date
    }

    EPISODES {
        int id PK
        int program_id FK
        int season_number
        int episode_number
        text title
        int duration_minutes
    }

    DMA_REGIONS {
        int id PK
        text code UK
        text name
        int universe_estimate_households
        int universe_estimate_persons
    }

    DEMOGRAPHIC_SEGMENTS {
        int id PK
        text code UK
        text label
        int min_age
        int max_age
        text gender
    }

    ADVERTISERS {
        int id PK
        text name
        text industry_sector
    }

    AD_CAMPAIGNS {
        int id PK
        int advertiser_id FK
        text name
        int target_demographic_segment_id FK
        date start_date
        date end_date
        numeric target_grp
    }

    RATE_CARDS {
        int id PK
        text daypart
        int demographic_segment_id FK
        bigint price_per_grp_idr
        date effective_start_date
        date effective_end_date
    }

    AIRINGS {
        int id PK
        int episode_id FK
        int channel_id FK
        date air_date
        time air_time
        text daypart
        boolean is_rerun
    }

    NIELSEN_RATINGS {
        int id PK
        int airing_id FK
        int dma_id FK
        int demographic_segment_id FK
        text measurement_type
        numeric rating_pct
        numeric share_pct
        numeric grp
        numeric hut_pct
        int sample_size
    }

    AD_SLOTS {
        int id PK
        int airing_id FK
        int advertiser_id FK
        int campaign_id FK
        int slot_position
        int duration_seconds
        int rate_card_id FK
        bigint price_idr
    }

    AD_REVENUE {
        int id PK
        int channel_id FK
        date air_date
        int slot_count
        numeric grp_delivered
        bigint revenue_idr
    }

    PROGRAMS ||--o{ EPISODES : "has"
    EPISODES ||--o{ AIRINGS : "aired as"
    CHANNELS ||--o{ AIRINGS : "broadcasts"
    AIRINGS ||--o{ NIELSEN_RATINGS : "measured by"
    DMA_REGIONS ||--o{ NIELSEN_RATINGS : "measured in"
    DEMOGRAPHIC_SEGMENTS ||--o{ NIELSEN_RATINGS : "measured for"
    AIRINGS ||--o{ AD_SLOTS : "carries"
    ADVERTISERS ||--o{ AD_SLOTS : "buys"
    AD_CAMPAIGNS ||--o{ AD_SLOTS : "fulfilled by"
    RATE_CARDS ||--o{ AD_SLOTS : "prices"
    ADVERTISERS ||--o{ AD_CAMPAIGNS : "runs"
    DEMOGRAPHIC_SEGMENTS ||--o{ AD_CAMPAIGNS : "targets"
    DEMOGRAPHIC_SEGMENTS ||--o{ RATE_CARDS : "priced for"
    CHANNELS ||--o{ AD_REVENUE : "earns"
```

Follows the real-world Nielsen audience-measurement model: every rating is
scoped to a DMA (market) and a demographic segment, and ad pricing
(`rate_cards`/`ad_slots`) is negotiated in GRP, not raw viewer counts. See
`mcp_servers/tv/semantic/schema.yaml`'s glossary for DMA/Rating/Share/
GRP/HUT definitions. `daypart` is constrained to
`prime_time | day_time | late_night` throughout.

## 3. `mcn_plus` — MCN+ Analytics (Streaming + Shorts)

```mermaid
erDiagram
    REGIONS {
        int id PK
        text name UK
    }

    DEVICES {
        int id PK
        text device_type
        text platform
    }

    LICENSORS {
        int id PK
        text name
        text country
    }

    SUBSCRIPTION_PLANS {
        int id PK
        text code UK
        text name
        bigint price_idr
        int max_concurrent_streams
    }

    COIN_PACKAGES {
        int id PK
        text code UK
        int coin_amount
        bigint price_idr
    }

    TITLES {
        int id PK
        text title
        text product
        text content_type
        text genre
        text maturity_rating
        int licensor_id FK
        date release_date
    }

    SEASONS {
        int id PK
        int title_id FK
        int season_number
    }

    EPISODES {
        int id PK
        int title_id FK
        int season_id FK
        int episode_number
        int duration_seconds
        date release_date
    }

    SUBSCRIBERS {
        int id PK
        text external_subscriber_code UK
        date signup_date
        int region_id FK
        int primary_device_id FK
    }

    ENGAGEMENT {
        int id PK
        int title_id FK
        int episode_id FK
        date date
        text product
        int device_id FK
        int region_id FK
        int watch_minutes
        numeric completion_rate
        int viewers
    }

    SUBSCRIPTIONS {
        int id PK
        int subscriber_id FK
        int plan_id FK
        date start_date
        date end_date
        text status
        text churn_reason
    }

    SUBSCRIPTION_TRANSACTIONS {
        int id PK
        int subscriber_id FK
        int plan_id FK
        date billing_date
        bigint amount_idr
        text status
    }

    COIN_TRANSACTIONS {
        int id PK
        int subscriber_id FK
        int coin_package_id FK
        int title_id FK
        date transaction_date
        int coins_spent
        bigint amount_idr
    }

    CONTENT_LICENSING_COSTS {
        int id PK
        int title_id FK
        int licensor_id FK
        bigint license_fee_idr
        date license_start_date
        date license_end_date
    }

    REVENUE {
        int id PK
        date date
        text product
        bigint subscription_revenue_idr
        bigint coin_revenue_idr
        int active_subscribers
    }

    TITLES ||--o{ SEASONS : "has"
    TITLES ||--o{ EPISODES : "has"
    SEASONS ||--o{ EPISODES : "groups"
    LICENSORS ||--o{ TITLES : "licenses"
    LICENSORS ||--o{ CONTENT_LICENSING_COSTS : "charges"
    TITLES ||--o{ CONTENT_LICENSING_COSTS : "costs"
    TITLES ||--o{ ENGAGEMENT : "watched as"
    EPISODES ||--o{ ENGAGEMENT : "watched as"
    DEVICES ||--o{ ENGAGEMENT : "measured on"
    REGIONS ||--o{ ENGAGEMENT : "measured in"
    REGIONS ||--o{ SUBSCRIBERS : "located in"
    DEVICES ||--o{ SUBSCRIBERS : "primary device"
    SUBSCRIBERS ||--o{ SUBSCRIPTIONS : "has"
    SUBSCRIPTION_PLANS ||--o{ SUBSCRIPTIONS : "tier"
    SUBSCRIBERS ||--o{ SUBSCRIPTION_TRANSACTIONS : "billed"
    SUBSCRIPTION_PLANS ||--o{ SUBSCRIPTION_TRANSACTIONS : "billed for"
    SUBSCRIBERS ||--o{ COIN_TRANSACTIONS : "purchases"
    COIN_PACKAGES ||--o{ COIN_TRANSACTIONS : "purchased as"
    TITLES ||--o{ COIN_TRANSACTIONS : "unlocks"
```

Per ADR-0014, MCN+ and MCN+ Shorts are one business unit with two
products, not two separate schemas — `product` (`streaming | shorts`) is a
column on `titles`/`engagement`/`revenue`, shared structures used by both.
Monetization is deliberately split into two fact tables —
`subscription_transactions` (streaming, plan-based) and
`coin_transactions` (shorts, one-off coin unlocks) — since they're
genuinely different business models. `REVENUE` is a daily rollup, not
per-title, so it has no FK to `TITLES`.

## 4. `mcn_news` — MCN News Analytics

```mermaid
erDiagram
    DESKS {
        int id PK
        text code UK
        text name
    }

    AUTHORS {
        int id PK
        text name
        int desk_id FK
    }

    PLATFORMS {
        int id PK
        text code UK
        text name
    }

    AD_SLOT_TYPES {
        int id PK
        text code UK
        text name
    }

    ARTICLES {
        int id PK
        text headline
        int desk_id FK
        int author_id FK
        text content_type
        date publish_date
        boolean is_breaking
    }

    ARTICLE_ENGAGEMENT {
        int id PK
        int article_id FK
        int platform_id FK
        date date
        int page_views
        int unique_visitors
        int avg_time_on_page_seconds
        int social_shares
    }

    AD_REVENUE {
        int id PK
        date date
        int ad_slot_type_id FK
        int platform_id FK
        bigint impressions
        bigint revenue_idr
    }

    CORRECTIONS {
        int id PK
        int article_id FK
        date correction_date
        text reason
        text severity
    }

    DESKS ||--o{ AUTHORS : "employs"
    DESKS ||--o{ ARTICLES : "publishes"
    AUTHORS ||--o{ ARTICLES : "writes"
    ARTICLES ||--o{ ARTICLE_ENGAGEMENT : "measured as"
    PLATFORMS ||--o{ ARTICLE_ENGAGEMENT : "measured on"
    AD_SLOT_TYPES ||--o{ AD_REVENUE : "sold as"
    PLATFORMS ||--o{ AD_REVENUE : "earned on"
    ARTICLES ||--o{ CORRECTIONS : "corrected by"
```

`AD_REVENUE` here is not per-article (ad inventory is sold platform-wide,
by slot type and platform, not per-story), so it has no FK to `ARTICLES` —
unlike `mcn_tv`'s airing-linked ad slots. `CORRECTIONS` reflects the
correction/retraction SOP already in the knowledge base
(`severity`: `minor | major | retraction`).

## Cross-database relationships (logical, not enforced)

Each business unit's analytics database is referenced logically by
`nova_core.business_units.code` (`tv` / `plus` / `news`) and
`nova_core.documents.business_unit_code` — there is no physical foreign
key across database instances, by design (ADR-0005: each unit's data is
queried live via that unit's own MCP server, never joined at the database
level).
