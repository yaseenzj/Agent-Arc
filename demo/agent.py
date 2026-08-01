import asyncio
from src.telemetry import manager

async def run_primary_agent(server):
    """
    Simulates the Primary Reasoning Asset Management Agent triggering a workflow.
    It uses the outdated schema ("total_cents") which will cause a validation error.
    """
    drifted_payload = {"user_id": "123", "total_cents": 500}
    
    print(f"\n[PRIMARY AGENT] Calling tool 'update_crm' with payload:")
    print(f"                {drifted_payload}\n")
    await manager.broadcast("primary", f"👤 [PRIMARY AGENT] Calling tool 'update_crm' with payload {drifted_payload}", "info")
    
    try:
        # The agent makes the call expecting it to work...
        result = await server.call_tool("update_crm", drifted_payload)
        
        # If the proxy works, the agent receives success seamlessly!
        print(f"\n[PRIMARY AGENT] Received successful result seamlessly:")
        print(f"                {result}\n")
        
        print("\n" + "-"*60)
        print("[PRIMARY AGENT] Making the exact same call again later...")
        print("-"*60 + "\n")
        
        result2 = await server.call_tool("update_crm", drifted_payload)
        
        print(f"\n[PRIMARY AGENT] Received successful result seamlessly AGAIN:")
        print(f"                {result2}\n")
        
    except Exception as e:
        print(f"\n[PRIMARY AGENT] CRASHED with error: {e}\n")
