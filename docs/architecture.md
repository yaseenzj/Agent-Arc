# AutoHeal MCP Proxy - Architecture Design

## System Overview
The AutoHeal MCP Proxy is designed to decouple tool execution failure states from the primary AI agent. It acts as a FastMCP middleware interceptor that catches JSON-RPC validation exceptions (e.g., 400 Bad Request) indicating schema drift, and automatically self-heals the payload before the primary agent even notices a failure.

## Component Architecture

1. **Primary Agent**: The main reasoning engine trying to accomplish a workflow.
2. **FastMCP Server**: The host for the tools/APIs.
3. **AutoHeal Middleware (`interceptor.py`)**: Traps execution, catches validation errors, and passes the failed context to the orchestrator.
4. **Proxy Engine (`engine.py`)**: The central orchestrator for the self-healing workflow.
5. **Delta Cache (`cache.py`)**: A high-speed Redis key-value store mapping old payload hashes to successful payload deltas.
6. **Inference Fallback (`inference.py`)**: A fast, local LLM (e.g., Ollama running Llama 3.1 8B) tuned for structured JSON output to deduce schema mapping fixes.

## Request Lifecycle (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Agent as Primary Agent (Afsal)
    participant FastMCP as Proxy Interceptor (Yaseen)
    participant Engine as Proxy Engine (Yaseen)
    participant Cache as Redis Cache (Swaveel)
    participant Inference as Local LLM (Afsal)
    participant Tool as Target Tool (CRM)

    Agent->>FastMCP: Call Tool (Drifted Payload)
    FastMCP->>Tool: Execute call_next()
    Tool-->>FastMCP: 400 Bad Request / Validation Error
    FastMCP->>Engine: heal_and_retry(payload, error)
    
    Engine->>Cache: get_cached_delta(hash)
    alt Cache Miss
        Cache-->>Engine: None
        Engine->>Inference: infer_delta(schema, payload, error)
        Inference-->>Engine: {"old_key": "new_key"}
    else Cache Hit
        Cache-->>Engine: {"old_key": "new_key"}
    end
    
    Engine->>Engine: Remap Payload
    Engine->>Tool: Re-execute with Mapped Payload
    Tool-->>Engine: 200 OK
    Engine->>Cache: save_delta(hash, delta)
    Engine-->>FastMCP: Success Response
    FastMCP-->>Agent: Success
```
