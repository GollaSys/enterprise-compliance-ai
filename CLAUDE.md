# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Backend (requires Python 3.11+, venv activated)
source venv/bin/activate
pip install -r requirements-minimal.txt          # lightweight deps (no AI/DB)
pip install -r requirements.txt                  # full deps (CrewAI, SQLAlchemy, LangGraph, mem0, etc.)
python -m uvicorn src.api.main_simple:app --port 8001 --reload

# Frontend (requires Node.js 18+)
cd frontend && npm install --legacy-peer-deps
REACT_APP_API_URL=http://localhost:8001 npm start
# Node 23+: prepend NODE_OPTIONS=--openssl-legacy-provider

# Docker (7 services: postgres, redis, chroma, backend, frontend + langfuse-db, langfuse)
docker-compose up -d --build
docker-compose down -v                           # stop + remove volumes

# Demo shortcuts (Makefile)
make demo        # start all services + print URLs (frontend :3000, backend :8001, Langfuse :3001)
make demo-stop   # stop Langfuse services + kill local dev processes
make smoke       # scripts/demo_smoke_test.py — real LLM calls, ~30s
make dev         # docker infra + backend + frontend in one shot
make clean       # rm __pycache__, .pytest_cache, data/checkpoints.db
```

## Testing

Backend must be running on port 8001 before integration tests:

```bash
python test_api.py           # 10 API endpoint tests
python test_complete.py      # 11 tests including E2E workflow
python -m pytest tests/ -v   # unit tests (agents + eval judges)
python -m pytest tests/ -v -m "not eval"   # skip slow LLM eval tests
```

### Eval suite (LangSmith Evaluations API)

```bash
python evals/dataset.py                        # seed LangSmith dataset (idempotent)
python evals/run_evals.py                      # run eval CLI — prints table + saves JSON to evals/results/
python -m pytest tests/test_evals.py -m eval   # CI gate — asserts score thresholds
```

5 evaluators across 3 examples (GDPR x2, SOX x1):
- `pipeline_completeness` — all 5 agents ran, no mock fallbacks (threshold 1.0)
- `requirements_extracted` — ≥ 3 article references extracted (threshold 1.0)
- `gaps_identified` — ≥ 1 gap identified (threshold 1.0)
- `risk_scores_valid` — all scores in [1,10], valid priority labels (threshold 1.0)
- `report_coherence` — LLM-as-judge (gpt-4o-mini) rates report vs gaps (threshold 0.7)

Results appear in LangSmith under `compliance-demo-eval` → Experiments tab.

## Linting & Formatting

```bash
poetry run black src/        # format (88 char lines, py311)
poetry run isort src/        # sort imports (black-compatible profile)
poetry run flake8 src/       # lint
poetry run mypy src/         # type check (strict mode)
```

## Architecture

### Two backend entry points

- `src/api/main_simple.py` — Lightweight, in-memory stores, zero external deps. Used in Docker and for rapid testing. Mounts both the legacy routers and `/api/v2/demo/`.
- `src/api/main.py` — Full orchestration with ComplianceOrchestrator, StorageService, async lifespan, background tasks. Requires PostgreSQL, Redis, ChromaDB.

### Request flow

```
React (3000) --Axios/SSE--> FastAPI (8001) --> Routers --> Services/Demo --> Agents/DB
```

### Two parallel agent systems

**1. Legacy CrewAI agents** (`src/agents/`) — used by `main.py` via `src/services/orchestrator.py`:
- All inherit from `BaseComplianceAgent` (structlog logging, tenacity retry — 3 attempts, exponential backoff 4–10s)
- 5 agents: RegulatoryAnalyst, PolicyMapper, EvidenceValidator, RiskScorer, ExecutiveReporter
- Routers in `src/api/routers/` dispatch to these (one file per domain: dashboard, compliance, documents, agents, reports)
- **Tool creation**: CrewAI v1+ requires `crewai.tools.BaseTool` subclasses — `langchain_core.tools.Tool` is rejected at validation time. Use `make_crewai_tool(name, description, func)` from `src/agents/base_agent.py` to wrap bound methods into BaseTool instances via dynamic class + closure.

**2. Demo LangGraph pipeline** (`src/demo/`) — mounted at `/api/v2/demo/` in `main_simple.py`:
- `src/demo/graph/workflow.py` — builds a sequential `StateGraph`: `START → regulatory_analyst → policy_mapper → evidence_validator → risk_scorer → executive_reporter → END`. Each edge checks `state.error` and can route to an `error_handler` node.
- `src/demo/graph/state.py` — `ComplianceState` TypedDict holding `sse_events`, `a2a_tasks`, `error`, and per-agent outputs.
- `src/demo/agents/` — 5 LangGraph node functions (one file each). Each node reads the last `A2ATask` from state, does its work, and appends a new `A2ATask`.
- `src/demo/a2a_types.py` — Google A2A Protocol Pydantic models (`A2ATask`, `TaskArtifact`, `MCPCall`, `AgentCard`). Agents communicate by writing structured envelopes into shared state, not by calling each other directly.
- `src/demo/mcp/client.py` — `MCPClient` tries a Node.js MCP subprocess (5s timeout) then falls back to direct disk reads from `data/regulations/`. Demo never crashes when MCP servers are unavailable.
- `src/demo/memory/mem0_client.py` — `Mem0Client` wraps mem0 with graceful degradation. Uses ChromaDB at `data/mem0/` as the vector store. All failures are logged and swallowed — demo continues without memory.
- `src/demo/observability/` — `langfuse.py` (Langfuse tracing client, emits trace URLs into SSE events) and `terminal.py`.
- **SSE streaming uses `AsyncSqliteSaver`** — `build_workflow()` uses sync `SqliteSaver` for `app.invoke()`; `astream_compliance_pipeline()` uses `AsyncSqliteSaver.from_conn_string()` as an async context manager so `app.astream()` can await checkpoint reads/writes.
- `src/demo/router.py` — FastAPI router with 4 endpoints: `GET /health`, `GET /agents` (A2A agent card discovery), `POST /run` (synchronous), `GET /stream` (SSE).

### SSE streaming

The `GET /api/v2/demo/stream` endpoint uses `sse_starlette.sse.EventSourceResponse`. The graph yields `sse_events` from state after each node. The frontend `frontend/src/hooks/useAgentStream.ts` opens an `EventSource`, parses events, and updates `agentStatuses` and `traceUrls` state. The demo page is at `/demo` (React Router route → `frontend/src/pages/AgentDemo.tsx`).

### Services (legacy path)

- `orchestrator.py` — coordinates CrewAI agent execution, falls back to mock agents on init failure
- `storage_service.py` — file persistence to `./data/`, activity logging
- `document_service.py` — async upload with ThreadPoolExecutor (4 workers), SHA256 hashing
- `rag_service.py` — OpenAI embeddings + ChromaDB, chunking (1000 chars, 200 overlap)

### Frontend

React 18 + TypeScript, MUI components, TanStack React Query for server state, Recharts for visualizations. React Router DOM for routing. API client in `frontend/src/services/api.ts`. SSE hook in `frontend/src/hooks/useAgentStream.ts`.

## Key Patterns

- **Pydantic models** for all request/response schemas: `src/models/schemas.py` (legacy) and `src/demo/a2a_types.py` (demo pipeline)
- **In-memory stores** in `main_simple.py` use Python dicts/lists (`documents_store`, `compliance_analyses`, `reports_store`, `policies_store`, `risks_store`)
- **Background tasks** — legacy compliance analysis runs async via FastAPI `BackgroundTasks`; client polls status/results endpoints
- **LangGraph checkpointing** — `SqliteSaver` persists graph state to `data/checkpoints.db` for short-term checkpoint/resume across a single run
- **mem0 long-term memory** — `EvidenceValidator` reads prior findings; `RiskScorer` writes new findings. Run the demo twice to observe memory recall. If `data/mem0/` gets corrupted (ChromaDB version mismatch causes a Rust `PanicException`), delete the directory and it will be recreated on next run.
- **Config** — `src/core/config.py` uses Pydantic `BaseSettings` loading from `.env`
- **CORS** — backend allows all origins (`["*"]`) in development
- **LangChain package layout** — `langchain` v0.3+ split text splitters into `langchain_text_splitters` and documents into `langchain_core.documents`. Import from those packages directly, not from the top-level `langchain.*`.
- **Exception handling in `_load_long_term_memory`** — uses `except BaseException` (not `except Exception`) because PyO3 Rust panics raise `pyo3_runtime.PanicException` which inherits from `BaseException`.

## Environment Variables

For `main_simple.py` (the active dev path): only `OPENAI_API_KEY` matters (optional — agents return mock data without it). Langfuse tracing requires `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` (defaults to `http://localhost:3001`). See `.env.example` for full list including `DATABASE_URL` and `SECRET_KEY` needed for `main.py`.

**LangSmith tracing** (langsmith v0.7+): use `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true`, `LANGSMITH_ORG_ID`, `LANGCHAIN_PROJECT`. Note: the old `LANGCHAIN_API_KEY` / `LANGCHAIN_TRACING_V2` names are ignored by langsmith v0.7+. When starting uvicorn, use `env -i` to ensure a clean environment picks up the updated `.env` values — `load_dotenv()` won't override vars already set in the shell.

## Docker Topology

7 containers on `compliance-network` bridge:
- `compliance-postgres` (5432) — PostgreSQL 15, health-checked via `pg_isready`
- `compliance-redis` (6379) — Redis 7 with AOF persistence
- `compliance-chroma` (8000) — ChromaDB vector store (also used by mem0 at `data/mem0/`)
- `compliance-backend` (8001) — Python 3.11-slim, runs `main_simple.py`, depends on postgres healthy
- `compliance-frontend` (3000) — Node 18-alpine, nginx serves React build
- `langfuse-db` (5433) — Postgres 15 for Langfuse
- `langfuse` (3001) — Langfuse 2 observability UI; trace links emitted into SSE events

## Data Directory

```
data/
  checkpoints.db        # LangGraph SqliteSaver (short-term, per-run state)
  mem0/                 # ChromaDB vectors for mem0 long-term memory (gitignored)
  samples/
    gdpr_policy_sample.txt   # Seeded GDPR doc used as default demo input
  regulations/          # Bundled regulation text files (MCP fallback)

evals/
  __init__.py
  dataset.py            # Seeds LangSmith dataset 'compliance-demo-eval' (idempotent)
  judges.py             # 4 heuristic + 1 LLM-as-judge evaluators
  run_evals.py          # CLI runner: evaluate() + score table + JSON output
  results/              # Timestamped JSON eval results (gitignored)
```
