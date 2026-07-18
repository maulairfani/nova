#!/usr/bin/env bash
# One-off setup/seed orchestrator — runs the manual steps from README.md's
# "One-off setup" section in order, against an already-running stack
# (docker compose up -d --build). Safe to re-run: every step it calls is
# already idempotent on its own (migrations, seed_all.py, seed_users.py,
# bootstrap_buckets.py, seed_documents.py all no-op or skip on already-seeded
# state) — this script only saves typing/ordering, it adds no new logic.
#
# Usage: ./seed.sh
set -euo pipefail

cd "$(dirname "$0")"

# On Git Bash (Windows), MSYS auto-rewrites leading-slash arguments as if
# they were POSIX paths, which mangles the container-side half of `-v
# host:/container:ro` below (e.g. `/kb:ro` silently becomes a Windows path).
# Disabling that rewrite is a no-op on Linux/macOS, so this is safe everywhere.
export MSYS_NO_PATHCONV=1

echo "==> Business unit analytics schemas (alembic upgrade head)"
docker compose run --rm mcp-tv alembic upgrade head
docker compose run --rm mcp-plus alembic upgrade head
docker compose run --rm mcp-news alembic upgrade head

echo "==> Seeding dummy analytics data for all 3 units (ADR-0025)"
docker compose run --rm seed-data python seed_all.py

echo "==> Creating LangGraph's conversation-checkpoint tables"
docker compose run --rm backend-api python setup_checkpointer.py

echo "==> Migrating nova_core's identity/access schema + seeding dummy users"
docker compose run --rm backend-api alembic upgrade head
docker compose run --rm backend-api python seed_users.py

echo "==> Creating MinIO buckets + webhook subscriptions (ADR-0022)"
docker compose run --rm worker python bootstrap_buckets.py

echo "==> Seeding dummy KB documents through the real ingestion pipeline"
docker compose run --rm -v "$PWD/documents/kb:/kb:ro" worker python seed_documents.py

echo "==> Done. See backend/SEED_USERS.md for seeded accounts."
