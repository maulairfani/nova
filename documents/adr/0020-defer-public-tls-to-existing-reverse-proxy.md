# ADR-0020: Defer Public TLS/Reverse Proxy to the VM's Existing Nginx Proxy Manager (amends ADR-0019)

**Status:** Accepted (amends ADR-0019)

## Decision

Caddy stays in the stack, but no longer terminates public TLS or binds
host ports 80/443. It listens on an internal-only port (`8080` on the
host, forwarding to its own port 80) as a plain HTTP router
(`auto_https off`) that still dispatches by domain name to `frontend` or
`backend-api`. The deployment VM's existing **Nginx Proxy Manager**
(NPM) — already running there for the user's other self-hosted
services — owns the public-facing 80/443 ports and TLS certificates for
`DOMAIN_FRONTEND`/`DOMAIN_API`, forwarding to Caddy's internal port.

## Context

ADR-0019 assumed a dedicated VM with nothing else running on it, and had
Caddy bind 80/443 directly for automatic Let's Encrypt TLS. Discovered
during the actual first deploy that this VM already runs NPM for other
services — Caddy's attempt to bind 80/443 would conflict with (or be
shadowed by) NPM, which was already serving its own default page on the
project's domain.

## Alternatives Considered

- **Remove Caddy, configure NPM directly against `frontend`/`backend-api`**:
  rejected by the user — keeping Caddy preserves the domain-based
  internal routing already written and documented (ADR-0019), and avoids
  reconfiguring NPM per-container if Nova's internal service topology
  changes later; NPM only ever needs to know about one upstream port.
- **Run Caddy on the VM's host network / a different host entirely**:
  rejected — unnecessary; a single alternate port mapping is simpler and
  keeps Caddy inside the same Docker Compose stack as everything else.

## Rationale

NPM is the VM's established, already-trusted TLS/reverse-proxy layer for
every other service on it — duplicating that responsibility inside
Nova's own stack would mean two independent ACME clients competing for
the same ports and the same domains, a strictly worse outcome than
deferring to the one that's already there. Caddy's continued presence as
an *internal* router is cheap to keep (a few lines of Caddyfile) and
means Nova's own compose stack is still self-describing about how
`DOMAIN_FRONTEND`/`DOMAIN_API` map to containers, without needing that
knowledge duplicated into NPM's per-container proxy-host configuration.

## Consequences

- Positive: no port/ACME conflict with the VM's existing services.
- Positive: Nova's internal routing (which domain goes to which
  container) stays declared in `infrastructure/Caddyfile`, versioned
  alongside the rest of the stack, rather than living only in NPM's UI
  state (which isn't version-controlled).
- Negative: TLS certificate lifecycle for Nova's domains is now owned by
  NPM, outside this repository's control — if NPM's config is lost or
  misconfigured, Nova's public HTTPS access breaks even though Nova's own
  stack is healthy. Documented in the root README as a manual, one-time
  NPM configuration step (add two Proxy Hosts pointing at the VM's own
  `8080`), not something `release.yml` can perform (NPM's config isn't
  managed by this repository).
- Negative: ADR-0019's "Caddy issues and renews TLS certificates
  automatically" claim is now incorrect for this specific deployment —
  this ADR is the authoritative correction; ADR-0019's Decision text is
  left as originally written (not silently edited) per this project's ADR
  discipline, with only its Status line updated to point here.
