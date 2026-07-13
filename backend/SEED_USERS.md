# Seeded dev users (ADR-0021)

Dummy accounts created by `seed_users.py` — no signup flow exists, so
these are the only accounts that can log in until real user management is
built. Password is the same dummy value for every account (dev only, not
a real secret).

Password for all accounts: **`Nova123!`**

| Email | Display name | Business unit | Role |
|---|---|---|---|
| andi.wijaya@mcngroup.example | Andi Wijaya | tv | employee |
| budi.santoso@mcngroup.example | Budi Santoso | plus | finance |
| citra.lestari@mcngroup.example | Citra Lestari | news | employee |
| dewi.anggraini@mcngroup.example | Dewi Anggraini | group | employee |
| eko.prasetyo@mcngroup.example | Eko Prasetyo | group | admin |
| fajar.nugroho@mcngroup.example | Fajar Nugroho | tv | employee |
| fajar.nugroho@mcngroup.example | Fajar Nugroho | plus | employee |

Notes:
- `group` is the virtual MCN Group corporate-level unit, not a real
  business unit MCP server (ADR-0021) — `dewi` and `eko` have no
  business-unit-specific data access.
- `dewi` (`group`/`employee`): Shared MCP Server (web search) only.
- `eko` (`group`/`admin`): cross-unit data access to all business units,
  without needing per-unit membership.
- `budi` (`plus`/`finance`): tier is stored, but not yet enforced by
  `mcp_servers/plus`'s SQL Analytics Tool — see ADR-0021's Consequences.
- `fajar` has two membership rows (`tv` and `plus`), both `employee`.

Source of truth is `seed_users.py` — update that first if this list ever
needs to change, then update this file to match.
