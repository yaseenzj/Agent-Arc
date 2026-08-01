import pytest
import asyncio
from src.data.cache import DeltaCache

@pytest.mark.asyncio
async def test_cache_miss():
    cache = DeltaCache()
    res = await cache.get_cached_delta("test_tool", "hash1")
    assert res is None

@pytest.mark.asyncio
async def test_cache_hit():
    cache = DeltaCache()
    await cache.save_delta("test_tool", "hash1", {"old": "new"})
    res = await cache.get_cached_delta("test_tool", "hash1")
    assert res == {"old": "new"}
