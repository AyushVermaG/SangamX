# SangamX Backend

FastAPI backend orchestrating the multi-agent AI collaboration pipeline for SangamX. Exposes HTTP and Server-Sent Events (SSE) streaming endpoints to the frontend, manages task lifecycles and event queues, and interfaces with the LangGraph multi-agent engine via a dedicated `EngineAdapter`.

---

## Architecture Overview

```
Frontend (React/Vite)
       │
       ▼ (HTTP / SSE)
FastAPI Application (main.py / app/api/v1/engine.py)
       │
       ├── TaskStore (app/task_store.py)
       │     ├── Concurrency-safe task state tracking (asyncio.Lock)
       │     ├── Live Event Distribution (Pub/Sub)
       │     ├── Historical Event Replay on Reconnect
       │     ├── Cancellation & Task Worker Management
       │     └── Automatic TTL Expired Task Cleanup
       │
       └── EngineAdapter (app/engine/adapter.py)
             ├── Task ID & Session Context Propagation
             ├── Event Normalization & Terminal Event Guarantees
             └── AI Engine Entry Point (app/engine/graph.py)
```

---

## API Endpoints

### Health Check

- **`GET /health`**
  - **Response:** `200 OK`
  - **Body:** `{"status": "healthy"}`

### Workflow Execution

- **`POST /api/v1/engine/run`**
  - Submits a query to start an asynchronous multi-agent engine execution.
  - **Status Code:** `200 OK`
  - **Request Body:**
    ```json
    {
      "query": "Explain quantum computing in simple terms.",
      "session_id": "optional-custom-session-id",
      "config": {
        "planner_provider": "gemini",
        "planner_model": "gemini-2.0-flash-exp",
        "critic_provider": "groq",
        "critic_model": "llama-3.1-8b-instant"
      }
    }
    ```
  - **Response:**
    ```json
    {
      "task_id": "c1f7a0b3-9e45-4df3-a3d8-5ecf36d40019",
      "status": "queued"
    }
    ```

### Task Status Polling

- **`GET /api/v1/engine/status/{task_id}`**
  - Polls current task state, final answer, error details, and event counts.
  - **Status Code:** `200 OK` (or `404 Not Found`)
  - **Response:**
    ```json
    {
      "task_id": "c1f7a0b3-9e45-4df3-a3d8-5ecf36d40019",
      "status": "done",
      "final_answer": "Quantum computing uses qubits...",
      "error": null,
      "events_count": 7
    }
    ```

### Real-Time Event Streaming (SSE)

- **`GET /api/v1/engine/stream/{task_id}`**
  - Server-Sent Events stream delivering live agent events as JSON frames.
  - Supports transparent client reconnection by replaying event history prior to streaming new live events.
  - Concludes stream cleanly on backend terminal event (`workflow_completed`, `workflow_failed`, or `cancelled`).
  - **SSE Event Types:**
    - `agent_start`: An agent begins work (Planner, Researcher, Analyst, Critic, Synthesizer).
    - `agent_done`: An agent completes its step.
    - `revision_start`: Disagreement triggers a revision pass.
    - `disagreement`: Critic detects contradiction between researcher and analyst.
    - `final_answer`: Synthesizer produces the final merged answer.
    - `error`: Emitted if an unrecoverable failure occurs in an agent node.
    - `workflow_completed`: Backend terminal event emitted on successful workflow execution.
    - `workflow_failed`: Backend terminal event emitted on workflow failure.
    - `cancelled`: Emitted if task is cancelled by user.

### Task Management

- **`GET /api/v1/engine/tasks`**
  - Lists recent active and concluded tasks.
  - **Status Code:** `200 OK`

- **`DELETE /api/v1/engine/cancel/{task_id}`**
  - Cancels an active or queued task, halts background execution, and emits cancellation events.
  - **Status Code:** `200 OK` (or `404 Not Found`)

---

## Configuration & Environment Variables

Copy `.env.example` to `.env` in the `backend/` directory:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | `""` | Google Gemini API Key (free tier: Google AI Studio) |
| `GROQ_API_KEY` | `""` | Groq API Key (free tier: Groq Cloud) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama inference server address |
| `OLLAMA_MODEL` | `qwen3:4b` | Default local model fallback |
| `OLLAMA_MAX_CONCURRENCY` | `2` | Max concurrent Ollama local inference requests |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins (comma-separated) |
| `LOG_LEVEL` | `INFO` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> **Zero-Cost Guarantee:** SangamX only uses free-tier API quotas (Gemini / Groq) and local Ollama inference. Paid APIs and paid fallbacks are strictly prohibited.

---

## Running the Backend

### Prerequisites

Python 3.11+ installed.

### Start the Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Running Backend Tests

Backend tests use `pytest` and `pytest-asyncio` in `auto` mode. External AI provider dependencies are safely stubbed in `conftest.py` so the full test suite runs without consuming real credentials or external quotas.

```bash
cd backend
python -m pytest tests/ -v
```

### Test Suite Structure

| File | Scope |
| :--- | :--- |
| `tests/test_api_health.py` | Health endpoint and API status codes |
| `tests/test_config.py` | Pydantic configuration and environment variables |
| `tests/test_disagreement.py` | Disagreement detection logic |
| `tests/test_engine_adapter.py` | EngineAdapter event forwarding and terminal guarantees |
| `tests/test_graph_flow.py` | Workflow orchestration, routing logic, bounded revision |
| `tests/test_integration.py` | Full HTTP workflow (run, status, tasks, cancel, 404s) |
| `tests/test_providers.py` | Provider abstraction, Groq/Gemini/Ollama fallback |
| `tests/test_sse_stream.py` | SSE formatting, multi-listener pub/sub, reconnection replay |
| `tests/test_state_models.py` | Pydantic schemas and typed state definitions |
| `tests/test_task_store.py` | Concurrency safety, lifecycle transitions, TTL eviction |
