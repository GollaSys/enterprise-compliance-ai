# Agent Demo Redesign — Spec

**Date:** 2026-04-10
**Audience:** Engineering team demo
**Status:** Approved for implementation

---

## Goal

Extend the existing Enterprise Compliance AI platform with a new demo stack that showcases Agent-to-Agent (A2A) communication, RAG, MCP integration, agent memory, and observability. The existing v1 backend and all 21 passing tests remain untouched.

---

## Approach: Side-by-Side Demo Layer

All new code lives in `src/demo/` and is exposed under `/api/v2/`. The existing `main_simple.py` and `/api/v1/` routes are not modified. The React frontend gains a single new page at `/demo`.

This preserves the working baseline and lets the demo script contrast the two: "here is the simple in-memory version; here is what it becomes with real A2A, RAG, MCP, memory, and observability."

---

## Architecture

```
React Frontend (port 3000)
  ├── /api/v1/  →  main_simple.py   (existing, untouched)
  └── /api/v2/  →  src/demo/router.py  (new)
                      └── LangGraph StateGraph
                            ├── 5 agent nodes (A2A Task schemas)
                            ├── SQLite checkpointer (short-term memory)
                            ├── mem0 + Redis (long-term memory)
                            ├── Filesystem MCP + GitHub MCP
                            └── LangSmith + Langfuse + Rich terminal
```

---

## Tech Stack (new additions only)

| Concern | Technology |
|---|---|
| Agent orchestration | LangGraph (`langgraph`) |
| A2A protocol schemas | Pydantic models matching Google A2A spec |
| LLM | OpenAI GPT-4o (real API calls) |
| RAG embeddings | OpenAI `text-embedding-3-small` + ChromaDB (existing service) |
| MCP — documents | `mcp` Python SDK, `@modelcontextprotocol/server-filesystem` subprocess |
| MCP — regulations | `mcp` Python SDK, `@modelcontextprotocol/server-github` subprocess |
| Short-term memory | LangGraph `SqliteSaver` checkpointer (`data/checkpoints.db`) |
| Long-term memory | `mem0` with Redis backend (existing `compliance-redis`, DB index 1) |
| Observability — cloud | LangSmith (`langchain-smith`, `LANGCHAIN_TRACING_V2=true`) |
| Observability — local | Langfuse self-hosted Docker (`langfuse/langfuse:latest`, port 3001) |
| Observability — terminal | `rich` Live layout (3-panel: pipeline status, A2A messages, memory events) |
| Frontend streaming | FastAPI `EventSourceResponse` (SSE), React `EventSource` hook |

---

## File Structure

All new files:

```
src/demo/
├── __init__.py
├── a2a_types.py               # AgentCard, A2ATask, TaskArtifact, TaskState (Pydantic)
├── router.py                  # FastAPI /api/v2/ router — mounts into main_simple.py
│
├── agents/
│   ├── __init__.py
│   ├── regulatory_analyst.py  # LangGraph node + AgentCard definition
│   ├── policy_mapper.py
│   ├── evidence_validator.py
│   ├── risk_scorer.py
│   └── executive_reporter.py
│
├── graph/
│   ├── __init__.py
│   ├── state.py               # ComplianceState TypedDict
│   └── workflow.py            # StateGraph, edges, SqliteSaver checkpointer
│
├── memory/
│   ├── __init__.py
│   └── mem0_client.py         # mem0 init, search(), add(), reset()
│
├── mcp/
│   ├── __init__.py
│   └── client.py              # MCPClient wrapping filesystem + GitHub servers
│
└── observability/
    ├── __init__.py
    ├── langsmith.py           # LangSmith callback handler
    ├── langfuse.py            # Langfuse span wrapper per agent node
    └── terminal.py            # Rich Live panel — AgentTerminalPanel class

frontend/src/
├── pages/AgentDemo.tsx        # /demo route — pipeline view + SSE event log
└── hooks/useAgentStream.ts    # EventSource hook returning typed AgentEvent[]

scripts/
└── demo_smoke_test.py         # End-to-end smoke test against seeded GDPR PDF

data/
└── samples/
    └── gdpr_policy_sample.pdf # Seeded 3-page fictional GDPR policy with intentional gaps

tests/
├── test_demo_graph.py         # LangGraph node unit tests (FakeListChatModel, mocked MCP)
└── test_demo_api.py           # /api/v2/ endpoint tests (FastAPI TestClient)
```

`docker-compose.yml` gains two new services (`langfuse-db`, `langfuse`). All existing services unchanged.

---

## A2A Types

Each inter-agent handoff uses this schema (matches Google A2A spec, April 2025):

```python
class A2ATask(BaseModel):
    task_id: str                    # uuid4
    sender_agent: str               # e.g. "regulatory_analyst"
    recipient_agent: str            # e.g. "policy_mapper"
    state: TaskState                # pending | in_progress | completed | failed
    artifacts: List[TaskArtifact]   # structured output from sender
    mcp_calls: List[MCPCall]        # MCP tool calls made during this task
    timestamp: datetime

class TaskArtifact(BaseModel):
    type: str                       # e.g. "requirements_list", "gap_analysis"
    content: Any                    # agent-specific payload
    metadata: dict                  # source_doc, rag_chunks_used, etc.

class AgentCard(BaseModel):
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    input_schema: dict
    output_schema: dict
    mcp_servers: List[str]
```

`GET /api/v2/agents/cards` returns all 5 AgentCards — engineers can inspect agent capabilities at runtime.

---

## LangGraph State

```python
class ComplianceState(TypedDict):
    # Input
    regulation_type: str            # e.g. "GDPR"
    document_path: str              # resolved path to PDF

    # A2A message log — grows as agents complete
    a2a_tasks: List[A2ATask]

    # Memory
    long_term_context: dict         # mem0 search results loaded at run start
    short_term_memory: dict         # managed by SqliteSaver automatically

    # MCP
    mcp_artifacts: List[dict]       # files fetched via MCP during this run

    # Output
    final_report: Optional[str]
    error: Optional[str]

    # SSE
    sse_events: List[dict]          # accumulated events streamed to frontend
```

The graph is a `StateGraph(ComplianceState)` with 5 sequential nodes plus an `error_handler` node. Edges are linear except: if any node sets `state["error"]`, the graph routes to `error_handler` instead of the next agent.

---

## Data Flow — One Demo Run

**Trigger:** `POST /api/v2/demo/run` with `{"regulation_type": "GDPR", "document_id": "<optional>"}`

**Step 0 — Pre-graph mem0 lookup**
Before the graph starts, `mem0_client.search(f"{regulation_type} prior findings")` is called. Results loaded into `state.long_term_context`. Terminal shows: "Memory hit — N prior findings loaded" or "No prior memory for GDPR".

**Step 1 — Regulatory Analyst node**
- Calls Filesystem MCP → reads document from `document_path`
- Chunks text (1000 chars, 200 overlap) → OpenAI embeddings → ChromaDB similarity search
- Calls GitHub MCP → fetches regulation article text from public repo for cross-reference
- LLM extracts structured requirements list
- Creates `A2ATask(sender="regulatory_analyst", recipient="policy_mapper", artifacts=[requirements])`
- Appends task to `state.a2a_tasks`

**Step 2 — Policy Mapper node**
- Reads `state.a2a_tasks[-1]` — this is the A2A communication
- Calls GitHub MCP → fetches policy files
- LLM maps requirements to policies, identifies coverage gaps
- Creates `A2ATask(sender="policy_mapper", recipient="evidence_validator", artifacts=[gap_analysis])`

**Step 3 — Evidence Validator node (memory demo moment)**
- Queries `mem0.search(f"{regulation_type} {gap_description}")` for each gap
- If prior run flagged a gap as critical, surfaces: "Previously critical — check if mitigation was applied"
- Validates evidence from Filesystem MCP artifacts against gap list
- Creates `A2ATask(sender="evidence_validator", recipient="risk_scorer", artifacts=[validation_results])`

**Step 4 — Risk Scorer node (memory write moment)**
- Scores each gap: `risk = impact × likelihood × (1 - control_effectiveness)`
- Calls `mem0.add()` for each critical finding — persists to Redis for future runs
- Terminal shows: "Storing 3 findings to long-term memory"
- Creates `A2ATask(sender="risk_scorer", recipient="executive_reporter", artifacts=[risk_scores])`

**Step 5 — Executive Reporter node**
- Reads all 4 prior A2ATasks from `state.a2a_tasks`
- LLM generates board-ready report from full message history
- Sets `state.final_report`
- SSE stream closes; server prints LangSmith + Langfuse trace URLs

---

## MCP Integration

`mcp/client.py` exposes an `MCPClient` class that manages two subprocesses:

- **Filesystem MCP** (`@modelcontextprotocol/server-filesystem`): root = `./data/`. Used by Regulatory Analyst and Evidence Validator to read documents.
- **GitHub MCP** (`@modelcontextprotocol/server-github`): Used by Regulatory Analyst (fetches GDPR/SOX article text from `intersoft-consulting/gdpr-checklist` or equivalent public repo, configurable via `GITHUB_REPO` env var) and Policy Mapper (internal policy files from a configured repo).

Both are wrapped as LangChain `Tool` objects and injected into each agent node that needs them. MCP calls are recorded in `A2ATask.mcp_calls` for full traceability.

**Fallbacks:**
- Filesystem MCP subprocess failure → read file directly from disk
- GitHub MCP failure → serve bundled regulation snippets from `data/regulations/` (seeded with GDPR, SOX, FINRA key articles as plain text files — populated by `make demo-reset`)

---

## Memory Design

### Short-term (within-run): LangGraph SqliteSaver
- File: `data/checkpoints.db`
- Key: `thread_id = run_id`
- Agents reference prior steps via `state["a2a_tasks"]` — no separate query needed
- Automatic — LangGraph manages reads/writes

### Long-term (cross-run): mem0 + Redis
- Backend: `compliance-redis` on DB index 1
- **Writes** (Risk Scorer): `mem0.add(text=finding, user_id=regulation_type)` after each run
- **Reads** (Step 0 pre-graph, Evidence Validator): `mem0.search(query, user_id=regulation_type)`
- mem0 handles embedding + similarity search internally
- Failure mode: silent catch, demo continues without long-term context

---

## Observability

### LangSmith
- Enabled via `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` in `.env`
- LangGraph auto-traces all runs — no code changes needed beyond env vars
- Run URL printed to terminal and emitted as final SSE event
- Captures: every LLM call, tool call, token count, latency per node

### Langfuse (self-hosted)
- New Docker service at `http://localhost:3001` (no external account)
- `langfuse.py` wraps each agent node as a named Langfuse span via `observe()` decorator
- Shows: per-agent latency, token cost, memory read/write events as custom spans
- Trace URL emitted as SSE event alongside LangSmith URL

### Rich Terminal Panel
- `AgentTerminalPanel` in `observability/terminal.py` — a `rich.Live` layout with 3 panels:
  - **Pipeline** (top): 5 agent nodes with status badges (idle → ▶ running → ✓ done)
  - **A2A Messages** (middle): scrolling log of Task objects as they are created, colored by agent
  - **Memory Events** (bottom): mem0 reads (yellow) and writes (green) highlighted in real time
- Activated by `make demo` / `run_local.sh --demo`

---

## Frontend: AgentDemo.tsx

New page at route `/demo`, added to existing React Router config.

**Layout:**
- Left panel: 5 AgentCard components — each shows agent name, role, current status badge, task count
- Right panel: SSE event log — timestamped stream of A2A Task messages, MCP tool calls, memory events, LLM responses
- Bottom bar: "View LangSmith trace" + "View Langfuse trace" links (appear after run completes)
- Top bar: regulation type selector (GDPR / SOX / FINRA) + "Use sample doc" toggle + document picker (from uploaded docs)

**SSE hook (`useAgentStream.ts`):**
```typescript
type AgentEvent =
  | { type: "agent_start";   agent: string }
  | { type: "a2a_task";      task: A2ATask }
  | { type: "mcp_call";      server: string; tool: string; path: string }
  | { type: "memory_read";   query: string; hits: number }
  | { type: "memory_write";  finding: string }
  | { type: "agent_done";    agent: string; duration_ms: number }
  | { type: "run_complete";  langsmith_url: string; langfuse_url: string }
  | { type: "error";         agent: string; message: string }
```

---

## Document Strategy

### Seeded sample
`data/samples/gdpr_policy_sample.pdf` — a realistic 3-page fictional company data protection policy with two intentional gaps:
- Missing Article 17 (right-to-erasure) procedure
- Incomplete Article 30 records of processing activities

Used as default when no `document_id` is provided to `POST /api/v2/demo/run`.

### Real uploaded documents
`POST /api/v2/demo/run` accepts an optional `document_id`. If provided, the demo resolves it to the file uploaded via the existing `POST /api/v1/documents/upload` endpoint (stored in `data/uploads/`). The frontend "Live Agent Demo" page shows both options side by side.

---

## API Endpoints (new, all under /api/v2/)

| Method | Path | Description |
|---|---|---|
| POST | `/api/v2/demo/run` | Start a demo run. Body: `{regulation_type, document_id?}`. Returns `{run_id}`. |
| GET | `/api/v2/demo/stream` | SSE stream for a run. Query: `?run_id=...`. Yields `AgentEvent` objects. |
| GET | `/api/v2/demo/run/{run_id}` | Get final result of a completed run. |
| GET | `/api/v2/agents/cards` | List all 5 AgentCards (A2A discovery endpoint). |
| GET | `/api/v2/memory/history` | List mem0 entries. Query: `?regulation_type=GDPR`. |
| DELETE | `/api/v2/memory/reset` | Clear all mem0 entries (demo reset convenience). |

---

## Error Handling

- **Node failure**: try/except in every node. Sets `state["error"]`, routes to `error_handler` node which emits SSE error event and returns partial results. Demo never hangs.
- **MCP unavailable**: 5s subprocess timeout. Filesystem MCP → direct disk read. GitHub MCP → bundled regulation snippets in `data/regulations/`.
- **mem0 / Redis down**: silent catch in all memory calls. Shown as "Memory unavailable" in terminal panel.
- **LLM rate limit**: LangChain built-in retry — 3 attempts, exponential backoff. If all fail, node returns structured mock result so pipeline flow continues.
- **SSE client disconnect**: generator catches `asyncio.CancelledError`, cleans up run state.

---

## Docker Changes

Two new services added to `docker-compose.yml`:

```yaml
langfuse-db:
  image: postgres:15-alpine
  ports: ["5433:5432"]              # separate from compliance-postgres on 5432
  environment:
    POSTGRES_DB: langfuse
    POSTGRES_USER: langfuse
    POSTGRES_PASSWORD: langfuse

langfuse:
  image: langfuse/langfuse:latest
  ports: ["3001:3000"]
  depends_on: [langfuse-db]
  environment:
    DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
    NEXTAUTH_SECRET: demo-secret
    NEXTAUTH_URL: http://localhost:3001
    SALT: demo-salt
```

`mem0` uses existing `compliance-redis` on DB index 1 — no new Redis container.

---

## Testing

**Existing (untouched):**
- `test_api.py` — 10 tests against `/api/v1/`
- `test_complete.py` — 11 tests against `/api/v1/`

**New:**
- `tests/test_demo_graph.py` — unit tests per LangGraph node. Uses `FakeListChatModel` and a mocked `MCPClient`. Tests: A2ATask shape correctness, state transitions, mem0 call signatures, error routing. No real API keys needed.
- `tests/test_demo_api.py` — integration tests for `/api/v2/` endpoints using FastAPI `TestClient` with fully mocked graph. Tests SSE event stream shape and run lifecycle.
- `scripts/demo_smoke_test.py` — end-to-end smoke test against the seeded GDPR PDF using real LLM calls. Validates each agent node produces a non-empty A2ATask artifact. Prints pass/fail per step. Expected runtime: ~30s.

---

## New Environment Variables

Add to `.env.example`:

```bash
# LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=enterprise-compliance-demo

# Langfuse (self-hosted — no key needed for local Docker)
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=demo
LANGFUSE_SECRET_KEY=demo

# GitHub MCP
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_pat
GITHUB_REPO=intersoft-consulting/gdpr-checklist  # public repo for regulation reference text

# mem0
MEM0_REDIS_URL=redis://localhost:6379/1
```

---

## Demo Script (5 minutes, engineering audience)

1. `make demo` — starts all Docker services + Rich terminal panel
2. Open `http://localhost:3000/demo` — Live Agent Demo page
3. Click **"Run with sample GDPR doc"** → watch agents activate, A2A Tasks scroll in terminal, mem0 shows "no prior memory"
4. Run completes → click **LangSmith** link → walk through token-level trace per agent
5. Click **Langfuse** link → show per-agent latency, memory spans
6. Click **"Run again"** → mem0 now shows "2 prior findings loaded" — long-term memory demo moment
7. Upload a real document via Documents page → return to `/demo`, pick it from the selector → run again

---

## Makefile Targets (new)

```makefile
demo:          ## Start all services + demo Rich panel
demo-reset:    ## Clear mem0 memory + SQLite checkpoints (clean demo state)
demo-smoke:    ## Run scripts/demo_smoke_test.py against seeded GDPR PDF
test-demo:     ## Run tests/test_demo_graph.py + tests/test_demo_api.py
```
