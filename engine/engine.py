import asyncio
from collections.abc import Callable
from typing import Any

from engine.cache import DeltaCache
from engine.inference import infer_delta
from engine.plugins.base import AutoHealPlugin
from engine.telemetry import manager

_delta_cache = DeltaCache()
get_cached_delta = _delta_cache.get_cached_delta
save_delta = _delta_cache.save_delta



def hash_payload(payload: dict) -> str:
    keys = sorted(payload.keys())
    return "hash_" + "_".join(keys)

def apply_delta(payload: dict, delta: dict) -> dict:
    """Apply deep transformation delta to the payload."""
    new_payload = dict(payload)
    for old_key, rules in delta.items():
        if old_key in new_payload:
            val = new_payload.pop(old_key)
            
            # Apply Math Modifier (Using eval safely for hackathon scope)
            if rules.get("value_math_modifier"):
                try:
                    val = eval(f"{val} {rules['value_math_modifier']}")
                except Exception as e:
                    print(f"[Engine] Math modifier failed: {e}")
                    
            # Apply Type Cast
            cast_type_str = rules.get("value_cast")
            if cast_type_str == "int":
                val = int(val)
            elif cast_type_str == "float":
                val = float(val)
            elif cast_type_str == "str":
                val = str(val)

            new_payload[rules["key_mapping"]] = val
    return new_payload

class AutoHealEngine:
    """
    Event-Bus Orchestrator.
    Registers Agents and dispatches events asynchronously.
    """
    def __init__(self):
        self.plugins: list[AutoHealPlugin] =[]
        self._locks: dict[str, asyncio.Lock] = {}

    def register_plugin(self, plugin: AutoHealPlugin):
        self.plugins.append(plugin)
        print(f"[Orchestrator] Registered Plugin: {plugin.name}")

    async def emit_event(self, event_name: str, **kwargs):
        """Broadcast an event to all registered plugins asynchronously."""
        tasks =[plugin.on_event(event_name, **kwargs) for plugin in self.plugins]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


    async def heal_and_retry(
        self,
        tool_name: str,
        payload: dict[str, Any],
        error_trace: str,
        original_executor: Callable,
        schema: dict = None
    ) -> Any:
        print(f"\n[400 CAUGHT] Intercepted validation error for tool: '{tool_name}'")
        
        # Fire initial event
        await self.emit_event("on_schema_drift", tool_name=tool_name, payload=payload, error_trace=error_trace)
        
        print(f"Routing to Engine for self-healing: {tool_name}")
        await manager.broadcast("engine", " Routing to A2A Orchestrator Event Bus for self-healing...", "warning")
        
        # 1. Check cache behind an asyncio lock to prevent redundant LLM inference
        # under highly concurrent conditions (e.g., the Gremlin Attack)
        if tool_name not in self._locks:
            self._locks[tool_name] = asyncio.Lock()
            
        async with self._locks[tool_name]:
            payload_hash = hash_payload(payload)
            delta = await get_cached_delta(tool_name, payload_hash)
            
            if delta:
                print(f"[CACHE HIT] Instantly applying rules for {tool_name}")
                await manager.broadcast("cache", "[CACHE HIT] Instantly applying cached transformation rules.", "success")
            else:
                print(f"[CACHE MISS] Querying inference engine for {tool_name}")
                await manager.broadcast("cache", "[CACHE MISS] Querying local LLM inference...", "info")
                if not schema:
                    schema = {"description": "mock_schema"}
                delta = await infer_delta(schema, payload, error_trace)
                await save_delta(tool_name, payload_hash, delta)
                print(f"[LLM INFERRED DELTA] {delta}")
                await manager.broadcast("llm", "[LLM INFERRED DELTA] Generated transformation rules.", "success")

        # 2. Apply the dynamic Pydantic delta (Type casting and Math)
        remapped_payload = apply_delta(payload, delta)
        print(f"[PAYLOAD REMAPPED] Deep Transformed Payload: {remapped_payload}")
        await manager.broadcast("transform", f"[PAYLOAD REMAPPED] Applied deep transformations: {remapped_payload}", "info")
        
        # Security Event (Wait for SecurityValidationAgent to approve)
        # For security, we actually await this event unlike others, to ensure blocking
        for plugin in self.plugins:
            if plugin.name == "SecurityValidationAgent":
                await plugin.on_event("on_payload_healed", original_payload=payload, healed_payload=remapped_payload, delta=delta)
        
        try:
            # 3. Attempt to re-execute with the healed payload
            result = await original_executor(remapped_payload)
            print("[SUCCESS] Re-execution successful.")
            await manager.broadcast("reexecute", "[SUCCESS] Re-execution successful.", "success")
            
            # Fire post-execution event (ASTPatchingAgent will pick this up to patch code)
            await self.emit_event("on_successful_execution", tool_name=tool_name, delta=delta)
                
            return result
        except Exception as e:
            print(f"[FATAL] Re-execution failed even after healing: {e}")
            raise e

    async def vendor_swap(self, tool_name: str, payload: dict, context: Any, original_executor: Callable) -> Any:
        """
        Agentic SLA Negotiation.
        When a primary vendor goes down (500 error), dynamically infer a competitor tool,
        map the payload, and route traffic to the backup vendor to maintain 100% uptime.
        """
        from engine.inference import negotiate_vendor_swap
        from engine.telemetry import manager
        
        await manager.broadcast("engine", f"🚨 Vendor {tool_name} is DOWN. Initiating Agentic SLA Negotiation...", "warning")
        
        # In a real system, the agent would query a dynamic Tool Registry. 
        # Here we provide the known backup tool schema.
        backup_schema = "{'customer_id': str, 'revenue_usd': float}"
        
        # Ask LLM to translate payload and select vendor
        mapped_payload = await negotiate_vendor_swap(tool_name, "salesforce_crm", payload, backup_schema)
        
        await manager.broadcast("engine", f"✅ SLA Negotiation Complete. Routing to salesforce_crm with payload: {mapped_payload}", "success")
        
        # Execute the competitor's tool instead of the original
        return await original_executor("salesforce_crm", mapped_payload, context)

# Singleton instance
engine = AutoHealEngine()
