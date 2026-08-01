import os
import difflib
from datetime import datetime
import libcst as cst

from engine.plugins.base import AutoHealPlugin
from engine.telemetry import manager

class PayloadKeyTransformer(cst.CSTTransformer):
    """
    Surgically visits only Dictionary Elements in the syntax tree,
    swapping broken keys while preserving all surrounding code/comments perfectly.
    """
    def __init__(self, delta: dict):
        self.delta = delta
        self.patched = False

    def leave_DictElement(self, original_node: cst.DictElement, updated_node: cst.DictElement) -> cst.DictElement:
        if isinstance(updated_node.key, cst.SimpleString):
            key_value = updated_node.key.evaluated_value
            if key_value in self.delta:
                new_key = self.delta[key_value].get("key_mapping")
                if new_key:
                    self.patched = True
                    # Replace the node losslessly
                    new_key_node = cst.SimpleString(value=f'"{new_key}"')
                    return updated_node.with_changes(key=new_key_node)
        return updated_node



class ASTPatchingAgent(AutoHealPlugin):
    """
    AST Auto-Patching Agent (Human-in-the-Loop).
    Instead of editing production code directly, this agent simulates opening a GitHub Pull Request
    by generating a .diff patch file for a human Senior Engineer to review.
    """
    async def handle_on_successful_execution(self, tool_name: str, delta: dict):
        print(f"[{self.name}] Attempting to generate Pull Request patch for tool: {tool_name}")
        await manager.broadcast("mechanic", "[ASTPatchingAgent] Analyzing source code for Pull Request...", "warning")
        
        # For the hackathon demo, we explicitly target demo/agents/primary_agent.py
        target_file = os.path.join("demo", "agents", "primary_agent.py")
        
        if not os.path.exists(target_file):
            print(f"[{self.name}] Could not find {target_file} to patch.")
            return

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Parse the source code into a Concrete Syntax Tree (Lossless)
        try:
            source_tree = cst.parse_module(content)
        except Exception as e:
            print(f"[{self.name}] Failed to parse AST: {e}")
            return

        # 2. Traverse the tree and surgically mutate dictionary keys
        transformer = PayloadKeyTransformer(delta)
        modified_tree = source_tree.visit(transformer)
        
        patched = transformer.patched
        new_content = modified_tree.code

        if patched:
            # Human-in-the-Loop: Generate a diff patch instead of overwriting the file
            original_lines = content.splitlines(keepends=True)
            new_lines = new_content.splitlines(keepends=True)
            
            diff = difflib.unified_diff(
                original_lines, 
                new_lines, 
                fromfile=f"a/{target_file}", 
                tofile=f"b/{target_file}", 
                n=3
            )
            
            diff_text = "".join(diff)
            
            # Save the patch file
            timestamp = datetime.now().strftime("%Y%md_%H%M%S")
            pr_id = hash(timestamp) % 10000
            patch_filename = f"PR_{pr_id}_patch.diff"
            
            with open(patch_filename, "w", encoding="utf-8") as f:
                f.write(diff_text)
                
            print(f"[{self.name}] 🚀 Generated Pull Request patch: {patch_filename}")
            await manager.broadcast("mechanic", f"🚀 [ASTPatchingAgent] Opened GitHub PR #{pr_id} for Human Review! (See {patch_filename})", "success")
        else:
            print(f"[{self.name}] No hardcoded keys found to patch in {target_file}.")
