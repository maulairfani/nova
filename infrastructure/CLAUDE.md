# infrastructure/

Cross-cutting deployment configuration that doesn't belong to a single
service:

- `docker-compose.prod.yml` — the production compose file. Same 12
  services as the root [`docker-compose.yaml`](../docker-compose.yaml),
  but the 6 built-from-source services are replaced with pre-built GHCR
  images, and a `caddy` reverse-proxy service is added. See
  [ADR-0019](../documents/adr/0019-cicd-and-production-deployment.md).
- `Caddyfile` — reverse proxy config: two site blocks (frontend domain,
  API domain), automatic Let's Encrypt TLS, no manual cert management.
  `.github/workflows/release.yml` copies both files here to the
  deployment VM (flattened, not preserving this `infrastructure/` prefix)
  on every tagged release.

Still intentionally not here:

- Docker orchestration for **local development** lives in the root
  [`docker-compose.yaml`](../docker-compose.yaml), not here.
- Per-business-unit database schema migrations live with the service that
  owns that database — e.g. [`mcp_servers/tv/alembic/`](../mcp_servers/tv/alembic/)
  — not here. See [ADR-0016](../documents/adr/0016-database-migrations-alembic.md)
  for why migrations are colocated with each MCP server rather than
  centralized in this directory.

## Verifying changes here

Neither file needs a live deploy to validate:

```bash
# From the nova/ root — relative paths inside docker-compose.prod.yml
# (e.g. ./Caddyfile) resolve relative to this file's own directory.
docker compose -f infrastructure/docker-compose.prod.yml config

docker run --rm -v "$PWD/infrastructure/Caddyfile:/etc/caddy/Caddyfile:ro" \
  -e DOMAIN_FRONTEND=example.com -e DOMAIN_API=api.example.com \
  caddy:2-alpine caddy validate --config /etc/caddy/Caddyfile
```
