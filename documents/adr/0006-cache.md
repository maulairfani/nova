# ADR-0006: Cache — Redis

**Status:** Accepted

## Decision

Use **Redis** as the shared cache, and also as the async worker's message
broker (Section 5, "shared infrastructure").

## Context

The Performance Efficiency quality goal (Section 1.2) calls for caching
repeated/common queries. The async worker (ADR-0007) also needs a job
queue/broker.

## Alternatives Considered

- **Memcached** — simpler, pure cache, but has no built-in support for
  acting as a task queue broker, which would mean adding a second
  technology (e.g. RabbitMQ) just for the async worker.
- **In-process caching (no separate service)** — would not survive across
  the multiple Backend API/MCP server processes, and provides nothing for
  the async worker's job queue.

## Rationale

Redis was chosen because it serves two needs at once (cache + broker) with
one technology, directly serving the Maintainability goal's "avoid
introducing a second database technology" principle already applied
elsewhere in this document (ADR-0003, ADR-0004). It's simple to operate,
widely understood, and has first-class client libraries in Python.

## Consequences

- Positive: one shared, well-understood technology covers both caching and
  job queuing.
- Negative: Redis is in-memory — cached data and undelivered jobs are lost
  on a crash without persistence configuration; acceptable here since
  cached data is disposable (re-computed on a cache miss) and ingestion
  jobs can be safely re-triggered.
