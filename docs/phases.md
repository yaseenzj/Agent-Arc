# Implementation Phases

## Phase 1: Core Proxy Engine (Yaseen - Completed)
- [x] Create the interceptor middleware.
- [x] Create the orchestrator engine (`engine.py`).
- [x] Build the mock FastMCP server and live demo script (`main.py`).

## Phase 2: Persistent Caching (Swaveel - Next)
- [ ] Initialize `uv` project and `pyproject.toml`.
- [ ] Set up a local Redis docker container.
- [ ] Implement `proxy/cache.py` with async Redis functions:
  - `get_cached_delta(tool_name, payload_hash)`
  - `save_delta(tool_name, payload_hash, delta)`

## Phase 3: Inference Fallback Engine (Afsal - Next)
- [ ] Install and configure Ollama (e.g., Llama 3.1 8B or Qwen2.5 7B).
- [ ] Implement `proxy/inference.py` using Pydantic v2 schemas to ensure the local model strictly outputs `{"old_key": "new_key"}` JSON mappings.
- [ ] Build the mock `crm_tool.py` MCP target with a drifting schema toggle.
- [ ] Build `primary_agent.py` to trigger the actual workflow.

## Phase 4: Integration & Optimization
- [ ] Wire Swaveel's Cache and Afsal's Inference into Yaseen's Engine.
- [ ] Perform end-to-end latency testing.
- [ ] Finalize logging formatting for the live hackathon presentation.
