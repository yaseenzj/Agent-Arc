# Project Rules & Best Practices

To maintain the integrity of the AutoHeal MCP Proxy, all team members must adhere to the following rules:

### 1. Zero Crash Policy in Proxy
The proxy middleware (`interceptor.py`) and engine (`engine.py`) must **never** crash the main thread unless it is a fatal non-validation error (e.g., Network Disconnect, 500 Server Error). All schema and payload issues must be gracefully trapped and healed.

### 2. Strict JSON Output (Inference)
The LLM inference fallback (`inference.py`) must use Structured Outputs / JSON Schema validation (via Pydantic). We cannot rely on parsing free-text markdown for payload deltas. 
- *Rule*: Always return exactly `{"old_key": "new_key"}` mappings.

### 3. Asynchronous Execution
All I/O operations (Redis cache checks, LLM network calls, tool executions) must be fully `async`. Do not use blocking synchronous calls anywhere in the `proxy` package to ensure high throughput.

### 4. Cache First, Infer Second
Never call the LLM directly on a tool failure without first checking the hash in the Redis cache. The LLM is a last resort.

### 5. Dependency Management
All dependencies (Redis clients, Pydantic, FastMCP, etc.) must be strictly managed in `pyproject.toml` via Astral's `uv`. No global `pip install` commands.

### 6. Mock Implementations
When building your module, if you depend on a teammate's code that isn't merged yet, use `try/except ImportError` blocks with dummy fallbacks (as seen in `engine.py`) so your code can be tested in isolation.
