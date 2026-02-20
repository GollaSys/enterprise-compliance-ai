# Enterprise Compliance AI Platform

An AI-powered multi-agent compliance platform for enterprise regulatory compliance management. Built with a FastAPI backend, React + Material-UI frontend, and 5 specialized CrewAI agents that automate regulatory analysis, policy mapping, evidence validation, risk scoring, and executive reporting across GDPR, SOX, FINRA, SEC, HIPAA, and PCI-DSS frameworks.

---

## Features

- **Multi-Agent Compliance System** -- 5 CrewAI agents (Regulatory Analyst, Policy Mapper, Evidence Validator, Risk Scorer, Executive Reporter) work together to automate compliance workflows
- **Regulatory Analysis** -- Automated extraction and interpretation of requirements from GDPR, SOX, FINRA, SEC, HIPAA, and PCI-DSS
- **Policy Mapping** -- Intelligent mapping of internal policies to regulatory controls with gap identification
- **Evidence Validation** -- Automated validation of compliance evidence for completeness, accuracy, and timeliness
- **Risk Scoring** -- Quantitative risk assessment and prioritization with severity levels (critical, high, medium, low)
- **Gap Analysis** -- Identify coverage gaps between your policies and regulatory requirements
- **Executive Reporting** -- Generate board-ready compliance reports with executive summaries and recommendations
- **Interactive Dashboard** -- Real-time compliance metrics, risk distribution charts, trend lines, and activity feeds
- **Agent Orchestration Visualization** -- Visual pipeline showing how 5 CrewAI agents collaborate sequentially, with live demo mode that animates agent execution in real-time, detailed agent cards with tools/backstories, and performance metrics charts
- **Document Management** -- Upload, categorize, and process compliance documents
- **RESTful API** -- 25+ endpoints with Swagger/OpenAPI documentation

---

## Architecture

```
 +---------------------------------------------+
 |              React Frontend                  |
 |  (TypeScript + Material-UI + Recharts)       |
 |         http://localhost:3000                |
 +---------------------+------------------------+
                        |
                   HTTP / REST
                        |
 +---------------------v------------------------+
 |             FastAPI Backend                   |
 |         http://localhost:8001                |
 |         Swagger: /docs                       |
 +------+--------+--------+--------+-----------+
        |        |        |        |
 +------v--+ +---v----+ +-v------+ |
 | Agents  | |Services| | Models | |
 +----+----+ +---+----+ +--------+ |
      |          |                  |
      |    +-----v------+          |
      |    |Orchestrator |          |
      |    +-----+------+          |
      |          |                  |
 +----v----------v------------------v----------+
 |               Data Layer                     |
 |                                              |
 |  +------------+  +--------+  +------------+ |
 |  | PostgreSQL |  | Redis  |  |  ChromaDB  | |
 |  |   :5432    |  | :6379  |  |   :8000    | |
 |  | (Relational|  |(Cache) |  |  (Vector   | |
 |  |   Data)    |  |        |  |   Search)  | |
 |  +------------+  +--------+  +------------+ |
 +---------------------------------------------+

 CrewAI Agents:
 +-------------------+  +----------------+  +--------------------+
 | Regulatory        |  | Policy         |  | Evidence           |
 | Analyst           |  | Mapper         |  | Validator          |
 +-------------------+  +----------------+  +--------------------+
 +-------------------+  +--------------------+
 | Risk              |  | Executive          |
 | Scorer            |  | Reporter           |
 +-------------------+  +--------------------+
```

---

## Tech Stack

| Layer          | Technology                          | Version    |
| -------------- | ----------------------------------- | ---------- |
| Frontend       | React + TypeScript                  | 18.3       |
| UI Components  | Material-UI (MUI)                   | 5.15       |
| Charts         | Recharts, MUI X Charts              | 2.12 / 7.7 |
| HTTP Client    | Axios + TanStack React Query        | 1.7 / 5.45 |
| Routing        | React Router DOM                    | 6.23       |
| Backend        | FastAPI                             | 0.111      |
| ASGI Server    | Uvicorn                             | 0.30       |
| Validation     | Pydantic                            | 2.8        |
| AI Agents      | CrewAI                              | 0.41       |
| LLM Framework  | LangChain + LangChain-OpenAI        | 0.2 / 0.1  |
| Database       | PostgreSQL                          | 15         |
| Cache          | Redis                               | 7          |
| Vector Store   | ChromaDB                            | 0.5+       |
| ORM            | SQLAlchemy + asyncpg                | 2.0 / 0.29 |
| Containerization | Docker + Docker Compose           | --         |
| Language       | Python 3.11+ / TypeScript 4.9       | --         |

---

## Prerequisites

- **Docker and Docker Compose** (for containerized setup)
- **Python 3.11+** (for local development)
- **Node.js 18+** (for local frontend development)
- **npm** (comes with Node.js)
- **OpenAI API Key** (required for AI agent features; the platform runs without it but agent calls will use dummy responses)
- **Anthropic API Key** (optional)

---

## Setup -- Option 1: Docker (Recommended)

This spins up all five services (PostgreSQL, Redis, ChromaDB, backend, frontend) with a single command.

### Step 1: Clone the repository

```bash
git clone <your-repo-url>
cd enterprise-compliance-ai
```

### Step 2: Create the environment file

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### Step 3: Build and start all services

```bash
docker-compose up -d --build
```

This starts the following containers:

| Container              | Image                 | Port  |
| ---------------------- | --------------------- | ----- |
| compliance-postgres    | postgres:15-alpine    | 5432  |
| compliance-redis       | redis:7-alpine        | 6379  |
| compliance-chroma      | chromadb/chroma:latest| 8000  |
| compliance-backend     | (built from Dockerfile.backend) | 8001 |
| compliance-frontend    | (built from frontend/Dockerfile) | 3000 |

### Step 4: Verify containers are running

```bash
docker-compose ps
```

All five containers should show a running/healthy status.

### Step 5: Access the application

- **Frontend Dashboard:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **Swagger API Docs:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health

### Stopping the services

```bash
docker-compose down
```

To also remove persistent volumes (database data, cache, vector store):

```bash
docker-compose down -v
```

---

## Setup -- Option 2: Local Development (Without Docker)

Run the backend and frontend directly on your machine. You still need PostgreSQL, Redis, and ChromaDB available if you want full functionality, but the simplified backend (`main_simple.py`) works standalone with in-memory stores.

### Backend Setup

#### Step 1: Create and activate a virtual environment

```bash
cd enterprise-compliance-ai
python3 -m venv venv
source venv/bin/activate
```

#### Step 2: Install Python dependencies

```bash
pip install -r requirements-minimal.txt
```

#### Step 3: Create the environment file

```bash
cp .env.example .env
```

Edit `.env` with your API keys as needed.

#### Step 4: Start the backend server

```bash
python -m uvicorn src.api.main_simple:app --port 8001
```

The API will be available at http://localhost:8001 with Swagger docs at http://localhost:8001/docs.

### Frontend Setup

Open a new terminal window.

#### Step 1: Navigate to the frontend directory

```bash
cd enterprise-compliance-ai/frontend
```

#### Step 2: Install Node.js dependencies

```bash
npm install --legacy-peer-deps
```

The `--legacy-peer-deps` flag is required to resolve peer dependency conflicts in the current dependency tree.

#### Step 3: Start the development server

```bash
REACT_APP_API_URL=http://localhost:8001 npm start
```

The React app will open at http://localhost:3000.

#### Node.js 23+ Users

If you are running Node.js 23 or later, you need to set an additional environment variable due to OpenSSL compatibility changes:

```bash
NODE_OPTIONS=--openssl-legacy-provider REACT_APP_API_URL=http://localhost:8001 npm start
```

---

## Verifying the Setup

### Quick health check

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "healthy",
  "services": {
    "api": "operational",
    "database": "operational",
    "agents": "operational",
    "vector_store": "operational"
  },
  "timestamp": "2026-02-19T..."
}
```

### Check the root endpoint

```bash
curl http://localhost:8001/
```

### Verify agents are active

```bash
curl http://localhost:8001/api/v1/agents/status
```

This should return the 5 agents (Regulatory Analyst, Policy Mapper, Evidence Validator, Risk Scorer, Executive Reporter) with status "active".

### Open the Swagger docs

Visit http://localhost:8001/docs in your browser to explore and test all API endpoints interactively.

### Open the frontend dashboard

Visit http://localhost:3000 to see the compliance dashboard with metrics, risk charts, and navigation to all platform features.

---

## API Endpoints

All endpoints are prefixed under the backend at `http://localhost:8001`.

### Health and System

| Method | Endpoint        | Description                         |
| ------ | --------------- | ----------------------------------- |
| GET    | `/`             | Platform info and feature list      |
| GET    | `/health`       | Service health status               |

### Dashboard

| Method | Endpoint                        | Description                              |
| ------ | ------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/dashboard/metrics`     | Compliance score, risks, gaps, trends    |
| GET    | `/api/v1/dashboard/activities`  | Recent activity feed                     |

### Documents

| Method | Endpoint                       | Description                              |
| ------ | ------------------------------ | ---------------------------------------- |
| POST   | `/api/v1/documents/upload`     | Upload a document (multipart form)       |
| GET    | `/api/v1/documents`            | List documents (filter by type, status)  |

### Compliance

| Method | Endpoint                                   | Description                          |
| ------ | ------------------------------------------ | ------------------------------------ |
| POST   | `/api/v1/compliance/analyze`               | Run compliance analysis              |
| GET    | `/api/v1/compliance/status/{compliance_id}`| Check analysis status                |
| GET    | `/api/v1/compliance/results/{compliance_id}`| Get full analysis results           |
| GET    | `/api/v1/compliance/regulations`           | List available regulations           |

### Regulations

| Method | Endpoint                | Description                                    |
| ------ | ----------------------- | ---------------------------------------------- |
| GET    | `/api/v1/regulations`   | List all regulations with requirement counts   |

### Policies

| Method | Endpoint              | Description                         |
| ------ | --------------------- | ----------------------------------- |
| GET    | `/api/v1/policies`    | List all policies                   |
| POST   | `/api/v1/policies`    | Create a new policy                 |

### Risks

| Method | Endpoint                | Description                              |
| ------ | ----------------------- | ---------------------------------------- |
| GET    | `/api/v1/risks`         | List risks (filter by level, status)     |
| POST   | `/api/v1/risks/assess`  | Assess risks for given gap IDs           |

### Evidence

| Method | Endpoint                    | Description                          |
| ------ | --------------------------- | ------------------------------------ |
| POST   | `/api/v1/evidence/validate` | Validate evidence against requirements|

### Gap Analysis

| Method | Endpoint               | Description                              |
| ------ | ---------------------- | ---------------------------------------- |
| POST   | `/api/v1/gaps/analyze` | Run gap analysis across regulations      |

### Agents

| Method | Endpoint                                            | Description                                |
| ------ | --------------------------------------------------- | ------------------------------------------ |
| GET    | `/api/v1/agents/status`                             | Get status of all 5 agents                 |
| GET    | `/api/v1/agents/details`                            | Get detailed agent metadata (roles, tools)  |
| GET    | `/api/v1/agents/orchestration`                      | Get pipeline definition with data flow      |
| GET    | `/api/v1/agents/metrics`                            | Get agent performance metrics               |
| POST   | `/api/v1/agents/orchestration/run`                  | Start a simulated orchestration run         |
| GET    | `/api/v1/agents/orchestration/{run_id}/timeline`    | Get step-by-step execution timeline         |
| POST   | `/api/v1/agents/{agent_name}/execute`               | Execute a task on a specific agent          |

### Reports

| Method | Endpoint                        | Description                          |
| ------ | ------------------------------- | ------------------------------------ |
| POST   | `/api/v1/reports/generate`      | Generate a compliance report         |
| GET    | `/api/v1/reports`               | List generated reports               |
| GET    | `/api/v1/reports/{report_id}`   | Get a specific report by ID          |

---

## Testing

The project includes two test scripts that validate all API endpoints. The backend must be running before you execute them.

### Start the backend (if not already running)

```bash
source venv/bin/activate
python -m uvicorn src.api.main_simple:app --port 8001
```

### Run the API test suite (10 tests)

```bash
python test_api.py
```

This runs 10 test functions covering: health, dashboard, compliance analysis, documents, agents, reports, policies, risks, evidence validation, and gap analysis.

### Run the complete test suite (11 tests)

```bash
python test_complete.py
```

This runs 11 tests in a class-based suite that additionally includes a full end-to-end workflow test (upload document, run analysis, assess risks, validate evidence, generate report).

### Unit tests

```bash
python -m pytest tests/ -v
```

The `tests/` directory contains `test_agents.py` for agent-specific unit tests.

---

## Project Structure

```
enterprise-compliance-ai/
|-- docker-compose.yml          # All 5 services (postgres, redis, chroma, backend, frontend)
|-- Dockerfile.backend          # Backend image (python:3.11-slim + requirements-minimal.txt)
|-- requirements-minimal.txt    # Minimal Python deps (FastAPI, uvicorn, pydantic, etc.)
|-- requirements.txt            # Full Python deps (includes CrewAI, LangChain, SQLAlchemy, etc.)
|-- requirements-simple.txt     # Simplified dependency list
|-- pyproject.toml              # Poetry configuration and dev dependencies
|-- Makefile                    # Build/dev/test shortcuts
|-- .env.example                # Template for environment variables
|-- .gitignore                  # Git ignore rules
|-- .dockerignore               # Docker build ignore rules
|-- test_api.py                 # API test suite (10 tests)
|-- test_complete.py            # Complete test suite (11 tests)
|-- run_local.sh                # Local development startup script
|-- verify.sh                   # Verification script
|-- docker-test.sh              # Docker-based test runner
|
|-- src/
|   |-- __init__.py
|   |-- api/
|   |   |-- __init__.py
|   |   |-- main.py             # Full API entrypoint (with DB connections)
|   |   |-- main_simple.py      # Simplified API entrypoint (in-memory stores)
|   |   |-- routers/
|   |       |-- __init__.py
|   |       |-- agents.py       # Agent status and execution routes
|   |       |-- compliance.py   # Compliance analysis routes
|   |       |-- dashboard.py    # Dashboard metrics and activities routes
|   |       |-- documents.py    # Document upload and listing routes
|   |       |-- reports.py      # Report generation and retrieval routes
|   |
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- base_agent.py          # Base agent class
|   |   |-- regulatory_analyst.py  # Regulatory Analyst agent
|   |   |-- policy_mapper.py       # Policy Mapper agent
|   |   |-- evidence_validator.py  # Evidence Validator agent
|   |   |-- risk_scorer.py         # Risk Scorer agent
|   |   |-- executive_reporter.py  # Executive Reporter agent
|   |
|   |-- core/
|   |   |-- __init__.py
|   |   |-- config.py          # Application configuration
|   |   |-- database.py        # Database connection setup
|   |
|   |-- models/
|   |   |-- __init__.py
|   |   |-- schemas.py         # Pydantic data models
|   |
|   |-- services/
|       |-- __init__.py
|       |-- document_service.py   # Document processing logic
|       |-- orchestrator.py       # Agent orchestration service
|       |-- rag_service.py        # RAG (Retrieval-Augmented Generation) service
|       |-- storage_service.py    # File storage service
|
|-- frontend/
|   |-- Dockerfile              # Frontend image (node:18-alpine)
|   |-- package.json            # Node.js dependencies
|   |-- tsconfig.json           # TypeScript configuration
|   |-- public/
|   |   |-- index.html          # HTML entry point
|   |   |-- manifest.json       # Web app manifest
|   |-- src/
|       |-- index.tsx           # React entry point
|       |-- index.css           # Global styles
|       |-- App.tsx             # App root with routing
|       |-- components/
|       |   |-- Layout.tsx      # Sidebar navigation layout
|       |-- pages/
|       |   |-- Dashboard.tsx   # Dashboard with metrics and charts
|       |   |-- Compliance.tsx  # Compliance analysis interface
|       |   |-- Documents.tsx   # Document upload and management
|       |   |-- Policies.tsx    # Policy management
|       |   |-- Reports.tsx     # Report generation
|       |   |-- Agents.tsx      # Agent orchestration visualization
|       |   |-- Risks.tsx       # Risk assessment view
|       |   |-- Settings.tsx    # Platform settings
|       |-- services/
|           |-- api.ts          # Axios API client configuration
|
|-- tests/
|   |-- __init__.py
|   |-- test_agents.py         # Agent unit tests
|
|-- data/                       # Runtime data directory (documents, policies, reports, metadata)
```

---

## Configuration / Environment Variables

Copy `.env.example` to `.env` and fill in your values. The table below lists all supported variables:

| Variable                      | Description                            | Default / Example                                             |
| ----------------------------- | -------------------------------------- | ------------------------------------------------------------- |
| `OPENAI_API_KEY`              | OpenAI API key for LLM calls           | (required for AI features)                                    |
| `ANTHROPIC_API_KEY`           | Anthropic API key (optional)           | (optional)                                                    |
| `DATABASE_URL`                | PostgreSQL connection string           | `postgresql+asyncpg://user:password@localhost:5432/compliance_db` |
| `REDIS_URL`                   | Redis connection string                | `redis://localhost:6379/0`                                    |
| `CHROMA_HOST`                 | ChromaDB server hostname               | `localhost`                                                   |
| `CHROMA_PORT`                 | ChromaDB server port                   | `8000`                                                        |
| `CHROMA_COLLECTION`           | ChromaDB collection name               | `compliance_docs`                                             |
| `SECRET_KEY`                  | JWT signing key                        | `your-secret-key-here-change-in-production`                   |
| `ALGORITHM`                   | JWT algorithm                          | `HS256`                                                       |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration (minutes)         | `30`                                                          |
| `APP_ENV`                     | Environment (development/production)   | `development`                                                 |
| `APP_PORT`                    | Application port                       | `8000`                                                        |
| `APP_HOST`                    | Application bind host                  | `0.0.0.0`                                                     |
| `LOG_LEVEL`                   | Logging level                          | `INFO`                                                        |
| `FRONTEND_URL`                | Frontend URL (for CORS)                | `http://localhost:3000`                                       |
| `REACT_APP_API_URL`           | Backend URL (used by React frontend)   | `http://localhost:8001`                                       |
| `AWS_REGION`                  | AWS region (production)                | `us-east-1`                                                   |
| `AWS_ACCESS_KEY_ID`           | AWS access key (production)            | (optional)                                                    |
| `AWS_SECRET_ACCESS_KEY`       | AWS secret key (production)            | (optional)                                                    |
| `PROMETHEUS_PORT`             | Prometheus metrics port                | `9090`                                                        |
| `JAEGER_HOST`                 | Jaeger tracing host                    | `localhost`                                                   |
| `JAEGER_PORT`                 | Jaeger tracing port                    | `6831`                                                        |

**Docker Compose note:** When running via `docker-compose`, database URLs are overridden in `docker-compose.yml` to use container hostnames (e.g., `postgres`, `redis`, `chroma`) instead of `localhost`.

---

## Troubleshooting

### Backend won't start: "ModuleNotFoundError"

Make sure you activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate
pip install -r requirements-minimal.txt
```

### Frontend: "error:0308010C:digital envelope routines::unsupported"

This happens on Node.js 23+ due to OpenSSL changes. Set the legacy provider flag:

```bash
NODE_OPTIONS=--openssl-legacy-provider REACT_APP_API_URL=http://localhost:8001 npm start
```

### Frontend: npm install fails with peer dependency errors

Use the `--legacy-peer-deps` flag:

```bash
npm install --legacy-peer-deps
```

### Docker: "port is already allocated"

Another process is using port 5432, 6379, 8000, 8001, or 3000. Either stop the conflicting process or change the port mapping in `docker-compose.yml`:

```bash
# Find what's using a port (example: 5432)
lsof -i :5432
```

### Docker: backend container keeps restarting

Check the logs:

```bash
docker-compose logs backend
```

The backend depends on PostgreSQL being healthy. If Postgres hasn't finished initializing, the backend will retry. Wait 30-40 seconds for the health check start period to pass.

### "Cannot connect to API" when running tests

The backend must be running on port 8001 before executing `test_api.py` or `test_complete.py`:

```bash
# Start backend first
python -m uvicorn src.api.main_simple:app --port 8001

# In another terminal, run tests
python test_api.py
```

### CORS errors in the browser

The backend allows all origins by default (`allow_origins=["*"]`). If you see CORS errors, ensure `REACT_APP_API_URL` points to the correct backend URL (http://localhost:8001) and the backend is actually running.

### ChromaDB connection refused

If running locally without Docker, ChromaDB must be started separately. The simplified backend (`main_simple.py`) does not require ChromaDB -- it uses in-memory stores. ChromaDB is only needed when using the full backend (`main.py`) with vector search features.

### Docker: rebuilding after code changes

If you change backend or frontend code, rebuild the images:

```bash
docker-compose up -d --build
```

For the backend, source code is volume-mounted (`./src:/app/src`), so Python file changes are reflected without rebuilding. Frontend changes require a rebuild since the Dockerfile copies the full source.
