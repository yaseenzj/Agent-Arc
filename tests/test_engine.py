
import pytest

from engine.cache import DeltaCache


@pytest.mark.asyncio
async def test_cache_initialization():
    """Test that the Postgres cache starts up correctly"""
    cache = DeltaCache()
    await cache.connect()
    assert cache._pool is not None

import uuid


@pytest.mark.asyncio
async def test_cache_miss():
    """Test that missing keys return None"""
    cache = DeltaCache()
    unique_hash = str(uuid.uuid4())
    result = await cache.get_cached_delta("fake_tool", unique_hash)
    assert result is None

@pytest.mark.asyncio
async def test_cache_hit():
    """Test that saving and retrieving works perfectly"""
    cache = DeltaCache()
    await cache.save_delta("test_tool", "abc", {"some": "rule"})
    result = await cache.get_cached_delta("test_tool", "abc")
    assert result == {"some": "rule"}
