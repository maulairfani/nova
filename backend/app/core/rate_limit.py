"""Per-user chat rate limit (ADR-0027) — Redis fixed-window counter, reusing
the same client cache.py already maintains (INCR/EXPIRE/TTL/GET don't need
decoded string values, so decode_responses=False is fine here too)."""
import uuid

from app.agent.cache import get_redis
from app.schemas.usage import UsageOut

CHAT_RATE_LIMIT = 30
CHAT_RATE_LIMIT_WINDOW_SECONDS = 5 * 60 * 60  # 18000, i.e. 5 hours


def _key(user_id: uuid.UUID) -> str:
    return f"ratelimit:chat:{user_id}"


async def increment_and_check(user_id: uuid.UUID) -> UsageOut:
    """Called once per chat request, always - even one that ends up
    rejected - since incrementing first is what keeps this race-free under
    concurrent sends. `used` is the raw post-increment count, not clamped to
    `limit`: deps.check_rate_limit needs to tell request #50 (allowed) apart
    from #51 (blocked) via `used > limit`."""
    redis = get_redis()
    key = _key(user_id)
    used = await redis.incr(key)
    # NX: only arms a TTL once per window. A plain (non-NX) EXPIRE here would
    # push the reset back on every message, turning this into a sliding
    # window instead of the fixed one the limit is supposed to be. Calling
    # it unconditionally (not just when used == 1) also self-heals a key
    # that somehow ended up without a TTL - the next request re-arms it.
    await redis.expire(key, CHAT_RATE_LIMIT_WINDOW_SECONDS, nx=True)
    ttl = await redis.ttl(key)
    reset_seconds = ttl if ttl >= 0 else CHAT_RATE_LIMIT_WINDOW_SECONDS
    return UsageOut(
        used=used,
        limit=CHAT_RATE_LIMIT,
        remaining=max(0, CHAT_RATE_LIMIT - used),
        reset_seconds=reset_seconds,
    )


async def get_usage_status(user_id: uuid.UUID) -> UsageOut:
    """Read-only - GET + TTL only, never INCR - so checking usage (the
    Settings endpoint) never itself consumes quota."""
    redis = get_redis()
    key = _key(user_id)
    raw = await redis.get(key)
    used = int(raw) if raw is not None else 0
    ttl = await redis.ttl(key)
    reset_seconds = max(ttl, 0)  # -2 (no key) or -1 (no TTL) -> no active window
    return UsageOut(
        used=min(used, CHAT_RATE_LIMIT),
        limit=CHAT_RATE_LIMIT,
        remaining=max(0, CHAT_RATE_LIMIT - used),
        reset_seconds=reset_seconds,
    )
