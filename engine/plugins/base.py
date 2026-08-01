import asyncio
from typing import Any


class AutoHealPlugin:
    """
    Base class for all Plug-and-Play AutoHeal plugins.
    Plugins subscribe to specific events emitted by the orchestrator event bus.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__

    async def on_event(self, event_name: str, **kwargs) -> Any:
        """
        Routing method that orchestrator calls.
        Subclasses should implement specific event handlers (e.g. handle_on_schema_drift).
        """
        handler = getattr(self, f"handle_{event_name}", None)
        if handler and asyncio.iscoroutinefunction(handler):
            try:
                return await handler(**kwargs)
            except Exception as e:
                print(f"[{self.name}] Error handling event '{event_name}': {e}")
        return None
