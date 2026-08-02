# 🚀 Enterprise Neural Control Plane: AutoHeal A2A Architecture

> **Elevator Pitch:** A self-healing, multi-agent AI pipeline that automatically detects schema drift, infers fixes via Groq's lightning-fast LPU, safely patches payloads in 0ms using PostgreSQL, and opens automated GitHub Pull Requests via True AST Patching—all visualized through a stunning, real-time glassmorphism React dashboard.

---

## 🛑 The Problem We Solve
In microservice and agentic architectures (A2A), APIs evolve constantly. When a target API changes its expected schema (e.g., from `amount_usd` to `total_cents`), traditional AI agents crash, requiring manual developer intervention to update hardcoded payloads and parse new documentation.

## 🛠️ Our Solution: The AutoHeal Engine
We built a deterministic, zero-downtime interceptor that automatically traps these errors and heals the system on the fly without dropping the request.

### 🧠 Core Architecture

1. **FastMCP Interceptor (The Shield)**
   - Wraps outgoing tool calls. If a 400 Bad Request (Schema Drift) occurs, it halts the crash and diverts the payload to the Orchestrator.
   
2. **A2A Event Bus (The Nervous System)**
   - An asynchronous event-driven orchestrator that broadcasts the error context to our specialized Plugin Agents. It utilizes `asyncio.Lock()` to perfectly handle massive concurrency (e.g., if 50 agents fail at the exact same time).

3. **Groq Inference & Postgres Cache (The Brain)**
   - Queries Groq (Llama 3.1) to dynamically generate deep transformation rules or negotiate vendor swaps in 0.2 seconds.
   - Caches the rules in an Enterprise PostgreSQL Database. Future failures are healed in **0ms** via Cache Hits, completely bypassing the LLM.

4. **SecurityValidationAgent (The Guard)**
   - Inspects every dynamically healed payload to ensure the LLM hasn't hallucinated malicious prompt injections before re-execution.

5. **ASTPatchingAgent (Human-in-the-Loop PR Bot)**
   - Once a payload successfully re-executes, this agent parses the Python Concrete Syntax Tree (CST) using LibCST. It perfectly isolates the broken dictionary key, losslessly mutates it while preserving comments, and opens a simulated GitHub Pull Request `.diff` patch for a Senior Engineer to review.

---

## 🎮 How to Demo This (Hackathon Guide)

We built an incredible **Vite + React Flow** frontend to visualize this broadcaster stream in real time. 

### Action 1: The Concurrency Stress Test
Click **"Run Stress Test"** on the dashboard.
- **What it does:** Fires 3 simultaneous, outdated payloads to simulate a high-traffic production crash.
- **What to highlight to judges:** Point out how the UI beautifully traces the glowing cyan path. Show them the terminal logs proving that the `asyncio.Lock()` worked perfectly: it queried Groq exactly *once*, and served *Cache Hits* (0ms) from Postgres to the other concurrent requests, saving massive compute costs.

### Action 2: The Human-in-the-Loop PR Fix
Click **"Run Primary Agent"**.
- **What it does:** Fires the normal agent.
- **What to highlight to judges:** Point out the **ASTPatchingAgent**. Show them that instead of blindly overwriting code on a production server (which is a security violation), it executes a lossless `LibCST` tree transformation and generates an industry-standard `.diff` Pull Request file for a human to review.

---

## 💻 Tech Stack
- **AI & Inference:** Groq Cloud API, Llama 3.1 (8B-Instant)
- **Backend:** FastAPI, Python `asyncio`, LibCST (True AST Patching)
- **Database:** PostgreSQL (`asyncpg`)
- **Frontend:** React, Vite, `@xyflow/react` (for the interactive neural graph), Vanilla CSS
- **Infrastructure:** `uv` (Rust-based Python package manager), Pydantic v2
