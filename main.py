import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse
import uvicorn

from src.transport.interceptor import AutoHealMiddleware
from demo.mock_targets.crm_tool import MockFastMCPServer, mock_crm_tool
from demo.agent import run_primary_agent
from demo.agents.gremlin import run_gremlin_agent

app = FastAPI(title="AutoHeal Proxy Control Plane")

# 1. Initialize Mock FastMCP Server
mcp_server = MockFastMCPServer()

# 2. Register Target Tool (CRM System with Schema Drift)
mcp_server.register_tool("update_crm", mock_crm_tool)

# 3. Register Middleware Interceptor (Yaseen's AutoHeal)
mcp_server.add_middleware(AutoHealMiddleware())

@app.get("/")
def read_root():
    return {"message": "AutoHeal MCP Proxy is running. Use /api/run_agent or /api/run_gremlin."}

@app.post("/api/run_agent")
async def api_run_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_primary_agent, mcp_server)
    return {"status": "Primary agent dispatched. Check terminal logs."}

@app.post("/api/run_gremlin")
async def api_run_gremlin(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_gremlin_agent, mcp_server)
    return {"status": "Gremlin chaos agent dispatched. Check terminal logs."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
