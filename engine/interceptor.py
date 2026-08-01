import traceback
from collections.abc import Callable
from typing import Any

from engine.engine import engine
from engine.broadcaster import manager


class AutoHealMiddleware:
    """
    FastMCP Middleware interceptor.
    Traps JSON-RPC validation exceptions (400 Bad Request) before they crash the agent,
    and passes them to the orchestration engine for self-healing.
    """
    
    # Circuit Breaker state
    _failure_count = 0
    _circuit_open = False
    _circuit_open_time = 0
    
    async def on_call_tool(
        self,
        tool_name: str,
        payload: dict[str, Any],
        context: Any,
        call_next: Callable
    ) -> Any:
        import time
        if AutoHealMiddleware._circuit_open:
            if time.time() - AutoHealMiddleware._circuit_open_time > 15:
                print("[CIRCUIT BREAKER] 🔄 Half-open: Attempting traffic again...")
                AutoHealMiddleware._circuit_open = False
                AutoHealMiddleware._failure_count = 0
            else:
                await manager.broadcast("interceptor", "[CIRCUIT BREAKER] 🛑 Circuit OPEN. Traffic rejected to protect backend.", "error")
                raise Exception("Circuit Breaker OPEN. Backend is protected from cascading failure.")

        try:
            # 1. Attempt normal execution
            result = await call_next(tool_name, payload, context)
            AutoHealMiddleware._failure_count = 0 # reset on success
            return result
            
        except Exception as e:
            # 2. Trap the exception
            error_msg = str(e).lower()
            
            # Check if this is a validation / 400 Bad Request error (Schema Drift)
            if "validation" in error_msg or "400" in error_msg or "missing" in error_msg or "deprecated" in error_msg:
                AutoHealMiddleware._failure_count += 1
                if AutoHealMiddleware._failure_count >= 10:
                    AutoHealMiddleware._circuit_open = True
                    AutoHealMiddleware._circuit_open_time = time.time()
                    print("\n[CIRCUIT BREAKER] 🛑 TRIPPED! Too many consecutive failures.")
                    await manager.broadcast("interceptor", "[CIRCUIT BREAKER] 🛑 TRIPPED! Backend protected.", "error")

                error_trace = traceback.format_exc()
                
                print(f"\n[400 CAUGHT] Intercepted validation error for tool: '{tool_name}'")
                await manager.broadcast("interceptor", f"[400 CAUGHT] Intercepted validation error for tool: '{tool_name}'", "error")
                
                
                # Define a closure to re-execute call_next with a modified payload natively
                async def re_executor(new_payload: dict):
                    return await call_next(tool_name, new_payload, context)
                
                # 3. Suppress the crash and delegate to the Self-Healing Engine
                return await engine.heal_and_retry(
                    tool_name=tool_name,
                    payload=payload,
                    error_trace=error_trace,
                    original_executor=re_executor
                )
            elif "500" in error_msg or "offline" in error_msg:
                print(f"\n[500 CAUGHT] Intercepted Provider Outage for tool: '{tool_name}'")
                await manager.broadcast("interceptor", f"[500 CAUGHT] Legacy Provider '{tool_name}' is OFFLINE.", "error")
                
                # Delegate to Agentic SLA Negotiation (Vendor Swap)
                return await engine.vendor_swap(
                    tool_name=tool_name,
                    payload=payload,
                    context=context,
                    original_executor=call_next
                )
            else:
                # If it's a completely unrelated error, let it crash normally.
                raise e
