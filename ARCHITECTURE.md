# Architecture & Design Document

**Enterprise Compliance AI Platform**
**Version:** 1.0.0
**Last Updated:** 2026-02-19

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [System Context Diagram](#2-system-context-diagram)
3. [Component Architecture](#3-component-architecture)
4. [Low-Level Design](#4-low-level-design)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Technology Stack](#6-technology-stack)
7. [Deployment Architecture](#7-deployment-architecture)
8. [Security Architecture](#8-security-architecture)
9. [Non-Functional Requirements](#9-non-functional-requirements)

---

## 1. High-Level Architecture

The Enterprise Compliance AI Platform is a multi-agent AI system that automates regulatory compliance analysis for financial services organizations. It combines five specialized CrewAI agents -- Regulatory Analyst, Policy Mapper, Evidence Validator, Risk Scorer, and Executive Reporter -- with a FastAPI backend, React frontend, and a RAG (Retrieval-Augmented Generation) pipeline backed by ChromaDB. The platform ingests regulatory documents, maps them against organizational policies, validates operational evidence, quantifies risk, and produces board-ready executive reports. Two API entry points exist: a lightweight in-memory version (`main_simple.py`) for rapid development and testing, and a full orchestrated version (`main.py`) that delegates to the `ComplianceOrchestrator`, `StorageService`, and all five agents via CrewAI `Crew` execution.

```
+-----------------------------------------------------------------------------------+
|                              PRESENTATION LAYER                                   |
|                                                                                   |
|   +-----------------------------------------------------------------------+       |
|   |                    React 18 + TypeScript Frontend                     |       |
|   |  +----------+ +------------+ +-----------+ +--------+ +-----------+  |       |
|   |  | Dashboard | | Compliance | | Documents | | Risks  | |  Reports  |  |       |
|   |  +----------+ +------------+ +-----------+ +--------+ +-----------+  |       |
|   |  | Policies | | Settings   |   MUI  |  Recharts  | TanStack Query |  |       |
|   |  +----------+ +------------+---------+------------+----------------+  |       |
|   +-----------------------------------------------------------------------+       |
|                              | Axios HTTP (port 3000 -> 8001)                     |
+-----------------------------------------------------------------------------------+
                               |
+-----------------------------------------------------------------------------------+
|                                API LAYER                                          |
|                                                                                   |
|   +-----------------------------------------------------------------------+       |
|   |                     FastAPI Application (port 8001)                    |       |
|   |                                                                       |       |
|   |   main_simple.py (lightweight, in-memory)                             |       |
|   |   main.py (full orchestration, lifespan events)                       |       |
|   |                                                                       |       |
|   |   Routers:                                                            |       |
|   |   /api/v1/dashboard/*  /api/v1/compliance/*  /api/v1/documents/*      |       |
|   |   /api/v1/policies/*   /api/v1/risks/*       /api/v1/reports/*        |       |
|   |   /api/v1/agents/*     /api/v1/evidence/*    /api/v1/gaps/*           |       |
|   |   /api/v1/regulations  /health               /                        |       |
|   |                                                                       |       |
|   |   Middleware: CORS | Pydantic Validation | Background Tasks           |       |
|   +-----------------------------------------------------------------------+       |
|                              |                                                    |
+-----------------------------------------------------------------------------------+
                               |
+-----------------------------------------------------------------------------------+
|                              SERVICE LAYER                                        |
|                                                                                   |
|   +---------------------+  +-------------------+  +------------------+            |
|   | ComplianceOrchestrator|  | StorageService   |  | DocumentService  |            |
|   | - Agent coordination |  | - File persistence|  | - Async upload   |            |
|   | - Job management     |  | - Activity logging|  | - SHA256 hashing |            |
|   | - Mock fallback      |  | - Metadata JSON   |  | - ThreadPool I/O |            |
|   +---------------------+  +-------------------+  +------------------+            |
|                                                                                   |
|   +-----------------------------------------------------------------------+       |
|   |                          RAGService                                   |       |
|   |   OpenAI Embeddings -> ChromaDB Vector Store -> Semantic Search       |       |
|   |   Document Chunking (1000 chars, 200 overlap) | Entity Extraction     |       |
|   +-----------------------------------------------------------------------+       |
|                              |                                                    |
+-----------------------------------------------------------------------------------+
                               |
+-----------------------------------------------------------------------------------+
|                             AGENT LAYER (CrewAI)                                  |
|                                                                                   |
|   +------------------+  +----------------+  +---------------------+               |
|   | Regulatory       |  | Policy         |  | Evidence            |               |
|   | Analyst          |  | Mapper         |  | Validator           |               |
|   | - Extract reqs   |  | - Map policies |  | - Validate evidence |               |
|   | - Search regs    |  | - Find gaps    |  | - Quality scoring   |               |
|   | - Analyze changes|  | - Recommend    |  | - Timeliness check  |               |
|   +------------------+  +----------------+  | - Chain of custody  |               |
|                                             +---------------------+               |
|   +------------------+  +---------------------+                                   |
|   | Risk Scorer      |  | Executive Reporter  |                                  |
|   | - Score risks    |  | - Exec summaries    |                                  |
|   | - Impact assess  |  | - Dashboard metrics |                                  |
|   | - Risk matrix    |  | - Board presentation|                                  |
|   | - Prioritize     |  | - Trend analysis    |                                  |
|   +------------------+  +---------------------+                                   |
|                                                                                   |
|   All agents extend BaseComplianceAgent (abstract)                                |
|   Retry: tenacity (3 attempts, exponential backoff 4-10s)                         |
|   Logging: structlog with agent binding                                           |
+-----------------------------------------------------------------------------------+
                               |
+-----------------------------------------------------------------------------------+
|                              DATA LAYER                                           |
|                                                                                   |
|   +------------------+  +------------------+  +------------------+                |
|   | PostgreSQL 15    |  | Redis 7          |  | ChromaDB         |                |
|   | - Analyses       |  | - Session cache  |  | - Embeddings     |                |
|   | - Documents      |  | - Rate limiting  |  | - Semantic search|                |
|   | - Policies       |  | - Pub/Sub        |  | - Document chunks|                |
|   | - Risks          |  | - AOF persistence|  |                  |                |
|   | - Reports        |  |                  |  |                  |                |
|   | Pool: 10+20      |  |                  |  |                  |                |
|   +------------------+  +------------------+  +------------------+                |
|                                                                                   |
|   +-----------------------------------------------------------------------+       |
|   | File System: ./data/documents  ./data/policies  ./data/reports        |       |
|   |              ./data/metadata/storage.json                             |       |
|   +-----------------------------------------------------------------------+       |
+-----------------------------------------------------------------------------------+
```

### Component Summary

| Layer | Component | Purpose |
|-------|-----------|---------|
| Presentation | React 18 + TypeScript | SPA with 7 pages, MUI design system, Recharts visualizations |
| API | FastAPI (main_simple.py) | Lightweight entry point, 20+ endpoints, in-memory storage |
| API | FastAPI (main.py) | Full version with orchestrator, storage service, lifespan events |
| API | Routers (5 modules) | agents, compliance, dashboard, documents, reports |
| Service | ComplianceOrchestrator | Coordinates all 5 agents, manages analysis jobs, CrewAI Crew execution |
| Service | StorageService | File-based persistence, activity logging (max 1000), metadata JSON |
| Service | DocumentService | Async file upload, SHA256 hashing, ThreadPoolExecutor (4 workers) |
| Service | RAGService | OpenAI embeddings, ChromaDB vector store, document chunking, entity extraction |
| Agent | RegulatoryAnalystAgent | Extracts requirements from SEC, FINRA, SOX, GDPR documents |
| Agent | PolicyMapperAgent | Maps policies to regulations, identifies gaps, generates recommendations |
| Agent | EvidenceValidatorAgent | Validates evidence completeness, quality, timeliness (90-day max), chain of custody |
| Agent | RiskScorerAgent | Calculates risk scores (impact x likelihood x control effectiveness), regulation-specific penalties |
| Agent | ExecutiveReporterAgent | Generates executive summaries, dashboard metrics, 6-slide board presentations, trend analysis |
| Data | PostgreSQL 15 | 5 tables (compliance_analyses, documents, policies, risks, reports), UUID PKs, JSON columns |
| Data | Redis 7 | Session caching, rate limiting, pub/sub messaging |
| Data | ChromaDB | Vector store for document embeddings, semantic similarity search |
| Data | File System | Document storage, policy files, generated reports, JSON metadata |

---

## 2. System Context Diagram

```
                        +---------------------------+
                        |    Compliance Officer /    |
                        |    Board Member / Auditor  |
                        |       (End Users)          |
                        +-------------+-------------+
                                      |
                                      | HTTPS (port 3000)
                                      |
                        +-------------v-------------+
                        |                           |
                        |    React Frontend SPA     |
                        |    (Browser Client)       |
                        |                           |
                        +-------------+-------------+
                                      |
                                      | REST API (port 8001)
                                      |
+------------------+    +-------------v-------------+    +---------------------+
|                  |    |                           |    |                     |
| Regulatory       |    |   Enterprise Compliance   |    |   OpenAI API        |
| Databases        |<-->|   AI Platform             |<-->|   (LLM Provider)    |
| (SEC, FINRA,     |    |                           |    |   - GPT-4           |
|  SOX filings)    |    |   - 5 CrewAI Agents       |    |   - Embeddings      |
|                  |    |   - RAG Pipeline          |    |   (text-embedding-  |
+------------------+    |   - Risk Engine           |    |    ada-002)         |
                        |   - Report Generator      |    |                     |
                        +---+--------+----------+---+    +---------------------+
                            |        |          |
              +-------------+   +----+----+   +-+------------------+
              |                 |         |   |                    |
    +---------v--------+  +----v----+ +---v--------+  +-----------v-+
    |   PostgreSQL 15  |  | Redis 7 | | ChromaDB   |  | File System |
    |   (Relational)   |  | (Cache) | | (Vectors)  |  | (Documents) |
    +------------------+  +---------+ +------------+  +-------------+
```

### External Actors

| Actor | Description | Interaction |
|-------|-------------|-------------|
| Compliance Officer | Primary user; uploads documents, runs analyses, reviews gaps | Full CRUD via React UI |
| Board Member | Consumer of executive reports and dashboards | Read-only dashboard and report views |
| Auditor | Validates evidence and reviews compliance status | Evidence validation, compliance results |
| OpenAI API | LLM provider for agent reasoning and document embeddings | API calls from CrewAI agents and RAGService |
| Regulatory Databases | External sources for SEC, FINRA, SOX, GDPR regulation texts | Ingested as documents, searched via RAG |

### System Boundary

The system boundary encompasses the FastAPI backend, all five CrewAI agents, the service layer (orchestrator, storage, document, RAG), and the three data stores (PostgreSQL, Redis, ChromaDB). The React frontend and external LLM providers sit outside the core system boundary but interact through well-defined interfaces (REST API and OpenAI SDK respectively).

---

## 3. Component Architecture

### 3.1 Frontend Layer

**Technology:** React 18.3.1 + TypeScript 4.9 + Create React App

**Pages (7):**

| Page | Route | Purpose | Key Features |
|------|-------|---------|--------------|
| Dashboard | `/dashboard` | Overview of compliance health | KPI cards, compliance trend line chart, risk distribution pie chart, recent activities feed |
| Compliance | `/compliance` | Run and review compliance analyses | Regulation selector, analysis trigger, results table with gap/risk details |
| Documents | `/documents` | Upload and manage regulatory documents | Drag-and-drop upload (React Dropzone), document list with type/status filters |
| Policies | `/policies` | Manage organizational policies | Policy CRUD, version tracking, coverage mapping |
| Risks | `/risks` | Risk register and assessment | Risk table with level/status filters, risk scoring details |
| Reports | `/reports` | Generate and view reports | Report type selector (executive/technical/audit), period picker, PDF generation |
| Settings | `/settings` | Platform configuration | Agent configuration, notification preferences, system settings |

**Architecture:**
```
frontend/src/
  |-- App.tsx                    # Root: Router, Theme, QueryClient, SnackbarProvider
  |-- index.tsx                  # Entry point
  |-- components/
  |     +-- Layout.tsx           # Persistent sidebar (280px), AppBar, navigation
  |-- pages/
  |     +-- Dashboard.tsx        # Metrics cards + Recharts visualizations
  |     +-- Compliance.tsx       # Analysis workflow
  |     +-- Documents.tsx        # Document management
  |     +-- Policies.tsx         # Policy management
  |     +-- Risks.tsx            # Risk register
  |     +-- Reports.tsx          # Report generation
  |     +-- Settings.tsx         # Configuration
  +-- services/
        +-- api.ts               # Axios instance + API modules (dashboard, compliance,
                                 #   documents, agents, reports)
```

**Key Libraries:**

| Library | Version | Purpose |
|---------|---------|---------|
| @mui/material | 5.15.20 | Component library (Cards, Tables, Buttons, Drawers, AppBar) |
| @mui/icons-material | 5.15.20 | Icon set for navigation and UI elements |
| @mui/x-charts | 7.7.0 | Advanced charting components |
| @mui/x-data-grid | 7.7.0 | Data grid for tabular displays |
| @tanstack/react-query | 5.45.1 | Server state management, caching, refetch |
| recharts | 2.12.7 | Charts (LineChart, PieChart, BarChart) for dashboard |
| axios | 1.7.2 | HTTP client with base URL configuration |
| react-router-dom | 6.23.1 | Client-side routing with 8 routes |
| react-dropzone | 14.2.3 | File upload with drag-and-drop |
| react-hook-form | 7.52.0 | Form state management and validation |
| notistack | 3.0.1 | Toast notifications (max 3 stacked, top-right) |
| date-fns | 3.6.0 | Date formatting and manipulation |

**State Management:**
- Server state: TanStack React Query (`refetchOnWindowFocus: false`, `retry: 1`)
- UI state: React `useState` hooks (sidebar open/close, menu anchors)
- No global client state store (no Redux/Zustand needed)

**Theme:**
- Primary: `#1976d2` (blue)
- Secondary: `#dc004e` (red)
- Font: Inter, Roboto fallback
- Border radius: 12px (global), 16px (cards/paper), 8px (buttons)

### 3.2 API Layer (FastAPI)

The API layer provides two entry points that share the same endpoint structure:

**Entry Point 1: `src/api/main_simple.py` (Lightweight)**
- Self-contained, no external service dependencies
- In-memory Python dicts/lists for all data storage
- Synchronous response (no background tasks for analysis)
- Pre-seeded risk data for immediate testing
- Used in Docker production via `Dockerfile.backend`

**Entry Point 2: `src/api/main.py` (Full Orchestration)**
- Uses `asynccontextmanager` lifespan for startup/shutdown
- Initializes `StorageService` and `ComplianceOrchestrator` at startup
- Background task execution via `FastAPI.BackgroundTasks`
- Pydantic response models for type-safe serialization
- Delegates to orchestrator and storage service for all operations

**Router Modules (`src/api/routers/`):**

| Router | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| dashboard.py | /api/v1/dashboard | GET /metrics, GET /activities, GET /alerts | Real-time metrics and activity feed |
| compliance.py | /api/v1/compliance | POST /analyze, GET /status/{id}, POST /gaps/analyze, POST /evidence/validate, POST /risks/assess, GET /regulations, GET /policies | Full compliance workflow |
| documents.py | /api/v1/documents | POST /upload, GET / | Document upload and listing |
| reports.py | /api/v1/reports | POST /generate, GET /, GET /{id} | Report generation and retrieval |
| agents.py | /api/v1/agents | GET /status, POST /{name}/execute | Agent management and task execution |

**Middleware Stack:**
```
Request -> CORS Middleware -> Route Handler -> Pydantic Validation -> Response
             |
             +-- allow_origins: ["*"] (dev) / ["http://localhost:3000", "http://localhost:3001"] (prod)
             +-- allow_credentials: True
             +-- allow_methods: ["*"]
             +-- allow_headers: ["*"]
```

### 3.3 Agent Layer (CrewAI)

All five agents inherit from `BaseComplianceAgent`, which wraps a CrewAI `Agent` with structured logging (structlog), retry logic (tenacity), and tool management.

**Agent 1: RegulatoryAnalystAgent**
- **Role:** Senior Regulatory Compliance Analyst
- **Dependencies:** DocumentService, RAGService
- **Tools:**
  - `extract_regulatory_requirements` -- Extracts requirements, obligations, controls, deadlines from document text via RAGService entity extraction
  - `search_regulations` -- Semantic search across regulation corpus with optional regulation_type filter, returns top 10 results
  - `analyze_regulatory_changes` -- Compares current vs previous document versions, identifies new/modified/removed requirements
- **Regulatory Coverage:** SEC, FINRA, SOX, GDPR

**Agent 2: PolicyMapperAgent**
- **Role:** Policy Compliance Mapping Specialist
- **Dependencies:** RAGService
- **Tools:**
  - `map_policy_to_regulation` -- Generates OpenAI embeddings for policy and regulation content, computes cosine similarity, maps policies with score > 0.7
  - `identify_policy_gaps` -- Iterates all regulations, checks coverage (>= 0.8 = covered, >= 0.5 = partial, < 0.5 = uncovered), returns sorted by remediation priority
  - `generate_policy_recommendations` -- Produces "new_policy" or "policy_update" recommendations based on gap type, with effort estimates
- **Scoring:** Coverage score derived from average similarity of mapped regulations; gap risk assessed by max_fine thresholds ($1M = high, $100K = medium)

**Agent 3: EvidenceValidatorAgent**
- **Role:** Compliance Evidence Validation Expert
- **Dependencies:** None (standalone)
- **Tools:**
  - `validate_evidence` -- Validates evidence against requirement list, checks required fields, determines compliant/partially_compliant/non_compliant status
  - `assess_evidence_quality` -- Weighted scoring: completeness (30%), accuracy (30%), consistency (20%), timeliness (20%); thresholds: >= 0.9 excellent, >= 0.7 good, >= 0.5 acceptable
  - `check_evidence_timeliness` -- 90-day maximum age; computes expiry date; marks requires_update if exceeded
  - `verify_evidence_chain` -- Validates chain of custody elements (actor + timestamp), integrity via hash verification, signature validation, audit trail completeness
- **Required Evidence Fields:** id, type, timestamp, source, content, hash

**Agent 4: RiskScorerAgent**
- **Role:** Compliance Risk Assessment Specialist
- **Dependencies:** None (standalone)
- **Tools:**
  - `calculate_risk_score` -- Formula: `impact * likelihood * (1 - control_effectiveness)`, with adjustments for regulatory severity (1.5x) and business criticality (1.3x), capped at 10.0
  - `assess_impact` -- Four dimensions: financial (fines, revenue loss, remediation cost), operational (disruption, availability, productivity), reputational (trust, perception, standing), legal (litigation, regulatory action, criminal liability)
  - `evaluate_likelihood` -- Factors: occurrence probability (base 0.3, +0.2 external exposure, +0.3 low control maturity), detection probability (0.7 with monitoring, 0.3 without), exploitation probability
  - `generate_risk_matrix` -- Distributes risks across critical/high/medium/low/minimal, generates heat map, identifies top 10 risks, computes aggregate metrics
  - `prioritize_remediation` -- Scores by adjusted risk (2x for immediate urgency), assigns timeline (critical=30d, high=60d, low=90d), estimates resources (hours, team_size, budget)
- **Regulation-Specific Penalties:** GDPR: $20M, SOX: $5M
- **Risk Levels:** >= 8 CRITICAL, >= 6 HIGH, >= 4 MEDIUM, >= 2 LOW, < 2 MINIMAL

**Agent 5: ExecutiveReporterAgent**
- **Role:** Executive Compliance Reporting Specialist
- **Dependencies:** None (standalone)
- **Tools:**
  - `generate_executive_summary` -- Produces report with compliance status (Excellent/Good/Acceptable/Needs Improvement/Critical based on rate), key findings, critical risks, achievements, recommendations, next steps
  - `create_dashboard_metrics` -- Four metric categories: KPIs (compliance rate, gap count, risk count, remediation completion, audit readiness, control effectiveness), trends (compliance, risk, gap closure, new regs), financial (fines avoided, investment, ROI, cost per control), operational (evidence collection, policy coverage, training, incident response)
  - `prepare_board_presentation` -- 6-slide structure: (1) Executive Summary, (2) Compliance Dashboard, (3) Risk Heat Map, (4) Remediation Progress, (5) Resource Requirements, (6) Strategic Recommendations
  - `generate_trend_analysis` -- Compliance trends, risk trends, regulatory change trends, quarterly forecasts with confidence level and assumptions

### 3.4 Service Layer

**ComplianceOrchestrator (`src/services/orchestrator.py`)**
- Central coordinator for all agent interactions
- Manages in-memory analysis jobs (`self.analyses: Dict`) and reports (`self.reports: Dict`)
- Initialization flow: creates RAGService -> DocumentService -> all 5 agents
- Falls back to mock agents (simple dicts) if real agent initialization fails
- Creates CrewAI `Crew` with 4 agents (regulatory_analyst, policy_mapper, evidence_validator, risk_scorer) for analysis execution
- Analysis lifecycle: created (10%) -> processing (50%) -> validating (75%) -> completed (100%) / failed (0%)
- Provides mock data for all operations when agents are in mock mode

**StorageService (`src/services/storage_service.py`)**
- File-based persistence under `./data/` directory
- Directory structure: `documents/`, `policies/`, `reports/`, `metadata/`
- Metadata stored as JSON in `./data/metadata/storage.json`
- Activity log capped at 1000 entries (saves most recent 100 to disk)
- Async file I/O via `aiofiles`
- ID generation: `DOC-{uuid8}`, `POL-{uuid8}`
- Supports filtering by type and status on all list operations

**DocumentService (`src/services/document_service.py`)**
- Async document upload with `ThreadPoolExecutor` (4 workers) for file I/O
- SHA256 content hashing for integrity verification
- Document ID: `{timestamp}_{md5(filename)[:8]}`
- Per-document metadata stored as individual JSON files in `metadata/` subdirectory
- Status lifecycle: `pending_processing` -> `processed` / `failed`
- Supports search, stats, status updates, and deletion

**RAGService (`src/services/rag_service.py`)**
- Embedding model: OpenAI `text-embedding-ada-002` via `langchain_openai.OpenAIEmbeddings`
- Vector store: ChromaDB (HTTP client mode, default host localhost:8000)
- Document chunking: `RecursiveCharacterTextSplitter` with chunk_size=1000, overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
- Semantic search: `similarity_search_with_score`, returns content + metadata + score + source
- Entity extraction: Pattern-based detection for requirements ("shall", "must", "required", "mandatory"), obligations ("obligated", "responsible", "duty", "liable"), controls ("control", "measure", "safeguard", "protection"), deadlines ("by", "before", "within", "no later than")
- CRUD: ingest, search, update (delete + re-ingest), delete
- Collection stats: document count, embedding model name, chunk size

### 3.5 Data Layer

**PostgreSQL 15 (Relational Data)**
- Async driver: `asyncpg` via SQLAlchemy `create_async_engine`
- Connection pool: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`
- ORM: SQLAlchemy declarative base with 5 tables
- All primary keys: UUID strings (`str(uuid.uuid4())`)
- All tables include JSON columns for flexible metadata storage
- Schema initialization: `Base.metadata.create_all` via `init_db()`

**Redis 7 (Caching & Messaging)**
- AOF persistence enabled (`--appendonly yes`)
- URL configured via `REDIS_URL` environment variable (default: `redis://localhost:6379/0`)
- Used for: session caching, rate limiting, pub/sub event distribution

**ChromaDB (Vector Store)**
- HTTP server mode on port 8000
- Collection: `compliance_docs` with description metadata
- Telemetry disabled (`ANONYMIZED_TELEMETRY=false`)
- Stores document chunk embeddings with metadata (doc_id, doc_type, chunk_index, total_chunks)

**File System (Document Storage)**
- Base path: `./data/`
- Subdirectories: `documents/`, `policies/`, `reports/`, `metadata/`
- Metadata persistence: `./data/metadata/storage.json` (JSON format)
- Individual document metadata: `./data/documents/metadata/{doc_id}.json`

---

## 4. Low-Level Design

### 4.1 Agent Design

**Base Agent Class Diagram:**

```
+---------------------------------------------------------------+
|                  BaseComplianceAgent (ABC)                     |
+---------------------------------------------------------------+
| - name: str                                                   |
| - role: str                                                   |
| - goal: str                                                   |
| - backstory: str                                              |
| - tools: List[Tool]                                           |
| - verbose: bool = True                                        |
| - max_iter: int = 10                                          |
| - memory: bool = True                                         |
| - agent: crewai.Agent                                         |
| - logger: structlog.BoundLogger                               |
+---------------------------------------------------------------+
| + __init__(name, role, goal, backstory, tools, verbose,       |
|            max_iter, memory)                                   |
| - _create_agent() -> Agent                                    |
|     [allow_delegation=False]                                  |
| + {abstract} create_task(**kwargs) -> Task                    |
| + @retry(stop=3, wait=exp(1, min=4, max=10))                 |
|   execute(task: Task) -> Any                                  |
| + add_tool(tool: Tool) -> None                                |
| + get_metrics() -> Dict[str, Any]                             |
+---------------------------------------------------------------+
          ^            ^            ^           ^          ^
          |            |            |           |          |
+---------+--+ +------+-----+ +----+------+ +--+------+ ++-----------+
|Regulatory  | |Policy      | |Evidence   | |Risk     | |Executive   |
|Analyst     | |Mapper      | |Validator  | |Scorer   | |Reporter    |
|Agent       | |Agent       | |Agent      | |Agent    | |Agent       |
+------------+ +------------+ +-----------+ +---------+ +------------+
| deps:      | | deps:      | | deps:     | | deps:   | | deps:      |
| DocService | | RAGService | | (none)    | | (none)  | | (none)     |
| RAGService | |            | |           | |         | |            |
+------------+ +------------+ +-----------+ +---------+ +------------+
| Tools: 3   | | Tools: 3   | | Tools: 4  | | Tools: 5| | Tools: 4   |
+------------+ +------------+ +-----------+ +---------+ +------------+
```

**Agent Tool Registry:**

| Agent | Tool Name | Input | Output |
|-------|-----------|-------|--------|
| RegulatoryAnalyst | extract_regulatory_requirements | document_content: str | Dict with requirements, obligations, controls, deadlines, citations lists |
| RegulatoryAnalyst | search_regulations | query: str, regulation_types: List[str] | List[Dict] with content, source, relevance_score, metadata |
| RegulatoryAnalyst | analyze_regulatory_changes | current_doc: str, previous_doc: str | Dict with new/modified/removed requirements, impact_assessment, compliance_gaps |
| PolicyMapper | map_policy_to_regulation | policy: Dict, regulations: List[Dict] | Dict with policy_id, mapped_regulations (score>0.7), coverage_score, gaps, strengths |
| PolicyMapper | identify_policy_gaps | policies: List[Dict], regulations: List[Dict] | List[Dict] sorted by priority with regulation, gap_type (uncovered/partial), risk_level |
| PolicyMapper | generate_policy_recommendations | gaps: List[Dict], existing_policies: List[Dict] | List[Dict] with type (new_policy/policy_update), priority, effort estimate |
| EvidenceValidator | validate_evidence | evidence: Dict, requirements: List[Dict] | Dict with validation_status, compliance_mappings, issues, recommendations |
| EvidenceValidator | assess_evidence_quality | evidence: Dict | Dict with completeness/accuracy/consistency/timeliness scores, overall_quality |
| EvidenceValidator | check_evidence_timeliness | evidence: Dict, max_age_days: int=90 | Dict with is_current, age_days, expiry_date, requires_update |
| EvidenceValidator | verify_evidence_chain | evidence: Dict | Dict with has_valid_chain, chain_elements, integrity_status, signatures_valid |
| RiskScorer | calculate_risk_score | gap: Dict, context: Dict | Dict with base/adjusted risk scores, risk_level, risk_factors, mitigation_urgency |
| RiskScorer | assess_impact | gap: Dict | Dict with financial/operational/reputational/legal impact categories |
| RiskScorer | evaluate_likelihood | gap: Dict, historical_data: Dict | Dict with occurrence/detection/exploitation probabilities, overall_likelihood |
| RiskScorer | generate_risk_matrix | risks: List[Dict] | Dict with risk_distribution, heat_map, top_risks (top 10), aggregate_metrics |
| RiskScorer | prioritize_remediation | risks: List[Dict] | List[Dict] sorted by priority with timeline, resources, dependencies, quick_wins |
| ExecutiveReporter | generate_executive_summary | data: Dict | Dict with compliance_status, key_findings, critical_risks, recommendations, next_steps |
| ExecutiveReporter | create_dashboard_metrics | data: Dict | Dict with KPIs, trend_indicators, financial_metrics, operational_metrics |
| ExecutiveReporter | prepare_board_presentation | data: Dict | Dict with 6 slides: summary, dashboard, risk map, remediation, resources, recommendations |
| ExecutiveReporter | generate_trend_analysis | data: Dict | Dict with compliance/risk/regulatory/operational trends, quarterly forecast |

**Agent Orchestration Flow:**

```
ComplianceOrchestrator.run_compliance_analysis(analysis_id, request_data)
  |
  +-- [1] Update status -> "processing"
  |
  +-- [2] Check agent mode
  |     |
  |     +-- Mock mode: Generate mock results directly
  |     |
  |     +-- Real mode: _run_agent_analysis()
  |           |
  |           +-- Create CrewAI Crew with 4 agents:
  |           |     - regulatory_analyst.agent
  |           |     - policy_mapper.agent
  |           |     - evidence_validator.agent
  |           |     - risk_scorer.agent
  |           |
  |           +-- Execute crew tasks (sequential)
  |
  +-- [3] Store results in self.analyses[analysis_id]
  |
  +-- [4] Update status -> "completed" (with completed_at timestamp)
  |
  +-- [Error] Update status -> "failed" (with error message)
```

### 4.2 API Design

**Complete Endpoint Table:**

| Method | Path | Request Body | Response | Description |
|--------|------|-------------|----------|-------------|
| GET | `/` | -- | `{name, version, status, features[]}` | Platform info |
| GET | `/health` | -- | `{status, services{api, database, agents, vector_store}, timestamp}` | Health check |
| GET | `/api/v1/dashboard/metrics` | -- | `DashboardMetrics` | Real-time KPIs, trends, risk distribution |
| GET | `/api/v1/dashboard/activities` | -- | `{activities[{id, type, title, timestamp, severity}]}` | Recent activity feed |
| POST | `/api/v1/documents/upload` | `multipart/form-data: file, doc_type` | `DocumentUploadResponse` | Upload document for processing |
| GET | `/api/v1/documents` | Query: `doc_type?, status?, limit=100` | `{documents[], total}` | List documents with filters |
| POST | `/api/v1/compliance/analyze` | `ComplianceRequest` | `ComplianceResponse` | Initiate compliance analysis |
| GET | `/api/v1/compliance/status/{compliance_id}` | -- | `{compliance_id, status, progress}` | Check analysis progress |
| GET | `/api/v1/compliance/results/{compliance_id}` | -- | Analysis results with gaps, risks, recommendations | Get completed analysis results |
| GET | `/api/v1/compliance/regulations` | -- | `{regulations[{id, name, jurisdiction}]}` | List supported regulations |
| GET | `/api/v1/regulations` | -- | `{regulations[{id, name, jurisdiction, requirements, last_updated}]}` | Detailed regulation listing |
| GET | `/api/v1/policies` | -- | `{policies[]}` | List all policies |
| POST | `/api/v1/policies` | Query: `name, content, version=1.0` | `{policy_id, status}` | Create new policy |
| GET | `/api/v1/risks` | Query: `level?, status=open` | `{risks[], total}` | List risks with filters |
| POST | `/api/v1/risks/assess` | `List[str]` (gap_ids) | `{assessments[], total_risk_score, overall_risk_level}` | Assess risk for gaps |
| POST | `/api/v1/evidence/validate` | `EvidenceValidationRequest` | `{validations[], total_validated, overall_validity}` | Validate evidence |
| POST | `/api/v1/gaps/analyze` | `GapAnalysisRequest` | `{gaps[], total_gaps, critical_gaps, coverage_score}` | Analyze regulation-policy gaps |
| GET | `/api/v1/agents/status` | -- | `List[AgentStatus]` | Agent health and task counts |
| POST | `/api/v1/agents/{agent_name}/execute` | `Dict[str, Any]` (task_data) | `{status, agent, result}` | Execute task with specific agent |
| POST | `/api/v1/reports/generate` | `ReportRequest` | `ReportResponse` | Generate compliance report |
| GET | `/api/v1/reports` | Query: `report_type?, limit=50` | `{reports[]}` | List generated reports |
| GET | `/api/v1/reports/{report_id}` | -- | Report detail with content | Get specific report |

**Request/Response Flow (Full Version):**

```
Client Request
     |
     v
+----+-----+     +----------+     +--------------+
| FastAPI   |---->| Pydantic |---->| Route        |
| CORS      |     | Validate |     | Handler      |
| Middleware |     | Request  |     |              |
+-----------+     +----------+     +------+-------+
                                          |
                          +---------------+-----------+
                          |               |           |
                   +------v------+ +------v-----+ +--v-----------+
                   | Orchestrator| | Storage    | | Background   |
                   | (Agents)   | | Service    | | Tasks        |
                   +------+------+ +------+-----+ +--------------+
                          |               |
                   +------v------+ +------v-----+
                   | CrewAI Crew | | File I/O   |
                   | Execution   | | + Metadata |
                   +------+------+ +------+-----+
                          |               |
                   +------v------+ +------v-----+
                   | LLM API    | | PostgreSQL |
                   | (OpenAI)   | | / Redis    |
                   +-------------+ +------------+
                          |
                     +----v----+
                     | Response|
                     | (JSON)  |
                     +---------+
```

### 4.3 Data Models

**Database Schema (SQLAlchemy ORM):**

```
+------------------------------------------+
|          compliance_analyses             |
+------------------------------------------+
| id          : String (PK, UUID)          |
| created_at  : DateTime (default: utcnow) |
| updated_at  : DateTime (auto-update)     |
| status      : String (default: "pending")|
| compliance_score : Float (default: 0.0)  |
| regulation_type  : String                |
| results     : JSON                       |
| metadata    : JSON                       |
+------------------------------------------+

+------------------------------------------+
|              documents                   |
+------------------------------------------+
| id          : String (PK, UUID)          |
| filename    : String (NOT NULL)          |
| doc_type    : String                     |
| upload_date : DateTime (default: utcnow) |
| status      : String (default: "pending")|
| file_path   : String                     |
| metadata    : JSON                       |
+------------------------------------------+

+------------------------------------------+
|              policies                    |
+------------------------------------------+
| id          : String (PK, UUID)          |
| name        : String (NOT NULL)          |
| version     : String                     |
| created_at  : DateTime (default: utcnow) |
| updated_at  : DateTime (auto-update)     |
| status      : String (default: "active") |
| content     : JSON                       |
| metadata    : JSON                       |
+------------------------------------------+

+------------------------------------------+
|                risks                     |
+------------------------------------------+
| id              : String (PK, UUID)      |
| identified_at   : DateTime (utcnow)     |
| risk_level      : String                 |
| risk_score      : Float                  |
| description     : String                 |
| mitigation_status : String (def: "open") |
| metadata        : JSON                   |
+------------------------------------------+

+------------------------------------------+
|               reports                    |
+------------------------------------------+
| id           : String (PK, UUID)         |
| generated_at : DateTime (utcnow)        |
| report_type  : String                    |
| period       : String                    |
| content      : JSON                      |
| metadata     : JSON                      |
+------------------------------------------+
```

**Pydantic Schema Hierarchy:**

```
BaseModel
  |
  +-- Enums
  |     +-- RegulationType: GDPR | SOX | FINRA | SEC | HIPAA | PCI_DSS
  |     +-- RiskLevel: CRITICAL | HIGH | MEDIUM | LOW | MINIMAL
  |
  +-- Request Models
  |     +-- ComplianceRequest
  |     |     +-- regulation_type: RegulationType
  |     |     +-- document_ids: List[str]
  |     |     +-- policy_ids: Optional[List[str]]
  |     |     +-- include_evidence: bool = True
  |     |     +-- generate_report: bool = True
  |     |
  |     +-- ReportRequest
  |     |     +-- report_type: str  ("executive" | "technical" | "audit")
  |     |     +-- period: str  ("Q1" | "Q2" | "Q3" | "Q4" | "Annual")
  |     |     +-- filters: Optional[Dict[str, Any]]
  |     |     +-- include_charts: bool = True
  |     |     +-- format: str = "pdf"
  |
  +-- Response Models
  |     +-- ComplianceResponse
  |     |     +-- compliance_id: str
  |     |     +-- status: str
  |     |     +-- message: str
  |     |     +-- estimated_time: Optional[int]
  |     |
  |     +-- DocumentUploadResponse
  |     |     +-- document_id: str
  |     |     +-- filename: str
  |     |     +-- status: str
  |     |     +-- message: str
  |     |
  |     +-- ReportResponse
  |           +-- report_id: str
  |           +-- status: str
  |           +-- message: str
  |           +-- download_url: Optional[str]
  |
  +-- Domain Models
  |     +-- Gap
  |     |     +-- id, description, severity, regulation, remediation
  |     |     +-- estimated_cost: Optional[float]
  |     |     +-- timeline: Optional[str]
  |     |
  |     +-- Risk
  |     |     +-- id, level: RiskLevel, score: float, description, mitigation
  |     |     +-- status: str = "open"
  |     |     +-- owner: Optional[str]
  |     |
  |     +-- Policy
  |     |     +-- id, name, version, content, created_at
  |     |     +-- updated_at: Optional[datetime]
  |     |     +-- status: str = "active"
  |     |     +-- coverage: List[str]
  |     |
  |     +-- Evidence
  |           +-- id, type, source, timestamp
  |           +-- content: Optional[str]
  |           +-- validation_status: str = "pending"
  |           +-- hash: Optional[str]
  |
  +-- Composite Result Models
  |     +-- ComplianceResult
  |     |     +-- compliance_id, regulation_type, compliance_score: float
  |     |     +-- gaps: List[Gap], risks: List[Risk]
  |     |     +-- evidence_summary: Dict, recommendations: List[Dict]
  |     |     +-- executive_summary: str
  |     |
  |     +-- ValidationResult
  |     |     +-- evidence_id, validation_status
  |     |     +-- completeness: float, accuracy: float
  |     |     +-- matched_requirements: List[str], issues: List[str]
  |     |
  |     +-- GapAnalysisResult
  |     |     +-- gaps: List[Gap], coverage_score: float
  |     |     +-- total_gaps: int, critical_gaps: int
  |     |     +-- remediation_plan: Optional[Dict]
  |     |
  |     +-- RiskAssessment
  |           +-- assessments: List[Dict], total_risk_score: float
  |           +-- recommended_priority: str
  |           +-- mitigation_timeline: str, estimated_budget: float
  |
  +-- Dashboard Models
        +-- DashboardMetrics
        |     +-- overall_compliance: float, active_risks: int
        |     +-- open_gaps: int, audit_readiness: float
        |     +-- trends: Dict[str, List[Dict]]
        |     +-- risk_distribution: Dict[str, int]
        |     +-- regulatory_status: List[Dict]
        |
        +-- AgentStatus
              +-- agent_id: str, name: str, status: str
              +-- tasks_completed: int
              +-- last_active: Optional[datetime]
```

### 4.4 Service Design

**Orchestrator Sequence Diagram -- Compliance Analysis:**

```
Client          API Handler       Orchestrator        Agents            Data Stores
  |                 |                  |                  |                  |
  |  POST /analyze  |                  |                  |                  |
  |---------------->|                  |                  |                  |
  |                 | create_analysis() |                  |                  |
  |                 |----------------->|                  |                  |
  |                 |                  | Generate ID      |                  |
  |                 |                  | COMP-{uuid8}     |                  |
  |                 |<-analysis_id-----|                  |                  |
  |                 |                  |                  |                  |
  |                 | [BackgroundTask] |                  |                  |
  |  <--202---------|  run_compliance  |                  |                  |
  |  {status:       |  _analysis()    |                  |                  |
  |   processing}   |---------------->|                  |                  |
  |                 |                  | status="processing"               |
  |                 |                  |                  |                  |
  |                 |                  | [If real agents] |                  |
  |                 |                  |  Create Crew     |                  |
  |                 |                  |----------------->|                  |
  |                 |                  |                  | RegulatoryAnalyst|
  |                 |                  |                  |---extract_reqs-->|
  |                 |                  |                  |<--requirements---|
  |                 |                  |                  |                  |
  |                 |                  |                  | PolicyMapper     |
  |                 |                  |                  |---map_policies-->|
  |                 |                  |                  |<--gaps-----------|
  |                 |                  |                  |                  |
  |                 |                  |                  | EvidenceValidator|
  |                 |                  |                  |---validate------>|
  |                 |                  |                  |<--validation-----|
  |                 |                  |                  |                  |
  |                 |                  |                  | RiskScorer       |
  |                 |                  |                  |---score_risks--->|
  |                 |                  |                  |<--scores---------|
  |                 |                  |                  |                  |
  |                 |                  | Aggregate results|                  |
  |                 |                  | status="completed"                 |
  |                 |                  |                  |                  |
  |  GET /status    |                  |                  |                  |
  |---------------->|  get_analysis    |                  |                  |
  |                 |  _status()       |                  |                  |
  |                 |----------------->|                  |                  |
  |  <--{progress:  |<--status---------|                  |                  |
  |      100}       |                  |                  |                  |
  |                 |                  |                  |                  |
  |  GET /results   |                  |                  |                  |
  |---------------->|  get_analysis    |                  |                  |
  |                 |  _results()      |                  |                  |
  |                 |----------------->|                  |                  |
  |  <--{results}   |<--full results---|                  |                  |
```

**Storage Service Design:**

```
StorageService
  |
  +-- initialize()
  |     +-- Create directories: documents/, policies/, reports/, metadata/
  |     +-- Load metadata from ./data/metadata/storage.json
  |
  +-- In-Memory State:
  |     +-- self.documents: Dict[str, Dict]   # doc_id -> metadata
  |     +-- self.policies: Dict[str, Dict]    # policy_id -> metadata
  |     +-- self.reports: Dict[str, Dict]     # report_id -> metadata
  |     +-- self.activities: List[Dict]       # max 1000 entries
  |
  +-- Persistence:
  |     +-- _save_metadata() -> writes to ./data/metadata/storage.json
  |     |     (saves last 100 activities to disk)
  |     +-- _load_metadata() -> reads from ./data/metadata/storage.json
  |
  +-- Activity Logging:
  |     +-- _add_activity(type, title, metadata)
  |     +-- Auto-truncates at 1000 entries
  |     +-- Types: document_uploaded, policy_created, analysis_completed, etc.
  |
  +-- cleanup()
        +-- Saves all pending metadata to disk
```

**RAG Pipeline Flow:**

```
Document Upload                    Query/Search
     |                                  |
     v                                  v
+----+--------+                  +------+-------+
| Raw Document|                  | Search Query |
| (text)      |                  | (natural     |
+----+--------+                  |  language)   |
     |                           +------+-------+
     v                                  |
+----+----------+                       v
| Text Splitter |               +-------+--------+
| chunk=1000    |               | OpenAI         |
| overlap=200   |               | Embeddings     |
| separators:   |               | (ada-002)      |
| \n\n, \n,     |               +-------+--------+
| ". ", " ", "" |                       |
+----+----------+                       v
     |                          +-------+--------+
     v                          | ChromaDB       |
+----+----------+               | Similarity     |
| Chunks[]      |               | Search         |
| + metadata    |               | (with scores)  |
| (doc_id,      |               +-------+--------+
|  doc_type,    |                       |
|  chunk_index, |                       v
|  total_chunks)|               +-------+--------+
+----+----------+               | Ranked Results |
     |                          | [{content,     |
     v                          |   metadata,    |
+----+----------+               |   score,       |
| OpenAI        |               |   source}]     |
| Embeddings    |               +----------------+
| (ada-002)     |
+----+----------+
     |
     v
+----+---------+
| ChromaDB     |
| add_documents|
| (vectors +   |
|  metadata)   |
+--------------+
```

---

## 5. Data Flow Diagrams

### 5.1 Compliance Analysis Flow

```
+----------+       +----------+       +-------------------+
| User     |       | Frontend |       | API (FastAPI)     |
| selects  |------>| sends    |------>| POST /compliance/ |
| regulation|      | POST req |       | analyze           |
| + docs   |       |          |       |                   |
+----------+       +----------+       +--------+----------+
                                               |
                                    +----------v-----------+
                                    | Orchestrator          |
                                    | create_analysis()     |
                                    | -> COMP-{uuid8}       |
                                    +----------+-----------+
                                               |
                              +----------------v------------------+
                              | BackgroundTask:                    |
                              | run_compliance_analysis()          |
                              +----------------+------------------+
                                               |
                    +--------------------------+--------------------------+
                    |                          |                          |
          +---------v---------+    +-----------v---------+    +----------v----------+
          | RegulatoryAnalyst |    | PolicyMapper        |    | EvidenceValidator   |
          | - Extract reqs    |    | - Map policies      |    | - Validate evidence |
          | - Search regs     |    | - Identify gaps     |    | - Quality assess    |
          | - RAG semantic    |    | - Embedding match   |    | - Timeliness check  |
          | - Entity extract  |    | - Cosine similarity |    | - Chain verify      |
          +---------+---------+    +-----------+---------+    +----------+----------+
                    |                          |                          |
                    +--------------------------+--------------------------+
                                               |
                                    +----------v-----------+
                                    | RiskScorer            |
                                    | - Score each gap      |
                                    | - Impact x Likelihood |
                                    |   x (1-Control Eff)   |
                                    | - Generate matrix     |
                                    | - Prioritize          |
                                    +----------+-----------+
                                               |
                                    +----------v-----------+
                                    | Aggregate Results     |
                                    | - compliance_score    |
                                    | - gaps[]              |
                                    | - risks[]             |
                                    | - recommendations[]   |
                                    | - evidence_validation |
                                    +----------+-----------+
                                               |
                                    +----------v-----------+
                                    | Store in              |
                                    | self.analyses[id]     |
                                    | status = "completed"  |
                                    +-----------------------+
```

### 5.2 Document Upload & Processing Flow

```
+----------+      +-----------+      +-------------------+
| User     |      | Frontend  |      | API               |
| drags    |----->| React     |----->| POST /documents/  |
| file via |      | Dropzone  |      | upload             |
| UI       |      | FormData  |      | (multipart)       |
+----------+      +-----------+      +--------+----------+
                                              |
                                   +----------v-----------+
                                   | Validate file         |
                                   | - Size <= 100MB       |
                                   | - Allowed types:      |
                                   |   .pdf .doc .docx     |
                                   |   .txt .csv .xlsx     |
                                   +----------+-----------+
                                              |
                              +---------------+---------------+
                              |                               |
                   +----------v-----------+        +----------v-----------+
                   | StorageService        |        | DocumentService      |
                   | save_document()       |        | upload_document()    |
                   | - DOC-{uuid8}         |        | - {timestamp}_{md5}  |
                   | - Write to disk       |        | - ThreadPoolExecutor |
                   | - Save metadata       |        | - SHA256 hash        |
                   | - Log activity        |        | - Save metadata JSON |
                   +----------+-----------+        +----------+-----------+
                              |                               |
                              +---------------+---------------+
                                              |
                                   +----------v-----------+
                                   | Return 200            |
                                   | DocumentUploadResponse|
                                   | {document_id,         |
                                   |  filename,            |
                                   |  status:"processing"} |
                                   +----------+-----------+
                                              |
                                   +----------v-----------+
                                   | [BackgroundTask]      |
                                   | orchestrator          |
                                   | .process_document()   |
                                   +----------+-----------+
                                              |
                                   +----------v-----------+
                                   | RAGService            |
                                   | .ingest_document()    |
                                   | - Decode UTF-8        |
                                   | - Chunk text (1000)   |
                                   | - Generate embeddings |
                                   | - Store in ChromaDB   |
                                   +-----------------------+
```

### 5.3 Report Generation Flow

```
+----------+      +-----------+      +-------------------+
| User     |      | Frontend  |      | API               |
| selects  |----->| sends     |----->| POST /reports/    |
| report   |      | ReportReq |      | generate          |
| type +   |      |           |      |                   |
| period   |      |           |      |                   |
+----------+      +-----------+      +--------+----------+
                                              |
                                   +----------v-----------+
                                   | Orchestrator          |
                                   | create_report()       |
                                   | -> RPT-{uuid8}        |
                                   +----------+-----------+
                                              |
                                   +----------v-----------+
                                   | Return 202            |
                                   | ReportResponse        |
                                   | {report_id,           |
                                   |  status:"generating"} |
                                   +----------+-----------+
                                              |
                                   +----------v-----------+
                                   | [BackgroundTask]      |
                                   | generate_report()     |
                                   +----------+-----------+
                                              |
                              +---------------+---------------+
                              |                               |
                   +----------v-----------+        +----------v-----------+
                   | ExecutiveReporter     |        | Gather Data          |
                   | Agent                 |        | - Compliance scores  |
                   |                       |        | - Risk assessments   |
                   | If real agents:       |        | - Gap analysis       |
                   | - generate_summary    |        | - Evidence status    |
                   | - create_metrics      |        +----------------------+
                   | - prepare_presentation|
                   | - generate_trends     |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   | Report Content        |
                   | - executive_summary   |
                   | - key_findings[]      |
                   | - compliance_scores{} |
                   | - recommendations[]   |
                   | - next_steps[]        |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   | Store in              |
                   | self.reports[id]      |
                   | status = "completed"  |
                   | + completed_at        |
                   +----------+-----------+
                              |
                   +----------v-----------+
                   | Client polls          |
                   | GET /reports/{id}     |
                   | -> Full report JSON   |
                   +-----------------------+
```

---

## 6. Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11 | Runtime (slim Docker image) |
| FastAPI | 0.111.0 | Async web framework, OpenAPI auto-docs |
| Uvicorn | 0.30.1 (standard) | ASGI server with uvloop and httptools |
| Pydantic | 2.8.2 | Data validation, settings management, schema definitions |
| SQLAlchemy | 2.0.31 | Async ORM with declarative models |
| asyncpg | 0.29.0 | PostgreSQL async driver |
| Redis (python) | 5.0.7 | Redis client for caching and pub/sub |
| aiofiles | 23.2.1 | Async file I/O operations |
| CrewAI | 0.41.1 | Multi-agent orchestration framework |
| LangChain | 0.2.14 | Agent tool framework, text splitters, document schemas |
| langchain-openai | 0.1.20 | OpenAI integration (embeddings, LLM calls) |
| OpenAI SDK | 1.35.3 | Direct OpenAI API client |
| ChromaDB | >=0.5.10, <0.6.0 | Vector store client |
| python-dotenv | 1.0.1 | Environment variable loading from .env |
| python-multipart | 0.0.9 | Multipart form data parsing (file uploads) |
| httpx | 0.27.0 | Async HTTP client |
| structlog | 24.4.0 | Structured logging with context binding |
| tenacity | 8.5.0 | Retry logic with exponential backoff |
| python-jose | 3.3.0 | JWT token creation and verification |
| passlib + bcrypt | 1.7.4 / 4.1.3 | Password hashing |
| prometheus-client | 0.20.0 | Metrics collection (optional) |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI component library |
| TypeScript | 4.9.5 | Type-safe JavaScript |
| react-scripts | 5.0.1 | Create React App build toolchain |
| @mui/material | 5.15.20 | Material UI component library |
| @mui/icons-material | 5.15.20 | Material UI icon set |
| @mui/x-charts | 7.7.0 | Advanced chart components |
| @mui/x-data-grid | 7.7.0 | Data grid component |
| @tanstack/react-query | 5.45.1 | Server state management |
| axios | 1.7.2 | HTTP client |
| recharts | 2.12.7 | Charting library (Line, Pie, Bar) |
| react-router-dom | 6.23.1 | Client-side routing |
| react-dropzone | 14.2.3 | File upload drag-and-drop |
| react-hook-form | 7.52.0 | Form management |
| notistack | 3.0.1 | Snackbar notifications |
| date-fns | 3.6.0 | Date utilities |
| @emotion/react + styled | 11.11.x | CSS-in-JS (MUI peer dependency) |

### Infrastructure

| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 15 (Alpine) | Relational database |
| Redis | 7 (Alpine) | Caching, rate limiting, pub/sub |
| ChromaDB | latest | Vector store for embeddings |
| Docker | -- | Containerization |
| Docker Compose | -- | Multi-service orchestration |
| Node.js | -- | Frontend build environment |

---

## 7. Deployment Architecture

### Docker Compose Topology

```
docker-compose.yml
  |
  +-- compliance-network (bridge)
       |
       +-- [compliance-postgres]     port 5432:5432
       |     image: postgres:15-alpine
       |     volume: postgres_data -> /var/lib/postgresql/data
       |     healthcheck: pg_isready (10s interval, 5 retries)
       |     env: POSTGRES_USER=compliance_user
       |          POSTGRES_PASSWORD=compliance_pass
       |          POSTGRES_DB=compliance_db
       |
       +-- [compliance-redis]        port 6379:6379
       |     image: redis:7-alpine
       |     volume: redis_data -> /data
       |     command: redis-server --appendonly yes
       |
       +-- [compliance-chroma]       port 8000:8000
       |     image: chromadb/chroma:latest
       |     volume: chroma_data -> /chroma/chroma
       |     env: CHROMA_SERVER_HOST=0.0.0.0
       |          CHROMA_SERVER_HTTP_PORT=8000
       |          ANONYMIZED_TELEMETRY=false
       |
       +-- [compliance-backend]      port 8001:8001
       |     build: Dockerfile.backend (python:3.11-slim)
       |     volumes: ./src -> /app/src (dev mount)
       |              ./data -> /app/data
       |     depends_on: postgres (healthy), redis (started), chroma (started)
       |     healthcheck: curl http://localhost:8001/health (30s interval)
       |     env: DATABASE_URL=postgresql+asyncpg://...@postgres:5432/compliance_db
       |          REDIS_URL=redis://redis:6379/0
       |          CHROMA_HOST=chroma
       |          CHROMA_PORT=8000
       |          OPENAI_API_KEY=${OPENAI_API_KEY:-dummy_key}
       |          ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
       |     cmd: uvicorn src.api.main_simple:app --host 0.0.0.0 --port 8001
       |
       +-- [compliance-frontend]     port 3000:3000
             build: ./frontend/Dockerfile
             depends_on: backend
             env: REACT_APP_API_URL=http://localhost:8001
```

**Service Dependency Graph:**

```
              frontend (3000)
                  |
                  | depends_on
                  v
              backend (8001)
              /     |      \
    depends_on  depends_on  depends_on
    (healthy)  (started)   (started)
       /          |            \
      v           v             v
  postgres    redis          chroma
  (5432)      (6379)         (8000)
```

**Volume Mapping:**

| Volume | Container Path | Purpose |
|--------|---------------|---------|
| postgres_data | /var/lib/postgresql/data | Persistent database storage |
| redis_data | /data | Redis AOF persistence |
| chroma_data | /chroma/chroma | Vector store persistence |
| ./src (bind) | /app/src | Backend source code (dev hot-reload) |
| ./data (bind) | /app/data | Document storage and metadata |

**Backend Dockerfile (`Dockerfile.backend`):**

```
Base Image:  python:3.11-slim
System Deps: gcc, curl
Python Deps: requirements-minimal.txt
App Copy:    ./src -> /app/src
Directories: /app/data/{documents,policies,reports,metadata}
Port:        8001
Entrypoint:  uvicorn src.api.main_simple:app --host 0.0.0.0 --port 8001
```

**Network Configuration:**
- All services share `compliance-network` (Docker bridge driver)
- Inter-service communication uses container names as hostnames (e.g., `postgres`, `redis`, `chroma`)
- Frontend accesses backend via `http://localhost:8001` (host-mapped port)
- Backend accesses databases via internal Docker DNS

---

## 8. Security Architecture

### Authentication Flow

```
+----------+       +-----------+       +-------------------+
| Client   |       | FastAPI   |       | JWT Auth          |
| (Browser)|------>| Endpoint  |------>| Middleware         |
+----------+       +-----------+       +--------+----------+
                                                |
                                     +----------v-----------+
                                     | python-jose          |
                                     | - Algorithm: HS256   |
                                     | - Secret: SECRET_KEY |
                                     | - Expiry: 30 min     |
                                     +----------+-----------+
                                                |
                                     +----------v-----------+
                                     | passlib + bcrypt     |
                                     | - Password hashing   |
                                     | - BCrypt rounds      |
                                     +-----------------------+
```

**Authentication Configuration (from `config.py`):**

| Setting | Default | Source |
|---------|---------|--------|
| `secret_key` | (required) | `SECRET_KEY` env var |
| `algorithm` | HS256 | `ALGORITHM` env var |
| `access_token_expire_minutes` | 30 | `ACCESS_TOKEN_EXPIRE_MINUTES` env var |

### Data Protection

| Layer | Protection | Implementation |
|-------|-----------|----------------|
| Transport | HTTPS/TLS | Reverse proxy (production) |
| API | CORS policy | FastAPI CORSMiddleware with configurable origins |
| Authentication | JWT tokens | python-jose with HS256, 30-minute expiry |
| Passwords | Bcrypt hashing | passlib with bcrypt backend |
| Documents | SHA256 integrity | Hash computed on upload, stored in metadata |
| Database | Connection pooling | SQLAlchemy async pool with pre-ping health checks |
| Secrets | Environment variables | python-dotenv loading from .env file |
| File Upload | Size limit | 100MB max upload size |
| File Upload | Type validation | Allowed: .pdf, .doc, .docx, .txt, .csv, .xlsx |

### API Security

- **Input Validation:** All request bodies validated via Pydantic models with type enforcement
- **Error Handling:** Structured error responses via FastAPI `HTTPException` (400, 404, 413, 500)
- **Rate Limiting:** Redis-based rate limiting (infrastructure ready, configured via `REDIS_URL`)
- **CORS:** Configurable origin list; defaults to `["http://localhost:3000", "http://localhost:3001"]` in production config, `["*"]` in development
- **File Validation:** Upload size check (100MB), file type whitelist enforcement
- **SQL Injection Prevention:** SQLAlchemy ORM with parameterized queries
- **Dependency Isolation:** Docker container isolation per service
- **Secrets Management:** All sensitive values (API keys, database credentials, JWT secret) loaded from environment variables, never hardcoded

---

## 9. Non-Functional Requirements

### Performance

| Metric | Target | Implementation |
|--------|--------|----------------|
| API response time (simple queries) | < 200ms | In-memory storage for simple endpoints, async handlers |
| Document upload | < 5s for 100MB | Async file I/O via ThreadPoolExecutor (4 workers) |
| Compliance analysis | < 120s | Background task execution, progress tracking |
| Semantic search | < 500ms | ChromaDB vector similarity with pre-computed embeddings |
| Dashboard load | < 1s | TanStack Query caching, refetch on demand |
| Database connection | Pooled | pool_size=10, max_overflow=20, pool_pre_ping=True |

### Scalability

| Dimension | Approach |
|-----------|----------|
| Horizontal API scaling | Stateless FastAPI instances behind load balancer; in-memory state migrates to PostgreSQL/Redis |
| Agent parallelism | CrewAI Crew supports parallel task execution; orchestrator can spawn multiple crews |
| Document storage | File system storage can migrate to S3/object storage; metadata in PostgreSQL |
| Vector store | ChromaDB supports distributed mode; can scale to millions of embeddings |
| Database | PostgreSQL connection pool with overflow; supports read replicas |
| Caching | Redis cluster for distributed caching; pub/sub for cross-instance events |
| Background tasks | Can migrate from FastAPI BackgroundTasks to Celery/Redis for distributed task queues |

### Availability

| Component | Strategy |
|-----------|----------|
| API | Health check endpoint `/health` with service-level status; Docker restart policies |
| Database | PostgreSQL health check via `pg_isready` (10s interval, 5 retries); connection pool pre-ping |
| Backend | Docker health check via `curl /health` (30s interval, 3 retries, 40s start period) |
| Agents | Mock fallback when real agents fail to initialize; graceful degradation |
| Storage | File system with JSON metadata backup; async writes with error handling |
| Analysis Jobs | Status tracking (created/processing/validating/completed/failed); error capture |

### Observability

| Aspect | Tool | Details |
|--------|------|---------|
| Structured Logging | structlog | Context-bound loggers per agent/service; key-value log entries |
| Application Logging | Python logging | Standard logging for orchestrator and API layer |
| Metrics | prometheus-client | Optional metrics collection endpoint |
| Health Monitoring | /health endpoint | Reports status of API, database, agents, and vector store |
| Activity Tracking | StorageService | Activity log with type, title, timestamp, metadata (max 1000 entries) |
| Agent Metrics | BaseComplianceAgent.get_metrics() | Agent name, role, tool count, max iterations |

### Reliability

| Feature | Implementation |
|---------|----------------|
| Retry logic | tenacity: 3 attempts, exponential backoff (min 4s, max 10s) on all agent executions |
| Error isolation | Each agent tool wrapped in try/except; returns empty result on failure |
| Graceful degradation | Orchestrator falls back to mock agents if CrewAI initialization fails |
| Data integrity | SHA256 hashing on document upload; file metadata consistency checks |
| Idempotency | UUID-based IDs for all entities prevent duplicate creation |
| Background task safety | Analysis and report generation run in background with status tracking; failures captured in analysis record |

---

*This document reflects the current implementation as of the codebase state on 2026-02-19. It should be updated as the platform evolves.*
