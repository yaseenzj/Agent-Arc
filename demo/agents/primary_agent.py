from engine.broadcaster import manager


async def run_primary_agent(server):
    """
    Simulates the Primary Reasoning Asset Management Agent triggering a workflow.
    """
    drifted_payload = {"user_id": 123, "total_cents": 5.0}
    
    print("\n[PRIMARY AGENT] Calling tool 'update_crm' with payload:")
    print(f"                {drifted_payload}\n")
    await manager.broadcast("primary", f"[PRIMARY AGENT] Calling tool 'update_crm' with payload {drifted_payload}", "info")
    
    try:
        # The agent makes the call expecting it to work...
        result = await server.call_tool("update_crm", drifted_payload)
        
        # If the proxy works, the agent receives success seamlessly!
        print("\n[PRIMARY AGENT] Received successful result seamlessly:")
        print(f"                {result}\n")
        

        
    except Exception as e:
        print(f"\n[PRIMARY AGENT] CRASHED with error: {e}\n")
