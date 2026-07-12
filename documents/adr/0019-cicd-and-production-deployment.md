# ADR-0019: CI/CD and Production Deployment — GitHub Actions, GHCR, Caddy on a Single VM

**Status:** Accepted — the TLS/reverse-proxy portion of this Decision is
amended by [ADR-0020](0020-defer-public-tls-to-existing-reverse-proxy.md):
the deployment VM already runs Nginx Proxy Manager for other services,
so Caddy no longer terminates public TLS directly.

## Decision

Use **GitHub Actions** for CI/CD: a `ci.yml` workflow (unit tests, one
integration test, image builds — no push) runs on every push/PR to `main`;
a `release.yml` workflow builds and pushes all 6 images to **GHCR**
(`ghcr.io`) tagged with a manually-pushed git tag (`v*.*.*`) plus `latest`,
then deploys to a single Ubuntu VM over SSH. The VM runs
`docker-compose.prod.yml` (pulling pre-built images instead of building
locally) behind **Caddy** as a reverse proxy, which issues and renews TLS
certificates automatically for the project's domain.

## Context

Q2's bonus checklist asks for GitHub Actions CI/CD (unit + integration
tests, build, version release, push to GHCR) — nothing existed yet (no
`.github/`, no tests, no versioning scheme). The user also has a real VM
and domain and wants actual continuous **deployment** there, not just
image publishing — genuinely new ground for this project (TDD §7
previously marked the reverse proxy as explicitly out of scope, and §11
flagged the single-Docker-host topology as an accepted demo-scale
simplification with no real external access story).

## Alternatives Considered

- **Watchtower** (auto-pulls and restarts containers on new image
  versions) for CD instead of an explicit SSH deploy step: rejected —
  no control over running Alembic migrations *before* the new containers
  start serving traffic; a schema change landing after the app code that
  depends on it is a real correctness risk this project's migration
  discipline (ADR-0016) is meant to avoid.
- **Nginx + certbot** for the reverse proxy: rejected for this scale —
  correct and more broadly documented, but requires a certbot renewal
  cron/systemd timer and more config to reach the same TLS outcome that
  Caddy provides by default from a ~6-line Caddyfile. Appropriate trade
  for a single small VM, not a claim that Nginx is the wrong choice in
  general.
- **Docker Hub** as the registry: rejected — GHCR keeps source and
  registry on one platform (no second account/credential to manage), is
  free for the project's images, and matches the bonus requirement's exact
  wording ("push to GHCR").
- **Automated semantic-release tooling** for versioning: rejected as
  unnecessary — this is the project's first versioning scheme with no
  existing history to reconcile; plain manually-pushed git tags
  (`v0.1.0`, `v0.2.0`, ...) triggering the release workflow are simpler
  and give the user explicit control over when a release actually happens.

## Rationale

GitHub Actions needs no new account/platform beyond what's already hosting
the source. Splitting CI (every push/PR — fast, no push, matrix-built
across all 6 images) from Release (tag-triggered — build, push, deploy) is
a standard pattern that keeps ordinary development iteration fast while
making releases an explicit, deliberate action. Deploying via SSH (not
Watchtower) lets the deploy script run each business unit's
`alembic upgrade head` — idempotent per ADR-0016 — before restarting
containers, preserving the migration-before-serve ordering guarantee.
Caddy's automatic TLS matches this project's "prefer well-known, simple
patterns" convention (`CLAUDE.md`) at the actual scale being deployed (one
VM, two domains).

Dummy seed data (`seed_postgres.py`/`seed_qdrant.py`, per ADR-0016 and
each unit's `CLAUDE.md`) is deliberately **not** run automatically on every
deploy — it's already idempotent, but re-running it costs real embedding
API calls for no benefit once a unit has been seeded once; seeding stays a
manual first-deploy step, same as local `docker compose up`.

## Consequences

- Positive: every push/PR gets fast feedback (unit tests + build checks)
  without needing real cloud credentials; only a tag push touches the
  real VM and consumes registry/embedding costs.
- Positive: the two real bugs found earlier this session (cross-unit tool
  scoping crash, tool name collisions) now have permanent regression tests
  (`backend/tests/test_mcp_client.py`), not just a one-off manual
  verification that could silently regress.
- Positive: TLS and CD close out part of TDD §11's "single Docker host
  deployment" risk entry — the topology is still a single VM (unchanged
  trade-off), but it's no longer undescribed/unreachable from outside the
  host.
- Negative: GitHub Actions secrets (`VM_HOST`, `VM_USER`, `VM_SSH_KEY`,
  `VM_DEPLOY_PATH`, `OPENROUTER_API_KEY`, `TAVILY_API_KEY`) become a new
  piece of operational surface the user must configure and keep current;
  documented in the root README rather than assumed.
- Negative: `docker-compose.prod.yml`'s `.env` (real production secrets,
  domain names, `GHCR_OWNER`) must be created directly on the VM — it is
  deliberately never generated or transmitted by CI, so it's a manual
  one-time setup step per VM, same treatment as the local dev `.env`.
- Negative: still a single point of failure (one VM) — orthogonal
  scaling/redundancy remains explicitly out of scope, unchanged from TDD
  §11's existing risk entry.
