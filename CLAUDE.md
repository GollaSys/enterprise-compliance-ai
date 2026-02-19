# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands

```bash
# Backend (requires Python 3.11+, venv activated)
source venv/bin/activate
pip install -r requirements-minimal.txt          # lightweight deps (no AI/DB)
pip install -r requirements.txt                  # full deps (CrewAI, SQLAlchemy, etc.)
python -m uvicorn src.api.main_simple:app --port 8001 --reload

# Frontend (requires Node.js 18+)
cd frontend && npm install --legacy-peer-deps
REACT_APP_API_URL=http://localhost:8001 npm start
# Node 23+: prepend NODE_OPTIONS=--openssl-legacy-provider

# Docker (all 5 services: postgres, redis, chroma, backend, frontend)
docker-compose up -d --build
docker-compose down -v                           # stop + remove volumes
```

## Testing

Backend must be running on port 8001 before tests:

```bash
python test_api.py           # 10 API endpoint tests
python test_complete.py      # 11 tests including E2E workflow
python -m pytest tests/ -v   # unit tests (agents)
```

## Linting & Formatting

```bash
poetry run black src/        # format (88 char lines, py311)
poetry run isort src/        # sort imports (black-compatible profile)
poetry run flake8 src/       # lint
poetry run mypy src/         # type check (strict mode)
```

## Architecture

**Two backend entry points:**
- `src/api/main_simple.py` — Lightweight, in-memory stores, zero external deps. Used in Docker and for rapid testing.
- `src/api/main.py` — Full orchestration with ComplianceOrchestrator, StorageService, async lifespan, background tasks. Requires PostgreSQL, Redis, ChromaDB.

**Request flow:**
```
React (3000) --Axios--> FastAPI (8001) --> Routers --> Services --> Agents/DB
```

**5 CrewAI agents** (`src/agents/`) inherit from `BaseComplianceAgent` which provides structlog logging and tenacity retry (3 attempts, exponential backoff 4-10s):
1. RegulatoryAnalyst — extracts requirements from docs via RAG
2. PolicyMapper — maps policies to regulatory controls
3. EvidenceValidator — validates completeness/accuracy/timeliness
4. RiskScorer — quantifies risk (impact × likelihood × control effectiveness)
5. ExecutiveReporter — generates board-ready summaries

**Services** (`src/services/`):
- `orchestrator.py` — coordinates agent Crew execution, falls back to mock agents on init failure
- `storage_service.py` — file persistence to `./data/`, activity logging
- `document_service.py` — async upload with ThreadPoolExecutor (4 workers), SHA256 hashing
- `rag_service.py` — OpenAI embeddings + ChromaDB, chunking (1000 chars, 200 overlap)

**Frontend** (`frontend/src/`): React 18 + TypeScript, MUI components, TanStack React Query for server state, Recharts for visualizations. 7 pages routed via React Router DOM. API client in `services/api.ts`.

## Key Patterns

- **Pydantic models** for all request/response schemas live in `src/models/schemas.py`
- **Routers** in `src/api/routers/` — one per domain (dashboard, compliance, documents, agents, reports)
- **In-memory stores** in `main_simple.py` use Python dicts/lists (documents_store, compliance_analyses, reports_store, policies_store, risks_store)
- **Background tasks** — compliance analysis runs async via FastAPI BackgroundTasks; client polls status/results endpoints
- **CORS** — backend allows all origins (`["*"]`) in development
- **Config** — `src/core/config.py` uses Pydantic BaseSettings loading from `.env`

## Environment Variables

Required: `DATABASE_URL`, `SECRET_KEY` (for `main.py`). For `main_simple.py`, only `OPENAI_API_KEY` matters (and is optional — agents return mock data without it). See `.env.example` for full list.

## Docker Topology

5 containers on `compliance-network` bridge:
- `compliance-postgres` (5432) — PostgreSQL 15, health-checked via pg_isready
- `compliance-redis` (6379) — Redis 7 with AOF persistence
- `compliance-chroma` (8000) — ChromaDB vector store
- `compliance-backend` (8001) — Python 3.11-slim, runs main_simple.py, depends on postgres healthy
- `compliance-frontend` (3000) — Node 18-alpine, nginx serves React build
