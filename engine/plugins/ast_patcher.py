import os
import re

from engine.plugins.base import AutoHealPlugin
from engine.telemetry import manager


class ASTPatchingAgent(AutoHealPlugin):
    """
    AST Auto-Patching Agent.
    Permanently patches the primary agent's source code on disk so it stops making the same mistake.
    """
    async def handle_on_successful_execution(self, tool_name: str, delta: dict):
        print(f"[{self.name}] Attempting to auto-patch source code for tool: {tool_name}")
        await manager.broadcast("mechanic", "[ASTPatchingAgent] Attempting to auto-patch source code...", "warning")
        
        # For the hackathon demo, we explicitly target demo/agents/primary_agent.py
        target_file = os.path.join("demo", "agents", "primary_agent.py")
        
        if not os.path.exists(target_file):
            print(f"[{self.name}] Could not find {target_file} to patch.")
            return

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        patched = False
        new_content = content
        for old_key, mapping_rules in delta.items():
            new_key = mapping_rules.get("key_mapping")
            if not new_key:
                continue
            
            if f'"{old_key}"' in new_content or f"'{old_key}'" in new_content:
                new_content = re.sub(f'["\']{old_key}["\']', f'"{new_key}"', new_content)
                patched = True

        if patched:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[{self.name}] SUCCESSFULLY PATCHED source code in {target_file}!")
            await manager.broadcast("mechanic", "[ASTPatchingAgent] SUCCESSFULLY PATCHED source code!", "success")
        else:
            print(f"[{self.name}] No hardcoded keys found to patch in {target_file}.")
