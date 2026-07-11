# mcp_servers/common/ — Shared Code Across Business Unit MCP Servers

Code every Business Unit MCP Server needs identically, per TDD §5.2 ("all
[business unit MCP servers] follow the same internal shape"):

- `auth.py` — the `AuthContext` shape (phase-1: unverified identity
  forwarded via headers, see `backend/CLAUDE.md`). Each unit's own
  `<unit>/auth.py` implements its own check function against this shape —
  this file only defines the shape, never a unit's actual rules.
- `embeddings.py` — OpenRouter embeddings client (ADR-0015). Shared because
  the KB Search Tool (query-time) and `seed_qdrant.py` (index-time) must
  use the *exact same* embedding model, or their vector spaces won't match.
- `qdrant_client.py` — connection + idempotent collection creation. The
  seed script owns collection creation (single source of truth), not the
  MCP server at query time.

When phase 2 adds `mcp_servers/plus/` and `mcp_servers/news/`, they import
from here rather than duplicating these three files.
