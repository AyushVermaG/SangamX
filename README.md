# SangamX — Multi-Agent AI Collaboration Platform

SangamX orchestrates a team of specialised AI agents (Planner, Researcher, Analyst, Critic, Synthesizer) that collaborate, debate, and self-correct to produce high-quality answers to complex queries. A LangGraph state machine drives the pipeline; a FastAPI backend exposes it over HTTP + SSE; a React/Vite frontend provides the interactive UI.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        React / Vite UI                       │
│   Landing Page  ──►  Engine Page  (SSE stream display)       │
└────────────────────────────┬────────────────────────────────┘
                             │  HTTP / SSE
┌────────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend (uvicorn)                   │
│                                                              │
│  POST /api/v1/engine/run  ──►  background asyncio task       │
│  GET  /api/v1/engine/status/{id}                             │
│  GET  /api/v1/engine/stream/{id}  ──►  SSE events            │
│  GET  /health                                                │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                  LangGraph Engine  (app/engine/)              │
│                                                              │
│   ┌──────────┐   ┌────────────┐   ┌──────────┐             │
│   │ Planner  │──►│ Researcher │──►│ Analyst  │             │
│   └──────────┘   └────────────┘   └────┬─────┘             │
│                                        │                     │
│                                   ┌────▼─────┐             │
│                                   │  Critic  │             │
│                                   └────┬─────┘             │
│                        agree?          │  disagree?         │
│                     ┌──────────────────┤                    │
│                     ▼                  ▼                    │
│              ┌────────────┐    ┌──────────────┐            │
│              │ Synthesizer│    │ Revision loop │            │
│              └─────┬──────┘    └──────┬───────┘            │
│                    │                  │ (max 1 round)       │
│                    └──────────────────┘                     │
│                           │                                 │
│                     final_answer                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Repository Layout

```
SangamX/
├── .gitignore
├── README.md
├── backend/
│   ├── main.py                      # FastAPI app factory + lifespan
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── config.py                # Settings (pydantic + python-dotenv)
│       ├── api/v1/engine.py         # POST /run, GET /status, GET /stream (SSE)
│       └── engine/
│           ├── state.py             # AgentState TypedDict + all Pydantic models
│           ├── graph.py             # LangGraph StateGraph (full pipeline)
│           ├── executor.py          # asyncio.gather parallel execution
│           ├── disagreement.py      # critic wrapper for disagreement detection
│           ├── providers.py         # get_llm() — Gemini / OpenAI selector
│           └── agents/
│               ├── planner.py
│               ├── researcher.py
│               ├── analyst.py
│               ├── critic.py
│               └── synthesizer.py
├── backend/prompts/                 # System prompt text files per agent
│   ├── planner.txt
│   ├── researcher.txt
│   ├── analyst.txt
│   ├── critic.txt
│   └── synthesizer.txt
├── backend/tests/
│   ├── conftest.py
│   ├── test_state_models.py         # 8 Pydantic model tests ✅
│   ├── test_config.py               # 4 settings tests ✅
│   ├── test_api_health.py
│   ├── test_disagreement.py
│   └── test_graph_flow.py
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── .env.example
    └── src/
        ├── App.jsx                  # Landing → EnginePage toggle
        ├── pages/EnginePage.jsx     # Full query→stream→result page
        ├── components/
        │   ├── QueryInput.jsx
        │   ├── AgentTrace.jsx       # Live SSE event feed
        │   └── FinalAnswer.jsx
        └── api/engineApi.js         # submitQuery, getTaskStatus, streamTaskEvents
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| pnpm | 8+ |

---

## Setup

### Backend

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
# Edit .env and fill in your API keys
```

### Frontend

```bash
cd frontend
pnpm install
cp .env.example .env     # or copy on Windows
# Edit .env if the backend runs on a different port
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key |
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key (fallback / critic) |
| `PLANNER_MODEL` | ❌ | `gemini-2.0-flash-exp` | Model for the Planner agent |
| `RESEARCHER_MODEL` | ❌ | `gemini-2.0-flash-exp` | Model for the Researcher agent |
| `ANALYST_MODEL` | ❌ | `gemini-2.0-flash-exp` | Model for the Analyst agent |
| `CRITIC_MODEL` | ❌ | `gemini-2.0-flash-exp` | Model for the Critic agent |
| `SYNTHESIZER_MODEL` | ❌ | `gemini-2.0-flash-exp` | Model for the Synthesizer agent |
| `CORS_ORIGINS` | ❌ | `http://localhost:5173` | Comma-separated allowed origins |
| `LOG_LEVEL` | ❌ | `INFO` | Python log level |
| `VITE_API_URL` | ❌ | `http://localhost:8000` | Frontend → Backend base URL |

---

## Running

### Backend (development)

```bash
cd backend
# Activate venv first (see Setup)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (development)

```bash
cd frontend
pnpm dev
# Opens at http://localhost:5173
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check → `{"status":"healthy"}` |
| `POST` | `/api/v1/engine/run` | Start a new engine run. Body: `QueryRequest`. Returns `task_id`. |
| `GET` | `/api/v1/engine/status/{task_id}` | Poll task status (`queued │ running │ done │ error`). |
| `GET` | `/api/v1/engine/stream/{task_id}` | SSE stream of `StreamEvent` objects until `done`/`error`. |

### QueryRequest schema

```json
{
  "query": "string (1–4000 chars)",
  "session_id": "string | null",
  "config": {
    "planner_model": "gemini-2.0-flash-exp",
    "researcher_model": "gemini-2.0-flash-exp",
    "analyst_model": "gemini-2.0-flash-exp",
    "critic_model": "gemini-2.0-flash-exp",
    "synthesizer_model": "gemini-2.0-flash-exp"
  }
}
```

### StreamEvent schema

```json
{
  "event": "agent_start | agent_done | disagreement | revision_start | final_answer | error | done",
  "agent": "string | null",
  "data": {},
  "timestamp": "ISO-8601"
}
```

---

## Running Tests

```bash
cd backend
# Activate venv first

# Fast tests (no API keys needed)
python -m pytest tests/test_state_models.py tests/test_config.py -v

# All tests (mocked LLM — still no real API keys)
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## Integration Guide for Aman (Frontend Developer)

### 1. Start a Run

```ts
// POST /api/v1/engine/run
const res = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/engine/run`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ query: userInput }),
});
const { task_id } = await res.json();
```

### 2. Stream Events

```js
// GET /api/v1/engine/stream/:task_id  (SSE — named events)
const es = new EventSource(
  `${import.meta.env.VITE_API_URL}/api/v1/engine/stream/${task_id}`
);

const EVENT_TYPES = ["agent_start","agent_done","disagreement",
                     "revision_start","final_answer","error","done"];

EVENT_TYPES.forEach(type => {
  es.addEventListener(type, (e) => {
    const data = JSON.parse(e.data);  // StreamEvent data payload
    // type: which event (agent_start | agent_done | disagreement |
    //        revision_start | final_answer | error | done)
    // data.agent: which agent fired (or null for system events)
    if (type === "done")  es.close();
    if (type === "error") es.close();
  });
});
```

### 3. Poll Status (optional fallback)

```ts
// GET /api/v1/engine/status/:task_id
const status = await fetch(
  `${import.meta.env.VITE_API_URL}/api/v1/engine/status/${task_id}`
).then(r => r.json());
// { task_id, status, final_answer, error, events_count }
```

### 4. Key contracts to rely on

| Contract | Detail |
|----------|--------|
| `task_id` | UUID string, stable for the lifetime of the server process |
| `status` values | `queued` → `running` → `done` or `error` |
| `final_answer` | Available on the `final_answer` StreamEvent **and** in `/status` after `done` |
| Revision loop | At most **1** revision round is ever triggered; the UI can show a "Revision in progress" banner on the `revision_start` event |
| Error handling | An `error` event is emitted before the stream closes on failure; check `event.data.message` |

---

## Contributing

1. Fork → feature branch → PR.
2. Run `pytest tests/test_state_models.py tests/test_config.py` before pushing — these must pass with zero real API keys.
3. Keep model names configurable via `.env`; never hard-code them in business logic.
