# 🏛️ AutoHeal MCP Proxy - Architecture Design

## System Overview
The AutoHeal MCP Proxy is designed to decouple tool execution failure states from the primary AI agent. It acts as a FastMCP middleware interceptor that catches JSON-RPC validation exceptions (e.g., 400 Bad Request) indicating schema drift, and automatically self-heals the payload before the primary agent even notices a failure.

## Component Architecture

1. **Primary Agent**: The main reasoning engine trying to accomplish a workflow.
2. **FastMCP Server**: The host for the tools/APIs.
3. **AutoHeal Middleware (`interceptor.py`)**: Traps execution, catches validation errors, and passes the failed context to the orchestrator.
4. **Proxy Engine (`engine.py`)**: The central orchestrator for the self-healing workflow. Features `asyncio.Lock()` concurrency protection.
5. **Delta Cache (`cache.py`)**: An Enterprise PostgreSQL Database mapping old payload hashes to successful payload deltas for permanent memory and 0ms latency lookups.
6. **Inference Fallback (`inference.py`)**: High-speed Groq Cloud API (Llama 3.1 8B) tuned for structured JSON output to deduce schema mapping fixes and negotiate vendor swaps in under 0.2 seconds.
7. **AST Patcher (`ast_patcher.py`)**: Uses Meta's LibCST to perform lossless syntax tree modifications and generate GitHub Pull Request `.diff` patches.

## Request Lifecycle (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Agent as Primary Agent (Afsal)
    participant FastMCP as Proxy Interceptor (Yaseen)
    participant Engine as Proxy Engine (Yaseen)
    participant Cache as Postgres DB (Swaveel)
    participant Inference as Groq Llama 3.1 (Afsal)
    participant Tool as Target Tool (CRM)
    participant Backup as Backup Tool (Salesforce)

    Agent->>FastMCP: Call Tool (Drifted Payload)
    FastMCP->>Tool: Execute call_next()
    
    alt 400 Bad Request (Schema Drift)
        Tool-->>FastMCP: 400 Bad Request
        FastMCP->>Engine: heal_and_retry()
        Engine->>Cache: get_cached_delta(hash)
        alt Cache Miss
            Cache-->>Engine: None
            Engine->>Inference: infer_delta(schema, payload)
            Inference-->>Engine: {"old_key": "new_key"}
        else Cache Hit
            Cache-->>Engine: {"old_key": "new_key"}
        end
        Engine->>Engine: Remap Payload
        Engine->>Tool: Re-execute Mapped Payload
        Tool-->>Engine: 200 OK
        
    else 500 Internal Server Error (Outage)
        Tool-->>FastMCP: 500 Internal Server Error
        FastMCP->>Engine: vendor_swap()
        Engine->>Inference: negotiate_vendor_swap(payload, backup_schema)
        Inference-->>Engine: Translated Payload
        Engine->>Backup: Execute Backup Tool (Salesforce)
        Backup-->>Engine: 200 OK
    end
    
    Engine->>Cache: save_delta(hash, delta)
    Engine-->>FastMCP: Success Response
    FastMCP-->>Agent: Success
```
