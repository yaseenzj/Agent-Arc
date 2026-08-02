import asyncio

from engine.broadcaster import manager


async def run_stress_test_agent(server):
    """
    The Stress Test Agent.
    Bombards the mock server with legacy payloads to prove resilience.
    """
    print("\n[STRESS TEST AGENT] Initiating Concurrency Attack on 'update_crm'...")
    

    payloads = [
        {"user_id": "991", "amount_usd": 150},
        {"user_id": "992", "amount_usd": 420},
        {"user_id": "993", "amount_usd": 50},
        {"user_id": "888", "amount_usd": 500} 
    ]
    
    async def attack(payload):
        print(f"[STRESS TEST] Firing legacy payload: {payload}")
        await manager.broadcast("gremlin", f"[STRESS TEST] Firing legacy payload: {payload}", "error")
        try:
            await server.call_tool("update_crm", payload)
        except Exception:
            pass

    # Fire all attacks concurrently to test asyncio.Lock and Cache sharing
    await asyncio.gather(*(attack(p) for p in payloads))
    print("[STRESS TEST AGENT] Attack sequence complete.")
