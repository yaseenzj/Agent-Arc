import asyncio

async def run_stress_test_agent(server):
    """
    The Stress Test Agent.
    Bombards the mock server with legacy payloads to prove resilience.
    """
    print("\n👾 [STRESS TEST AGENT] Initiating Concurrency Attack on 'update_crm'...")
    
    # The stress test sends a bunch of outdated payloads simultaneously
    payloads = [
        {"user_id": "991", "amount_usd": 150},
        {"user_id": "992", "amount_usd": 420},
        {"user_id": "993", "amount_usd": 50},
    ]
    
    async def attack(payload):
        print(f"👾 [STRESS TEST] Firing legacy payload: {payload}")
        try:
            await server.call_tool("update_crm", payload)
        except Exception as e:
            pass

    # Fire all attacks concurrently to test asyncio.Lock and Cache sharing
    await asyncio.gather(*(attack(p) for p in payloads))
    print("👾 [STRESS TEST AGENT] Attack sequence complete.")
