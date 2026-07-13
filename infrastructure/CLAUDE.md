# infrastructure/

Cross-cutting deployment configuration that doesn't belong to a single
service:

- `docker-compose.prod.yml` — the production compose file. Same 12
  services as the root [`docker-compose.yaml`](../docker-compose.yaml),
  but the 6 built-from-source services are replaced with pre-built GHCR
  images, and a `caddy` service is added (published on host port `8081`
  only, not 80/443). See [ADR-0019](../documents/adr/0019-cicd-and-production-deployment.md).
- `Caddyfile` — **internal** HTTP router only (`auto_https off`), two site
  blocks (frontend domain, API domain) forwarding to the right container.
  Public TLS/80/443 is owned by whatever reverse proxy already runs on
  the deployment VM (e.g. Nginx Proxy Manager) — discovered on the first
  real deploy that the VM wasn't dedicated to Nova alone, see
  [ADR-0020](../documents/adr/0020-defer-public-tls-to-existing-reverse-proxy.md).
  That external proxy needs a Proxy Host per domain pointing at the VM's
  own `8081` (chosen because `8080` was already bound by another service
  on the VM — pick whatever's actually free on your VM) — a manual,
  one-time step outside this repo (see root README).
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

Look for `"automatic HTTPS is completely disabled for server"` in the
validate output — confirms `auto_https off` is actually taking effect
(Caddy defaults to auto-HTTPS for any domain-name site address, which
would be wrong here since this Caddy never receives direct public
traffic).
