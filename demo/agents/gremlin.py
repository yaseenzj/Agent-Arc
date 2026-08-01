import asyncio
import random
from demo.mock_targets.crm_tool import mock_crm_tool

async def run_gremlin_agent(server):
    """
    The Chaos Engineering Attacker.
    Bombards the mock server with legacy payloads to prove resilience.
    """
    print("\n👾 [GREMLIN AGENT] Initiating Chaos Attack on 'update_crm'...")
    
    # The gremlin sends a bunch of outdated payloads simultaneously
    payloads = [
        {"user_id": "991", "amount_usd": 150},
        {"user_id": "992", "amount_usd": 420},
        {"user_id": "993", "amount_usd": 50},
    ]
    
    async def attack(payload):
        print(f"👾 [GREMLIN] Firing legacy payload: {payload}")
        try:
            await server.call_tool("update_crm", payload)
        except Exception as e:
            pass

    # Fire all attacks concurrently to test asyncio.Lock and Cache sharing
    await asyncio.gather(*(attack(p) for p in payloads))
    print("👾 [GREMLIN AGENT] Attack sequence complete.")
