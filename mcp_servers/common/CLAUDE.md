# mcp_servers/common/ — Shared Code Across Business Unit MCP Servers

Code every Business Unit MCP Server needs identically, per TDD §5.2 ("all
[business unit MCP servers] follow the same internal shape"):

- `auth.py` — the `AuthContext` shape (phase-1: unverified identity
  forwarded via headers, see `backend/CLAUDE.md`). Each unit's own
  `<unit>/auth.py` implements its own check function against this shape —
  this file only defines the shape, never a unit's actual rules.
- `embeddings.py` — OpenRouter embeddings client (ADR-0015). Shared so the
  KB Search Tool's query-time embedding uses the *exact same* model as
  index-time embedding — which now happens in `worker/`'s real ingestion
  pipeline (its own `embeddings.py`, a deliberate small duplicate, see
  `worker/CLAUDE.md`), not a seed script here. Vector spaces must match
  between the two or search breaks.
- `qdrant_client.py` — connection + idempotent collection creation. Each
  unit's own Qdrant collection is created lazily, on first ingestion
  (`worker/tasks.py`'s `ensure_collection`), not by anything in this
  directory.

When phase 2 adds `mcp_servers/plus/` and `mcp_servers/news/`, they import
from here rather than duplicating these three files.
