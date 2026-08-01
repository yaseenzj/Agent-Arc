import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.telemetry import manager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from src.transport.interceptor import AutoHealMiddleware
from demo.mock_targets.crm_tool import MockFastMCPServer, mock_crm_tool
from demo.agent import run_primary_agent
from demo.agents.stress_test import run_stress_test_agent

app = FastAPI(title="AutoHeal Proxy Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Vite frontend (port 5173) to communicate
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Initialize Mock FastMCP Server
mcp_server = MockFastMCPServer()

# 2. Register Target Tool (CRM System with Schema Drift)
mcp_server.register_tool("update_crm", mock_crm_tool)

# 3. Register Middleware Interceptor (Yaseen's AutoHeal)
mcp_server.add_middleware(AutoHealMiddleware())

@app.get("/")
def read_root():
    return {"message": "AutoHeal MCP Proxy is running. Use /api/run_agent or /api/run_stress_test."}

@app.post("/api/run_agent")
async def api_run_agent(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_primary_agent, mcp_server)
    return {"status": "Primary agent dispatched. Check terminal logs."}

@app.post("/api/run_stress_test")
async def api_run_stress_test(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_stress_test_agent, mcp_server)
    return {"status": "Stress Test agent dispatched. Check terminal logs."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
