import traceback
from typing import Callable, Any, Dict
from src.orchestrator.engine import engine

class AutoHealMiddleware:
    """
    FastMCP Middleware interceptor.
    Traps JSON-RPC validation exceptions (400 Bad Request) before they crash the agent,
    and passes them to the orchestration engine for self-healing.
    """
    
    async def on_call_tool(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        context: Any,
        call_next: Callable
    ) -> Any:
        try:
            # 1. Attempt normal execution
            return await call_next(tool_name, payload, context)
            
        except Exception as e:
            # 2. Trap the exception
            error_msg = str(e).lower()
            
            # Check if this is a validation / 400 Bad Request error (Schema Drift)
            if "validation" in error_msg or "400" in error_msg or "missing" in error_msg or "deprecated" in error_msg:
                error_trace = traceback.format_exc()
                
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
            else:
                # If it's a completely unrelated error (e.g., 500 Internal Server Error), 
                # let it crash normally.
                raise e
