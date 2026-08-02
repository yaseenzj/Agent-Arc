import os
import difflib
from datetime import datetime
import libcst as cst
from github import Github

from engine.plugins.base import AutoHealPlugin
from engine.broadcaster import manager

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
        
        if transformer.patched:
            new_content = modified_tree.code
            
            # --- Authentic GitHub PR Integration ---
            gh_token = os.getenv("GITHUB_TOKEN")
            if not gh_token:
                await manager.broadcast("mechanic", "❌ GITHUB_TOKEN not found in .env! Cannot create PR.", "error")
                return
                
            try:
                g = Github(gh_token)
                repo = g.get_repo("yaseenzj/Agent-Arc")
                
                # Create a new branch
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                branch_name = f"autoheal-patch-{timestamp}"
                
                main_branch = repo.get_branch("main")
                repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
                
                # Update the file in the repository (use forward slashes for github path)
                github_file_path = "demo/agents/primary_agent.py"
                file_contents = repo.get_contents(github_file_path, ref="main")
                
                repo.update_file(
                    path=github_file_path,
                    message=f"AutoHeal: Schema drift fix for {tool_name}",
                    content=new_content,
                    sha=file_contents.sha,
                    branch=branch_name
                )
                
                # Format the delta for the PR body
                delta_details = ""
                for old_key, fix in delta.items():
                    new_key = fix.get('key_mapping')
                    math_mod = fix.get('value_math_modifier')
                    delta_details += f"- Swapped outdated key `{old_key}` ➜ `{new_key}`\n"
                    if math_mod:
                        delta_details += f"- Applied mathematical transformation: `{math_mod}`\n"
                
                pr_body = (
                    f"## 🛠️ AutoHeal Schema Fix\n\n"
                    f"The AutoHeal proxy detected a **400 Bad Request** caused by schema drift in `{tool_name}`. "
                    f"The payload was automatically intercepted and healed via **Llama 3.1**.\n\n"
                    f"### Transformations Inferred:\n{delta_details}\n"
                    f"*This PR applies the generated LibCST AST patch to fix the source code permanently.*"
                )
                
                # Open the Pull Request
                pr = repo.create_pull(
                    title=f"AutoHeal Patch: Schema Drift in {tool_name}",
                    body=pr_body,
                    head=branch_name,
                    base="main"
                )
                
                print(f"[{self.name}] 🚀 Generated Pull Request: {pr.html_url}")
                await manager.broadcast("mechanic", f"🚀 [ASTPatchingAgent] Opened Real GitHub PR #{pr.number}!", "success")
                await manager.broadcast("mechanic", f"[PR_URL] {pr.html_url}", "info")
                
            except Exception as e:
                print(f"[{self.name}] GitHub API Error: {e}")
                await manager.broadcast("mechanic", f"❌ GitHub API Error: {str(e)}", "error")
        else:
            print(f"[{self.name}] No hardcoded keys found to patch in {target_file}.")
