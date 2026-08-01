import json
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

class DeltaCache:
    def __init__(self):
        self._pool = None
        self._db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/autoheal")

    async def connect(self):
        """Connect to PostgreSQL and ensure the table exists."""
        if not self._pool:
            try:
                self._pool = await asyncpg.create_pool(self._db_url)
                async with self._pool.acquire() as conn:
                    # Auto-create the table if it doesn't exist
                    await conn.execute('''
                        CREATE TABLE IF NOT EXISTS schema_deltas (
                            id SERIAL PRIMARY KEY,
                            tool_name VARCHAR(255) NOT NULL,
                            payload_hash VARCHAR(255) NOT NULL,
                            fix_dictionary JSONB NOT NULL,
                            UNIQUE(tool_name, payload_hash)
                        )
                    ''')
                print("[Postgres] Connected to Enterprise Database (schema_deltas verified)")
            except Exception as e:
                print(f"[Postgres ERROR] Could not connect to database: {e}")
                raise

    async def get_cached_delta(self, tool_name: str, payload_hash: str):
        """Look in PostgreSQL to see if we already know the fix."""
        if not self._pool:
            await self.connect()

        query = "SELECT fix_dictionary FROM schema_deltas WHERE tool_name = $1 AND payload_hash = $2"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(query, tool_name, payload_hash)
            
            if row:
                print(f"[CACHE HIT] Found instant Postgres fix for: {tool_name}")
                # asyncpg returns JSONB as a string by default unless a codec is set, we just parse it.
                return json.loads(row['fix_dictionary'])
            
            print(f"[CACHE MISS] Not in database yet for: {tool_name}")
            return None

    async def save_delta(self, tool_name: str, payload_hash: str, fix_dictionary: dict):
        """Save a new fix into PostgreSQL for permanent storage."""
        if not self._pool:
            await self.connect()

        query = '''
            INSERT INTO schema_deltas (tool_name, payload_hash, fix_dictionary)
            VALUES ($1, $2, $3)
            ON CONFLICT (tool_name, payload_hash) DO UPDATE 
            SET fix_dictionary = EXCLUDED.fix_dictionary
        '''
        
        async with self._pool.acquire() as conn:
            await conn.execute(query, tool_name, payload_hash, json.dumps(fix_dictionary))
            
        print(f"[CACHE SAVED] Saved fix to Postgres for: {tool_name}")
