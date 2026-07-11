# ADR-0011: Object Storage — MinIO

**Status:** Accepted

## Decision

Use **MinIO** to simulate each business unit's Document Repository
(Section 3.1), as a single shared deployment with one bucket per business
unit (Section 4).

## Context

Section 3.1 established that documents (SOPs, internal documentation) can
be various formats (not just Markdown), and Section 3.2 required an
object-storage-based Document Repository rather than local files, to
reflect how a real MCN Group business unit would actually store documents.

## Alternatives Considered

- **Local filesystem / mounted volume with Markdown files** — the simplest
  option, considered first, but rejected because it doesn't represent
  multi-format documents realistically and doesn't map to how object
  storage-based document repositories actually work in production.
- **Cloud object storage (S3, GCS)** — realistic for a production
  deployment, but adds a cloud-provider dependency and cost that
  contradicts the "prefer self-hosted" constraint (Section 2) for a demo
  build.

## Rationale

MinIO is open-source, S3-API-compatible (so the integration code would
transfer directly to real S3/GCS in a production deployment), and
self-hostable via Docker, fitting Section 2's constraints while still
representing the object-storage architecture pattern accurately.

## Consequences

- Positive: realistic representation of document storage; S3-compatible
  API means minimal rework if migrated to a real cloud provider later.
- Negative: one more container to run — mitigated by being a single shared
  deployment (bucket-partitioned per business unit) rather than one MinIO
  instance per unit, per Section 4's shared-infrastructure reasoning.
