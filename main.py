import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import BackgroundTasks, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from demo.agents.primary_agent import run_primary_agent
from demo.agents.stress_test import run_stress_test_agent
from demo.tools.mock_crm import MockFastMCPServer, mock_crm_tool, mock_salesforce_tool
from engine.engine import engine
from engine.interceptor import AutoHealMiddleware
from engine.plugins.ast_patcher import ASTPatchingAgent
from engine.plugins.security_validator import SecurityValidationAgent
from engine.telemetry import manager

app = FastAPI(title="AutoHeal Proxy Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#p&p
engine.register_plugin(SecurityValidationAgent())
engine.register_plugin(ASTPatchingAgent())

mcp_server = MockFastMCPServer()
mcp_server.register_tool("update_crm", mock_crm_tool)
mcp_server.register_tool("salesforce_crm", mock_salesforce_tool)

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
