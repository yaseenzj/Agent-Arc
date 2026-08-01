import ast
import os
import re
from src.agents.base import BaseAgent
from typing import Dict, Any

class MechanicAgent(BaseAgent):
    """
    AST Auto-Patching Agent.
    Permanently patches the primary agent's source code on disk so it stops making the same mistake.
    """
    async def handle_on_successful_execution(self, tool_name: str, delta: dict):
        print(f"🔧 [{self.name}] Attempting to auto-patch source code for tool: {tool_name}")
        
        # For the hackathon demo, we explicitly target demo/agent.py
        target_file = os.path.join("demo", "agent.py")
        
        if not os.path.exists(target_file):
            print(f"[{self.name}] Could not find {target_file} to patch.")
            return

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        # A robust enterprise version would use libCST or AST to walk the tree.
        # For the live demo, we will use a targeted regex to rewrite the dictionary payload
        # based on the delta mappings.
        patched = False
        new_content = content
        for old_key, mapping_rules in delta.items():
            new_key = mapping_rules.get("key_mapping")
            if not new_key:
                continue
            
            # Simple string replacement for demo purposes.
            # Replace: "amount_usd": 500  -> "total_cents": 500
            # Note: This is highly simplified for the hackathon visual!
            if f'"{old_key}"' in new_content or f"'{old_key}'" in new_content:
                new_content = re.sub(f'["\']{old_key}["\']', f'"{new_key}"', new_content)
                patched = True

        if patched:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"🚀 [{self.name}] SUCCESSFULLY PATCHED source code in {target_file}!")
        else:
            print(f"[{self.name}] No hardcoded keys found to patch in {target_file}.")
