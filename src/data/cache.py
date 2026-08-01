import json
import fakeredis.aioredis as redis

class DeltaCache:
    def __init__(self):
        # We use FakeRedis so you don't have to install heavy software on Windows!
        self._redis = None

    async def connect(self):
        """Connect to the fast memory box."""
        if not self._redis:
            self._redis = redis.FakeRedis(decode_responses=True)
            print("[Redis] Connected to Fast Memory Box")

    async def get_cached_delta(self, tool_name: str, payload_hash: str):
        """Look in memory to see if we already know the fix."""
        if not self._redis:
            await self.connect()

        key = f"autoheal:{tool_name}:{payload_hash}"
        data = await self._redis.get(key)

        if data:
            print(f"[CACHE HIT] Found instant 0ms fix for: {tool_name}")
            return json.loads(data)
        
        print(f"[CACHE MISS] Not in memory yet for: {tool_name}")
        return None

    async def save_delta(self, tool_name: str, payload_hash: str, fix_dictionary: dict):
        """Save a new fix into memory for next time."""
        if not self._redis:
            await self.connect()

        key = f"autoheal:{tool_name}:{payload_hash}"
        await self._redis.set(key, json.dumps(fix_dictionary))
        print(f"[CACHE SAVED] Saved fix to memory for: {tool_name}")
