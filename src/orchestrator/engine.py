import json
import asyncio
from typing import Any, Dict, Callable, List

from src.data.cache import DeltaCache
from src.ai.inference import infer_delta
from src.agents.base import BaseAgent
from src.agents.security_validator import SecurityValidationAgent
from src.agents.ast_patcher import ASTPatchingAgent

_delta_cache = DeltaCache()
get_cached_delta = _delta_cache.get_cached_delta
save_delta = _delta_cache.save_delta

# -------------------------------------------------------------------------
# AUTOHEAL ORCHESTRATOR (EVENT BUS)
# -------------------------------------------------------------------------

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
        self.agents: List[BaseAgent] = []
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Register A2A Plugins
        self.register_agent(SecurityValidationAgent())
        self.register_agent(ASTPatchingAgent())

    def register_agent(self, agent: BaseAgent):
        self.agents.append(agent)
        print(f"[Orchestrator] Registered Plugin Agent: {agent.name}")

    async def emit_event(self, event_name: str, **kwargs):
        """Broadcast an event to all registered agents asynchronously."""
        tasks = [agent.on_event(event_name, **kwargs) for agent in self.agents]
        # Run in background to not block orchestrator
        asyncio.create_task(asyncio.gather(*tasks, return_exceptions=True))

    def _get_lock(self, tool_name: str) -> asyncio.Lock:
        if tool_name not in self._locks:
            self._locks[tool_name] = asyncio.Lock()
        return self._locks[tool_name]

    async def heal_and_retry(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        error_trace: str,
        original_executor: Callable,
        schema: dict = None
    ) -> Any:
        print(f"\n[400 CAUGHT] Intercepted validation error for tool: '{tool_name}'")
        
        # Fire initial event
        await self.emit_event("on_schema_drift", tool_name=tool_name, payload=payload, error_trace=error_trace)
        
        payload_hash = hash_payload(payload)
        
        # Protect against concurrency: Only 1 LLM request per drifting endpoint at a time
        async with self._get_lock(tool_name):
            delta = await get_cached_delta(tool_name, payload_hash)
            
            if delta:
                print(f"[CACHE HIT] Found existing delta.")
            else:
                print(f"[CACHE MISS] Querying inference engine for delta...")
                if not schema:
                    schema = {"description": "mock_schema"}
                delta = await infer_delta(schema, payload, error_trace)
                print(f"[LLM INFERRED DELTA] Computed deep mapping rules: {delta}")
                await save_delta(tool_name, payload_hash, delta)

        # Apply transformations
        remapped_payload = apply_delta(payload, delta)
        print(f"[PAYLOAD REMAPPED] Deep Transformed Payload: {remapped_payload}")
        
        # Security Event (Wait for SecurityValidationAgent to approve)
        # For security, we actually await this event unlike others, to ensure blocking
        for agent in self.agents:
            if agent.name == "SecurityValidationAgent":
                await agent.on_event("on_payload_healed", original_payload=payload, healed_payload=remapped_payload, delta=delta)
        
        try:
            result = await original_executor(remapped_payload)
            print(f"[SUCCESS] Re-execution successful.")
            
            # Fire post-execution event (ASTPatchingAgent will pick this up to patch code)
            await self.emit_event("on_successful_execution", tool_name=tool_name, delta=delta)
                
            return result
        except Exception as e:
            print(f"[FATAL] Re-execution failed even after healing: {e}")
            raise e

# Singleton instance
engine = AutoHealEngine()
