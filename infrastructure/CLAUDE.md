# infrastructure/

Cross-cutting deployment configuration that doesn't belong to a single
service. For phase 1, this is intentionally sparse:

- Docker orchestration lives in the root [`docker-compose.yaml`](../docker-compose.yaml),
  not here.
- Per-business-unit database schema migrations live with the service that
  owns that database — e.g. [`mcp_servers/tv/alembic/`](../mcp_servers/tv/alembic/)
  — not here. See [ADR-0016](../documents/adr/0016-database-migrations-alembic.md)
  for why migrations are colocated with each MCP server rather than
  centralized in this directory.

What would land here in a later phase: shared reverse-proxy/load-balancer
config, TLS termination, or any provisioning config that spans multiple
services at once (none of that exists yet — TDD §7.1 explicitly scopes this
build to a single Docker host via docker-compose, not a multi-host
deployment).
