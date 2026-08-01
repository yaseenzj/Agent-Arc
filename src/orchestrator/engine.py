import json
import asyncio
from typing import Any, Dict, Callable, List

from src.data.cache import DeltaCache
from src.ai.inference import infer_delta
from src.agents.base import BaseAgent
from src.agents.security_validator import SecurityValidationAgent
from src.agents.ast_patcher import ASTPatchingAgent
from src.telemetry import manager

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
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

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
        
        print(f"Routing to Engine for self-healing: {tool_name}")
        await manager.broadcast("engine", f"⚙️ Routing to A2A Orchestrator Event Bus for self-healing...", "warning")
        
        # 1. Check cache behind an asyncio lock to prevent redundant LLM inference
        # under highly concurrent conditions (e.g., the Gremlin Attack)
        if tool_name not in self._locks:
            self._locks[tool_name] = asyncio.Lock()
            
        async with self._locks[tool_name]:
            payload_hash = hash_payload(payload)
            delta = await get_cached_delta(tool_name, payload_hash)
            
            if delta:
                print(f"[CACHE HIT] Instantly applying rules for {tool_name}")
                await manager.broadcast("cache", f"⚡ [CACHE HIT] Instantly applying cached transformation rules.", "success")
            else:
                print(f"[CACHE MISS] Querying inference engine for {tool_name}")
                await manager.broadcast("cache", f"🔍 [CACHE MISS] Querying local LLM inference...", "info")
                if not schema:
                    schema = {"description": "mock_schema"}
                delta = await infer_delta(schema, payload, error_trace)
                await save_delta(tool_name, payload_hash, delta)
                print(f"[LLM INFERRED DELTA] {delta}")
                await manager.broadcast("llm", f"🧠 [LLM INFERRED DELTA] Generated transformation rules.", "success")

        # 2. Apply the dynamic Pydantic delta (Type casting and Math)
        remapped_payload = apply_delta(payload, delta)
        print(f"[PAYLOAD REMAPPED] Deep Transformed Payload: {remapped_payload}")
        await manager.broadcast("transform", f"🔄 [PAYLOAD REMAPPED] Applied deep transformations: {remapped_payload}", "info")
        
        # Security Event (Wait for SecurityValidationAgent to approve)
        # For security, we actually await this event unlike others, to ensure blocking
        for agent in self.agents:
            if agent.name == "SecurityValidationAgent":
                await agent.on_event("on_payload_healed", original_payload=payload, healed_payload=remapped_payload, delta=delta)
        
        try:
            # 3. Attempt to re-execute with the healed payload
            result = await original_executor(remapped_payload)
            print(f"[SUCCESS] Re-execution successful.")
            await manager.broadcast("reexecute", f"✨ [SUCCESS] Re-execution successful.", "success")
            
            # Fire post-execution event (ASTPatchingAgent will pick this up to patch code)
            await self.emit_event("on_successful_execution", tool_name=tool_name, delta=delta)
                
            return result
        except Exception as e:
            print(f"[FATAL] Re-execution failed even after healing: {e}")
            raise e

# Singleton instance
engine = AutoHealEngine()
