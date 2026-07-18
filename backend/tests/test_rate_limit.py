"""Unit tests for the per-user chat rate limit (ADR-0027):
app/core/rate_limit.py's Redis fixed-window counter and
app/api/v1/deps.py's check_rate_limit dependency built on it."""
import asyncio
import uuid

import pytest
from fastapi import HTTPException

from app.agent.cache import get_redis
from app.api.v1.deps import check_rate_limit
from app.core.rate_limit import (
    CHAT_RATE_LIMIT,
    CHAT_RATE_LIMIT_WINDOW_SECONDS,
    _key,
    get_usage_status,
    increment_and_check,
)


async def _cleanup(user_id: uuid.UUID) -> None:
    await get_redis().delete(_key(user_id))


async def test_increment_and_check_counts_up_from_zero():
    user_id = uuid.uuid4()
    try:
        first = await increment_and_check(user_id)
        second = await increment_and_check(user_id)

        assert first.used == 1
        assert second.used == 2
        assert first.limit == CHAT_RATE_LIMIT
        assert second.remaining == CHAT_RATE_LIMIT - 2
    finally:
        await _cleanup(user_id)


async def test_ttl_armed_on_first_call_not_refreshed_by_second():
    """EXPIRE ... NX must only arm the window once - a plain EXPIRE on every
    call would turn this into a sliding window instead of the fixed one the
    limit is supposed to be."""
    user_id = uuid.uuid4()
    try:
        first = await increment_and_check(user_id)
        assert first.reset_seconds == CHAT_RATE_LIMIT_WINDOW_SECONDS

        redis = get_redis()
        await redis.expire(_key(user_id), 100)  # simulate time having passed
        second = await increment_and_check(user_id)

        assert second.reset_seconds <= 100
    finally:
        await _cleanup(user_id)


async def test_check_rate_limit_blocks_after_limit_reached():
    user_id = uuid.uuid4()
    try:
        for _ in range(CHAT_RATE_LIMIT):
            status = await increment_and_check(user_id)
        assert status.used == CHAT_RATE_LIMIT
        assert status.used <= status.limit  # request #50 itself is still allowed

        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(user_id=user_id)

        assert exc_info.value.status_code == 429
        assert exc_info.value.headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in exc_info.value.headers
    finally:
        await _cleanup(user_id)


async def test_get_usage_status_never_consumes_quota():
    user_id = uuid.uuid4()
    try:
        await increment_and_check(user_id)

        first = await get_usage_status(user_id)
        second = await get_usage_status(user_id)

        assert first.used == 1
        assert second.used == 1
    finally:
        await _cleanup(user_id)


async def test_get_usage_status_with_no_prior_requests():
    user_id = uuid.uuid4()
    status = await get_usage_status(user_id)

    assert status.used == 0
    assert status.remaining == CHAT_RATE_LIMIT
    assert status.reset_seconds == 0


async def test_increment_and_check_is_race_free_under_concurrency():
    """Confirms INCR's atomicity actually holds under real concurrent
    access, not just sequential calls."""
    user_id = uuid.uuid4()
    try:
        results = await asyncio.gather(*[increment_and_check(user_id) for _ in range(60)])
        used_values = sorted(r.used for r in results)

        assert used_values == list(range(1, 61))
    finally:
        await _cleanup(user_id)
