from typing import Any

from engine.plugins.base import AutoHealPlugin
from engine.telemetry import manager


class SecurityValidationAgent(AutoHealPlugin):
    """
    Zero-Trust Security Agent.
    Validates LLM inferred payloads before they are executed.
    """
    async def handle_on_payload_healed(self, original_payload: dict[str, Any], healed_payload: dict[str, Any], delta: dict):
        print(f"[{self.name}] Inspecting healed payload for malicious injections...")
        await manager.broadcast("security", "[SecurityValidationAgent] Inspecting healed payload for malicious injections...", "warning")
        
        # Simple heuristic security check (in a real app, this would be an SLM call or Pydantic validation)
        # Block anything trying to inject raw SQL or suspicious executable strings
        suspicious_keywords =["DROP TABLE", "SELECT *", "exec(", "os.system"]
        
        for key, value in healed_payload.items():
            if isinstance(value, str):
                for kw in suspicious_keywords:
                    if kw.lower() in value.lower():
                        print(f"[{self.name}] BLOCKED: Malicious payload detected: '{kw}'")
                        await manager.broadcast("security", "[SecurityValidationAgent] BLOCKED malicious payload!", "error")
                        raise ValueError(f"SecurityValidationAgent blocked malicious payload: {value}")
        
        print(f"[{self.name}] Payload approved. Safe for execution.")
        await manager.broadcast("security", "[SecurityValidationAgent] Payload approved. Safe for execution.", "success")
        return True
