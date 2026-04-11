# Enterprise Compliance AI — Demo Pipeline Architecture

This document describes the **v2 demo stack** (`/api/v2/demo/`), which runs alongside the existing v1 system without touching it. It covers the implemented architecture, component design, data flow, and a walkthrough guide for running the demo.

For the v1 system (CrewAI + REST API), see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Deep-Dive](#component-deep-dive)
4. [LangGraph Workflow](#langgraph-workflow)
5. [A2A Protocol & State](#a2a-protocol--state)
6. [Memory Architecture](#memory-architecture)
7. [MCP Integration](#mcp-integration)
8. [Observability](#observability)
9. [API Endpoints](#api-endpoints)
10. [SSE Streaming](#sse-streaming)
11. [Error Handling](#error-handling)
12. [Environment Variables](#environment-variables)
13. [How to Run the Demo](#how-to-run-the-demo)
14. [Demo Walkthrough Script](#demo-walkthrough-script)
15. [Testing](#testing)

---

## Overview

The v2 demo shows what a production-grade AI compliance pipeline looks like when built with modern agent patterns:

| What it demonstrates | How |
|---|---|
| **Agent-to-Agent (A2A) communication** | 5 LangGraph nodes pass typed `A2ATask` envelopes via shared state |
| **Model Context Protocol (MCP)** | `MCPClient` reads documents via filesystem MCP, regulation text via GitHub MCP |
| **Long-term memory** | mem0 + ChromaDB: Risk Scorer writes findings; Evidence Validator surfaces them on next run |
| **Short-term memory** | LangGraph `SqliteSaver` checkpoints the graph state to SQLite across a single run |
| **LLM observability** | LangSmith (cloud) and Langfuse (self-hosted Docker) trace every LLM call per agent |
| **Real-time streaming** | SSE stream delivers agent updates to the frontend as each node completes |

All demo code lives in `src/demo/`. The existing v1 code (`src/agents/`, `src/services/`, `src/api/routers/`) is untouched.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     React Frontend (:3000)                          │
│                                                                     │
│   /demo page (AgentDemo.tsx)                                        │
│     ├── Agent status cards (5 agents, live badges)                  │
│     ├── SSE event log (A2A Tasks, memory events, MCP calls)         │
│     └── Trace links (LangSmith + Langfuse, appear on completion)    │
└─────────────────────┬──────────────────────────────────────────────┘
                      │  HTTP REST + SSE (EventSource)
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (:8001)                            │
│                                                                     │
│   /api/v1/*  ──► main_simple.py  (v1, unchanged)                   │
│   /api/v2/demo/* ──► src/demo/router.py  (new)                     │
│                          │                                          │
│                    _load_long_term_memory()  ◄── mem0 pre-load      │
│                          │                                          │
│                    run_compliance_pipeline()                        │
│                          │                                          │
│              ┌───────────▼───────────────┐                         │
│              │   LangGraph StateGraph    │                         │
│              │   (src/demo/graph/)       │                         │
│              │                           │                         │
│              │  START                    │                         │
│              │    ▼                      │                         │
│              │  regulatory_analyst ──────┼──► MCP (filesystem)    │
│              │    ▼                      │    MCP (github)         │
│              │  policy_mapper    ────────┼──► MCP (github)         │
│              │    ▼                      │                         │
│              │  evidence_validator ──────┼──► mem0 READ            │
│              │    ▼                      │                         │
│              │  risk_scorer  ────────────┼──► mem0 WRITE           │
│              │    ▼                      │                         │
│              │  executive_reporter       │                         │
│              │    ▼                      │                         │
│              │  END                      │                         │
│              └───────────────────────────┘                         │
└──────────┬───────────────────────────────────────────────────────┬─┘
           │                                                       │
           ▼                                                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│  ChromaDB        │   │  SQLite          │   │  LangSmith (cloud)   │
│  data/mem0/      │   │  data/           │   │  + Langfuse (:3001)  │
│  (mem0 vectors)  │   │  checkpoints.db  │   │  (observability)     │
└──────────────────┘   └──────────────────┘   └──────────────────────┘
```

---

## Component Deep-Dive

### `src/demo/` — Directory Structure

```
src/demo/
├── a2a_types.py          # Pydantic A2A protocol models
├── router.py             # FastAPI router — 4 endpoints under /api/v2/demo/
│
├── agents/               # One file per LangGraph node function
│   ├── regulatory_analyst.py
│   ├── policy_mapper.py
│   ├── evidence_validator.py
│   ├── risk_scorer.py
│   └── executive_reporter.py
│
├── graph/
│   ├── state.py          # ComplianceState TypedDict
│   └── workflow.py       # StateGraph builder + run/astream entry points
│
├── memory/
│   └── mem0_client.py    # Mem0Client wrapper with graceful degradation
│
├── mcp/
│   └── client.py         # MCPClient: subprocess → disk fallback
│
└── observability/
    ├── langfuse.py        # Langfuse span wrapper (get_trace_url)
    └── terminal.py        # Rich terminal panel (optional)
```

### `src/demo/router.py` — Entry Point

Mounts at `/api/v2/demo/` in `main_simple.py`. Key behaviour:

- **Before the graph runs**, calls `_load_long_term_memory(regulation_type)` to pre-fetch prior findings from mem0 and inject them into `initial_state.long_term_context`.
- Generates a `run_id = "run-{uuid[:8]}"` used as the LangGraph `thread_id` for checkpointing.
- For `POST /run` — calls `run_compliance_pipeline(initial_state)` synchronously, serialises `a2a_tasks` to JSON, returns the full result.
- For `GET /stream` — calls `astream_compliance_pipeline(initial_state)`, yielding each node's `sse_events` as they arrive.

---

## LangGraph Workflow

### Graph Structure

```
START
  │
  ▼
regulatory_analyst  ──(error?)──► error_handler ──► END
  │
  ▼
policy_mapper       ──(error?)──► error_handler ──► END
  │
  ▼
evidence_validator  ──(error?)──► error_handler ──► END
  │
  ▼
risk_scorer         ──(error?)──► error_handler ──► END
  │
  ▼
executive_reporter
  │
  ▼
END
```

Edges between nodes use `add_conditional_edges` with `_should_continue`:

```python
def _should_continue(state: dict) -> str:
    return "error_handler" if state.get("error") else "continue"
```

If any node sets `state["error"]`, the graph short-circuits to `error_handler` which emits a `pipeline_error` SSE event and exits. The pipeline never hangs.

### Node Safety Wrapper

Every node is wrapped by `_safe_node` before being registered:

```python
def _safe_node(node_fn):
    def wrapper(state):
        try:
            return node_fn(state)
        except Exception as exc:
            return {"error": str(exc), "sse_events": [{"type": "node_error", ...}]}
    return wrapper
```

This means uncaught exceptions in an agent node write to `state.error` instead of crashing the graph.

### Short-Term Checkpointing

The workflow uses two checkpointer paths depending on caller:

**Sync path** (`run_compliance_pipeline` → `POST /run`): compiled with `SqliteSaver`:

```python
conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
graph.compile(checkpointer=checkpointer)
```

**Async SSE path** (`astream_compliance_pipeline` → `GET /stream`): compiled with `AsyncSqliteSaver` inside an async context manager:

```python
async with AsyncSqliteSaver.from_conn_string("data/checkpoints.db") as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    async for chunk in app.astream(initial_state, config=config):
        yield chunk
```

`SqliteSaver` does not support async methods — using it in `astream()` raises a `RuntimeError`. `AsyncSqliteSaver` must be used for the SSE streaming path. Both write to the same `data/checkpoints.db` file.

- Each run uses `thread_id = run_id` as its checkpoint key.
- State is persisted after every node, enabling resume-on-failure for the same `run_id`.
- Falls back to `graph.compile()` (no checkpointer) if SQLite fails to initialise.

### LLM Used

All 5 agent nodes use **GPT-4o-mini, temperature=0** via a lazy import:

```python
def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)
```

The lazy import means the demo runs (with mock fallbacks) even if `OPENAI_API_KEY` is not set — LLM errors are caught per-node and replaced with deterministic mock outputs.

---

## A2A Protocol & State

### ComplianceState

```python
class ComplianceState(TypedDict):
    regulation_type: str          # "GDPR" | "SOX" | "FINRA"
    document_path: str            # path to policy document

    # append-only — multiple nodes write without overwriting
    a2a_tasks: Annotated[list[A2ATask], operator.add]
    sse_events: Annotated[list[dict], operator.add]

    long_term_context: list[dict]  # mem0 results, loaded before graph start
    short_term_memory: dict        # managed by SqliteSaver automatically
    run_id: str
    error: str | None
```

`Annotated[list, operator.add]` is the LangGraph pattern for append-only fields. Each node returns `{"a2a_tasks": [new_task]}` and LangGraph merges them with `operator.add` — so the list grows rather than being replaced.

### A2A Task Models

```
A2ATask
  ├── task_id: str               (auto "task-{uuid[:8]}")
  ├── sender_agent: str          ("regulatory_analyst", etc.)
  ├── recipient_agent: str       ("policy_mapper", ..., "user")
  ├── state: str                 (completed | error)
  ├── artifacts: list[TaskArtifact]
  ├── mcp_calls: list[MCPCall]   (which MCP tools were invoked)
  ├── timestamp: datetime
  └── error: str | None

TaskArtifact
  ├── type: str    ("requirements_list" | "gap_analysis" |
  │                 "evidence_report" | "risk_scores" | "executive_report")
  ├── content: Any
  └── metadata: dict

MCPCall
  ├── server: str   ("filesystem" | "github")
  ├── tool: str     ("read_file" | "get_file_contents")
  └── args: dict
```

### Agent-to-Agent Handoff Pattern

Each node reads the previous node's output from `state["a2a_tasks"]` directly:

```python
# policy_mapper reads regulatory_analyst's output:
prior_tasks = state.get("a2a_tasks", [])
for artifact in prior_tasks[-1].artifacts:
    if artifact.type == "requirements_list":
        requirements = artifact.content
```

No function calls, no message queues — agents communicate through the shared state list. This is the Google A2A envelope pattern.

### Artifact Types Per Agent

| Agent | Reads artifact type | Writes artifact type |
|---|---|---|
| `regulatory_analyst` | — (reads document + regulation text via MCP) | `requirements_list` |
| `policy_mapper` | `requirements_list` | `gap_analysis` |
| `evidence_validator` | `gap_analysis` | `evidence_report` |
| `risk_scorer` | `evidence_report` | `risk_scores` |
| `executive_reporter` | all prior artifacts | `executive_report` |

---

## Memory Architecture

### Two Memory Layers

```
                    ┌─── Short-term (within-run) ───────────────────────┐
                    │                                                   │
                    │  LangGraph SqliteSaver                            │
                    │  File: data/checkpoints.db                        │
                    │  Key:  thread_id = run_id                        │
                    │  Scope: single run, auto-managed by LangGraph     │
                    │                                                   │
                    └───────────────────────────────────────────────────┘

                    ┌─── Long-term (cross-run) ──────────────────────────┐
                    │                                                   │
                    │  mem0 + ChromaDB                                  │
                    │  Vector store: data/mem0/                         │
                    │  Collection: compliance_demo                      │
                    │  user_id: "demo"                                  │
                    │                                                   │
                    │  WRITE: risk_scorer → top 5 risks (score ≥ 5.0)  │
                    │  READ:  evidence_validator (per gap query)        │
                    │  PRE-LOAD: router → loaded before graph starts    │
                    │                                                   │
                    └───────────────────────────────────────────────────┘
```

### Memory Lifecycle Per Run

```
[router.py]
  _load_long_term_memory(regulation_type)
      └── mem0.search(f"{regulation_type} prior findings")
              └── results → state.long_term_context
                      └── regulatory_analyst reads these as context in its prompt

[evidence_validator node]
  for each gap (up to 3):
      mem0.search(f"{regulation_type} {gap}", user_id="demo")
          └── prior findings surfaced → added to LLM prompt as "repeat finding" context

[risk_scorer node]
  for each risk with score ≥ 5.0 (up to 5):
      mem0.add(f"{regulation_type} critical gap: {gap}, score {score}, run_id={run_id}")
          └── persisted to ChromaDB — available to future runs
```

**Demo moment**: Run the pipeline twice on the same document. The second run's Evidence Validator will surface "Previously critical — check if mitigated" for the same gaps.

### mem0 Failure Modes

`Mem0Client` uses silent degradation — all methods return empty values on any failure:

- `init` fails → `self._memory = None`; `search()` returns `[]`, `add()` returns `False`
- `search()` raises → returns `[]`; pipeline continues without memory context
- `add()` raises → returns `False`; findings simply not stored

If `data/mem0/` contains a corrupted ChromaDB database (version mismatch causes a Rust `PanicException`), delete the directory — it is gitignored and recreates automatically on next use.

---

## MCP Integration

### MCPClient (`src/demo/mcp/client.py`)

Two-layer reliability: MCP subprocess first, disk fallback second.

```
read_file(path)
  1. _try_filesystem_mcp(path)   → checks for mcp-server-filesystem binary
                                    (currently always returns None — stub)
  2. fallback: Path(path).read_text()

get_regulation_text(regulation_type)
  1. _try_github_mcp(regulation_type)  → requires GITHUB_PERSONAL_ACCESS_TOKEN
                                          + GITHUB_REPO env vars
                                          (currently always returns None — stub)
  2. fallback: data/regulations/{REGULATION_TYPE}.txt
```

**Current state**: Both MCP subprocess methods are stubs that return `None`, so disk/bundled files are always used. The `MCPCall` records are still appended to `A2ATask.mcp_calls` for full traceability in the UI — showing which MCP tools *would* be called in production.

### Bundled Regulation Files

```
data/regulations/
  GDPR.txt      # GDPR key articles reference text
  SOX.txt       # SOX section summaries
  FINRA.txt     # FINRA rule summaries
```

These are the fallback when GitHub MCP is unavailable. The Regulatory Analyst uses the first 2000 chars as regulation context in its LLM prompt.

### Activating Real MCP

Set these env vars to enable GitHub MCP:

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
GITHUB_REPO=intersoft-consulting/gdpr-checklist   # or any public regulation repo
```

When set, `_try_github_mcp` will attempt the GitHub MCP subprocess. Replace the stub body in `client.py` with a proper stdio JSON-RPC client for production use.

---

## Observability

### LangSmith (cloud tracing)

LangGraph auto-traces all runs when `LANGSMITH_TRACING=true` is set. No code changes needed:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_ORG_ID=<your-org-uuid>    # from LangSmith → Settings → Organization
LANGCHAIN_PROJECT=enterprise-compliance-demo
```

> **Note:** LangSmith SDK v0.7+ uses `LANGSMITH_TRACING` and `LANGSMITH_API_KEY`. The legacy `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` names still work but are deprecated — use the new names to avoid silent failures.

`LANGSMITH_ORG_ID` is needed to construct correct project URLs (e.g. `smith.langchain.com/o/<org-id>/projects/p/...`). Without it the `executive_reporter` emits a bare `https://smith.langchain.com` URL with no deep link.

The `executive_reporter` node constructs the project URL and emits it as a `trace_urls.langsmith` field in the final SSE event + `executive_report` artifact. The frontend displays it as a clickable link after the run completes.

### Langfuse (self-hosted)

Runs as a Docker service on port 3001. No external account needed. The `src/demo/observability/langfuse.py` module provides `get_trace_url(run_id)` which returns the local trace URL.

Start via Docker Compose:

```bash
docker-compose up -d langfuse-db langfuse
# UI at http://localhost:3001
# Default credentials: admin / admin
```

For Langfuse tracing, set:

```bash
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=demo
LANGFUSE_SECRET_KEY=demo
```

### What to look for in traces

| In LangSmith | In Langfuse |
|---|---|
| Token count per agent node | Per-agent latency breakdown |
| Full prompt sent to GPT-4o-mini | Memory read/write events as custom spans |
| JSON parse success / fallback path taken | Cost per node |
| Retry count if LLM rate-limited | Trace timeline across all 5 nodes |

---

## API Endpoints

All mounted at `/api/v2/demo/` in `main_simple.py`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v2/demo/health` | Health check — returns `{"status": "ok", "version": "v2", "features": [...]}` |
| `GET` | `/api/v2/demo/agents` | Returns list of 5 `AgentCard` objects for A2A discovery |
| `POST` | `/api/v2/demo/run` | Run full pipeline synchronously. Body: `{regulation_type?, document_path?}`. Returns `{run_id, a2a_tasks, sse_events, error}` |
| `GET` | `/api/v2/demo/stream` | SSE stream. Query: `?regulation_type=GDPR&document_path=...`. Yields `AgentEvent` objects per node |

### POST /run Request Body

All fields have defaults — empty body `{}` is valid.

```json
{
  "regulation_type": "GDPR",       // default "GDPR" | "SOX" | "FINRA"
  "document_path": "/path/to/doc", // default: data/samples/gdpr_policy_sample.txt
  "document_id": "DOC-xxx"         // alternative: reference an uploaded v1 document
}
```

### AgentCard (GET /agents)

```json
[
  {
    "name": "regulatory_analyst",
    "description": "Extracts regulatory requirements from policy documents using RAG + MCP",
    "capabilities": ["rag", "mcp_filesystem", "mcp_github", "langfuse_traced"],
    "input_schema": {"document_path": "str", "regulation_type": "str"},
    "output_schema": {"requirements_list": "list[str]"}
  },
  ...
]
```

---

## SSE Streaming

### Server (`GET /api/v2/demo/stream`)

Uses `sse_starlette.sse.EventSourceResponse`. The async generator yields one SSE event per agent node as the graph streams:

```python
async for chunk in astream_compliance_pipeline(initial_state):
    for sse_event in chunk.get("sse_events", []):
        yield {"event": sse_event["type"], "data": json.dumps(sse_event)}
```

A `start` event is sent immediately; a `done` event closes the stream.

### SSE Event Shape

```typescript
// agent progress (nodes 1-4)
{ type: "agent_update", agent: "regulatory_analyst", status: "completed",
  task_id: "task-abc123", summary: "Extracted 5 requirements" }

// memory activity (evidence_validator)
{ type: "agent_update", agent: "evidence_validator",
  memory_hits: 2, summary: "Validated 3 gaps, 2 memory hits" }

// memory write (risk_scorer)
{ type: "agent_update", agent: "risk_scorer",
  memory_writes: 3, summary: "Scored 3 risks, stored 3 to memory" }

// final event (executive_reporter)
{ type: "run_complete", agent: "executive_reporter",
  trace_urls: { langsmith: "https://...", langfuse: "http://localhost:3001/..." } }

// on error (any node)
{ type: "pipeline_error", agent: "error_handler", message: "..." }
```

### Frontend Hook (`useAgentStream.ts`)

Opens an `EventSource` against `/api/v2/demo/stream`, parses events, and updates `agentStatuses` and `traceUrls` in React state. The `AgentDemo.tsx` page renders status badges per agent and a scrolling event log.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| LLM call fails (no API key, rate limit) | Each node catches the exception and returns a deterministic mock result. Pipeline continues. |
| Node throws an uncaught exception | `_safe_node` wrapper catches it, writes to `state.error`, routes to `error_handler`. |
| `error_handler` node activates | Emits `pipeline_error` SSE event with the error message. Graph exits cleanly. |
| MCP subprocess unavailable | `MCPClient` returns `None` from subprocess attempt, falls back to disk read silently. |
| mem0 / ChromaDB unavailable | `Mem0Client` returns `[]` / `False` on all calls. Pipeline continues without memory. |
| SQLite checkpointer fails | `workflow.py` catches the init exception and compiles without a checkpointer. |
| SSE client disconnects | `asyncio.CancelledError` is caught in the event generator; generator exits cleanly. |

---

## Environment Variables

Only `OPENAI_API_KEY` is required for real LLM calls. Everything else degrades gracefully.

```bash
# Required for real LLM calls (all 5 agents use GPT-4o-mini)
OPENAI_API_KEY=sk-...

# Optional: LangSmith cloud tracing (v0.7+ env var names)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_ORG_ID=<your-org-uuid>
LANGCHAIN_PROJECT=enterprise-compliance-demo

# Optional: Langfuse local tracing (needs Docker services running)
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=demo
LANGFUSE_SECRET_KEY=demo

# Optional: GitHub MCP (activate real MCP subprocess)
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
GITHUB_REPO=intersoft-consulting/gdpr-checklist
```

---

## How to Run the Demo

### Prerequisites

- Python 3.11+ with `venv` activated and `pip install -r requirements.txt`
- Node.js 18+ (`cd frontend && npm install --legacy-peer-deps`)
- Docker Desktop running (for Langfuse observability — optional but recommended)
- `OPENAI_API_KEY` set in `.env`

### Quickstart (all services)

```bash
# Start everything: Docker infra + backend + frontend
make demo

# Services started:
#   PostgreSQL :5432, Redis :6379, ChromaDB :8000 (Docker)
#   Langfuse DB :5433, Langfuse UI :3001 (Docker)
#   FastAPI backend :8001 (local)
#   React frontend :3000 (local)
```

Open:
- **Frontend demo page**: http://localhost:3000/demo
- **API docs (Swagger)**: http://localhost:8001/docs
- **Langfuse UI**: http://localhost:3001

### Local dev only (no Docker)

```bash
source venv/bin/activate
python -m uvicorn src.api.main_simple:app --port 8001 --reload
# in another terminal:
cd frontend && REACT_APP_API_URL=http://localhost:8001 npm start
```

The demo runs without Docker — mem0 uses local ChromaDB (`data/mem0/`), Langfuse traces are skipped.

### Stop everything

```bash
make demo-stop
```

### Smoke test (validates real LLM pipeline, ~30s)

```bash
make smoke
# or:
source venv/bin/activate && python scripts/demo_smoke_test.py
```

Runs 16 checks: A2A types, MCP client, mem0, workflow compilation, full pipeline with real LLM calls, and API endpoints. Exit code 0 = all passed.

---

## Demo Walkthrough Script

**Audience:** Engineers, technical stakeholders  
**Time:** ~5 minutes  
**Prerequisites:** `make demo` started, browser open at http://localhost:3000/demo

---

### Step 1 — Orient (30s)

Point to the **Agent Cards** on the left: 5 agents, each with capabilities listed. Explain:

> "These are the same 5 compliance agents as the v1 system. In v2 they're LangGraph nodes that communicate via A2A protocol — structured task envelopes instead of direct calls."

Point to the **regulation selector** (top bar) and the **"Use sample GDPR doc"** toggle.

---

### Step 2 — First run (90s)

1. Select **GDPR** regulation, leave "Use sample GDPR doc" on.
2. Click **Run**.
3. Watch the agent status badges light up left-to-right as SSE events arrive.
4. Point out the event log on the right — each line is an A2A Task or MCP call:
   > "See the MCP calls? The Regulatory Analyst is reading the document via filesystem MCP, then fetching GDPR article text via GitHub MCP."
5. When Evidence Validator runs, point to the memory line:
   > "No prior memory — this is the first run. It still validates the gaps but has no prior context."
6. When Risk Scorer runs:
   > "Risk Scorer is scoring each gap and writing the critical ones to mem0 long-term memory."
7. Run completes. Point to the executive summary.

---

### Step 3 — Observability (60s)

Click the **LangSmith trace link** (appears in bottom bar after run):

> "Every LLM call — prompt, response, token count, latency — is captured here. You can see exactly what each agent sent to GPT-4o-mini."

Click the **Langfuse link** (http://localhost:3001):

> "Langfuse shows per-agent latency and cost. The memory read/write events are tracked as custom spans — you can see the exact moment mem0 was queried."

---

### Step 4 — Memory demo moment (60s)

Back in the frontend, click **Run** again (same document, same regulation).

When Evidence Validator runs, point to the event log:

> "Now watch — memory hits. The Evidence Validator found 2 prior findings in mem0. These are the gaps the Risk Scorer flagged last run. It's now prompting the LLM with: 'These were previously critical — verify if mitigated.'"

When the run completes, compare the executive summary to the first run — the tone should reference repeat findings.

---

### Step 5 — Real document (optional, 60s)

1. Navigate to the Documents page (`/documents`), upload any PDF or text policy document.
2. Return to `/demo`, use the **document picker** to select the uploaded doc.
3. Run — the pipeline will analyse the real document through the same 5-agent pipeline.

---

### Cleanup

```bash
make demo-stop        # stops Docker services + kills local processes
make clean            # removes __pycache__, .pytest_cache, checkpoints.db
```

To reset memory for a clean demo:

```bash
rm -rf data/mem0/ data/checkpoints.db
```

---

## Eval Suite

The `evals/` directory contains a LangSmith Evaluations API suite that measures pipeline quality automatically.

### Directory Structure

```
evals/
  __init__.py          # package marker
  dataset.py           # seeds the LangSmith dataset (3 examples: GDPR x2, SOX x1)
  judges.py            # 5 evaluator functions (4 heuristic + 1 LLM-as-judge)
  run_evals.py         # CLI runner — prints score table + saves JSON to evals/results/
  results/             # timestamped JSON results (gitignored)
```

### Evaluators

| Evaluator | Type | Threshold | What it checks |
|---|---|---|---|
| `pipeline_completeness` | Heuristic | 1.0 | All 5 agents ran; no artifact has `metadata.mock=true` |
| `requirements_extracted` | Heuristic | 1.0 | `regulatory_analyst` produced ≥ 3 items with `Art.` / `Section` / `Rule` refs |
| `gaps_identified` | Heuristic | 1.0 | `policy_mapper` produced ≥ 1 non-empty gap string |
| `risk_scores_valid` | Heuristic | 1.0 | All `risk_scorer` risks have `risk_score ∈ [1,10]` and `priority ∈ {critical,high,medium,low}` |
| `report_coherence` | LLM-as-judge | 0.7 | GPT-4o-mini rates 1–5 whether the executive report addresses identified gaps; normalised to 0.0–1.0 |

### LangSmith Dataset

The dataset `compliance-demo-eval` contains 3 examples seeded by `evals/dataset.py`:

1. **GDPR full** — references the bundled `data/samples/gdpr_policy_sample.txt`
2. **GDPR minimal** — inline text of a thin policy missing Art.17 (erasure) and Art.30 (records)
3. **SOX financial** — inline text of a controls policy missing segregation of duties

`seed_dataset()` is idempotent — it checks for an existing dataset before creating.

### Running

```bash
# Full eval run (real LLM calls, ~2 min) — results in LangSmith Experiments tab
python evals/run_evals.py

# Unit tests for judge logic (no LLM, ~0.02s)
python -m pytest tests/test_judges.py -v

# Full eval as a pytest CI gate (slow — marked @pytest.mark.eval)
python -m pytest tests/test_evals.py -m eval -v

# Skip slow evals in fast CI
python -m pytest tests/ -m "not eval" -v
```

### Pydantic Serialisation Note

LangSmith passes `run.outputs` verbatim to evaluators. The pipeline returns `A2ATask` Pydantic objects in `a2a_tasks`, which evaluators receive as opaque Python objects — not dicts. `run_evals.py` serialises them before returning:

```python
serialized[k] = [
    item.model_dump(mode="json") if isinstance(item, BaseModel) else item
    for item in v
]
```

Without this, all heuristic judges would fail with `AttributeError: 'A2ATask' object has no attribute 'get'`.

---

## Testing

| Command | What it covers |
|---|---|
| `python -m pytest tests/test_demo_graph.py -v` | A2A types, `ComplianceState`, mem0 client, MCP client, all 5 node functions, workflow compilation and E2E with mocked LLM (24 tests) |
| `python -m pytest tests/test_demo_api.py -v` | All 4 HTTP endpoints via FastAPI `TestClient` with mocked pipeline (5 tests) |
| `python -m pytest tests/test_judges.py -v` | 11 unit tests for all heuristic judge functions — no LLM calls, runs in ~0.02s |
| `python -m pytest tests/test_evals.py -m eval -v` | Full LangSmith eval suite CI gate — real LLM calls, ~2 min, asserts all 5 thresholds |
| `make smoke` | Full pipeline with real LLM calls — 16 checks including per-agent artifact shape, SSE event count, runtime threshold (≤ 60s) |
| `python evals/run_evals.py` | Interactive eval run — prints score table, saves JSON to `evals/results/`, creates LangSmith Experiment |

Run all fast tests (no LLM, no eval) together via:

```bash
python -m pytest tests/ -m "not eval" -v
```

> **Note:** Run `test_demo_api.py` and `test_demo_graph.py` in the same `pytest tests/` invocation (not as separate `pytest file1 file2` arguments) to avoid a test isolation issue with the FastAPI `TestClient` fixture leaving module-level state.
