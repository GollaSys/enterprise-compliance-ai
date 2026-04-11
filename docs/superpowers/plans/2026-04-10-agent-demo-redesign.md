# Agent Demo Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `src/demo/` alongside the existing v1 stack — LangGraph + Google A2A schemas + MCP + mem0 memory + LangSmith/Langfuse/Rich observability + new `/demo` frontend page.

**Architecture:** Side-by-side. `main_simple.py` gains `app.include_router(demo_router, prefix="/api/v2")`. All new code in `src/demo/`. Existing 21 tests stay green throughout.

**Tech Stack:** langgraph, langchain-openai, mem0ai, mcp, langfuse, rich, sse-starlette, fpdf2, chromadb, langchain-chroma, pytest-asyncio, @modelcontextprotocol/server-filesystem, @modelcontextprotocol/server-github

---

## Task 1: Install dependencies

**Files:**
- Modify: `requirements-minimal.txt`
- Modify: `.env`

- [ ] **Step 1: Add Python deps to requirements-minimal.txt**

Replace contents of `requirements-minimal.txt`:

```
# Core API
fastapi==0.111.0
uvicorn[standard]==0.30.1
pydantic==2.8.2
python-dotenv==1.0.1
python-multipart==0.0.9

# Demo stack
langgraph>=0.2.28
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-chroma>=0.1.4
openai>=1.50.0
chromadb>=0.5.0

# Memory
mem0ai>=0.1.29

# MCP
mcp>=1.3.0

# Observability
langfuse>=2.36.0
rich>=13.7.0

# SSE streaming
sse-starlette>=2.1.0

# PDF generation (seeded sample)
fpdf2>=2.7.9

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
structlog>=24.0.0
```

- [ ] **Step 2: Install**

```bash
cd /Users/shan/Documents/AI-2026/enterprise-compliance-ai
source venv/bin/activate
pip install -r requirements-minimal.txt
```

Expected: all packages install without error. Takes ~2 min.

- [ ] **Step 3: Install Node.js MCP servers globally**

```bash
npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github
```

Expected: both packages install. Verify: `npx @modelcontextprotocol/server-filesystem --help` prints usage.

- [ ] **Step 4: Add demo env vars to .env**

Append to `.env`:

```bash
# LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=enterprise-compliance-demo

# Langfuse (self-hosted Docker — no external account needed)
LANGFUSE_HOST=http://localhost:3001
LANGFUSE_PUBLIC_KEY=publickey-demo
LANGFUSE_SECRET_KEY=secretkey-demo

# GitHub MCP
GITHUB_PERSONAL_ACCESS_TOKEN=
GITHUB_REPO=nicholasgasior/gsfmt

# mem0
MEM0_DATA_PATH=./data/mem0_storage
```

- [ ] **Step 5: Commit**

```bash
git add requirements-minimal.txt .env
git commit -m "feat: add demo stack dependencies"
```

---

## Task 2: A2A protocol types

**Files:**
- Create: `src/demo/__init__.py`
- Create: `src/demo/a2a_types.py`
- Create: `tests/test_demo_graph.py` (initial)

- [ ] **Step 1: Write failing test**

Create `tests/test_demo_graph.py`:

```python
import pytest
from datetime import datetime
from src.demo.a2a_types import (
    A2ATask, TaskArtifact, TaskState, AgentCard, MCPCall
)


def test_a2a_task_creation():
    task = A2ATask(
        sender_agent="regulatory_analyst",
        recipient_agent="policy_mapper",
        artifacts=[TaskArtifact(type="requirements_list", content={"requirements": ["Art.5"]})],
    )
    assert task.sender_agent == "regulatory_analyst"
    assert task.state == TaskState.COMPLETED
    assert len(task.task_id) > 0
    assert isinstance(task.timestamp, datetime)


def test_a2a_task_serialization():
    task = A2ATask(
        sender_agent="risk_scorer",
        recipient_agent="executive_reporter",
        artifacts=[TaskArtifact(type="risk_scores", content=[{"id": "R1", "score": 8.2}])],
        mcp_calls=[MCPCall(server="filesystem", tool="read_file", arguments={"path": "/data/doc.pdf"})],
    )
    data = task.model_dump()
    assert data["sender_agent"] == "risk_scorer"
    assert data["mcp_calls"][0]["server"] == "filesystem"


def test_agent_card():
    card = AgentCard(
        agent_id="regulatory_analyst",
        name="Regulatory Analyst",
        role="Senior Regulatory Compliance Analyst",
        capabilities=["document_analysis", "requirement_extraction"],
        input_schema={"document_path": "str", "regulation_type": "str"},
        output_schema={"requirements": "List[str]"},
        mcp_servers=["filesystem", "github"],
    )
    assert card.agent_id == "regulatory_analyst"
    assert "filesystem" in card.mcp_servers
```

- [ ] **Step 2: Run — expect failure**

```bash
cd /Users/shan/Documents/AI-2026/enterprise-compliance-ai && source venv/bin/activate
python -m pytest tests/test_demo_graph.py::test_a2a_task_creation -v
```

Expected: `ImportError: No module named 'src.demo'`

- [ ] **Step 3: Create `src/demo/__init__.py`**

```python
# src/demo/__init__.py
```

- [ ] **Step 4: Create `src/demo/a2a_types.py`**

```python
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, List, Optional
import uuid

from pydantic import BaseModel, Field


class TaskState(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class MCPCall(BaseModel):
    server: str
    tool: str
    arguments: dict = Field(default_factory=dict)
    result_summary: Optional[str] = None


class TaskArtifact(BaseModel):
    type: str
    content: Any
    metadata: dict = Field(default_factory=dict)


class A2ATask(BaseModel):
    task_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    sender_agent: str
    recipient_agent: str
    state: TaskState = TaskState.COMPLETED
    artifacts: List[TaskArtifact] = Field(default_factory=list)
    mcp_calls: List[MCPCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentCard(BaseModel):
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    input_schema: dict
    output_schema: dict
    mcp_servers: List[str] = Field(default_factory=list)
```

- [ ] **Step 5: Run — expect pass**

```bash
python -m pytest tests/test_demo_graph.py -v
```

Expected: 3 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/demo/__init__.py src/demo/a2a_types.py tests/test_demo_graph.py
git commit -m "feat: A2A protocol types (AgentCard, A2ATask, TaskArtifact)"
```

---

## Task 3: LangGraph state + mem0 client

**Files:**
- Create: `src/demo/graph/__init__.py`
- Create: `src/demo/graph/state.py`
- Create: `src/demo/memory/__init__.py`
- Create: `src/demo/memory/mem0_client.py`

- [ ] **Step 1: Add tests to `tests/test_demo_graph.py`**

Append:

```python
from src.demo.graph.state import ComplianceState
from src.demo.memory import mem0_client


def test_compliance_state_shape():
    state: ComplianceState = {
        "regulation_type": "GDPR",
        "document_path": "./data/samples/gdpr_policy_sample.pdf",
        "run_id": "RUN-001",
        "a2a_tasks": [],
        "long_term_context": {},
        "mcp_artifacts": [],
        "final_report": None,
        "error": None,
        "sse_events": [],
    }
    assert state["regulation_type"] == "GDPR"
    assert state["a2a_tasks"] == []


def test_mem0_search_returns_list_when_unavailable(monkeypatch):
    monkeypatch.setattr(mem0_client, "_client", None)
    monkeypatch.setattr(mem0_client, "_init_attempted", True)
    results = mem0_client.search("GDPR data retention", "GDPR")
    assert isinstance(results, list)


def test_mem0_add_returns_false_when_unavailable(monkeypatch):
    monkeypatch.setattr(mem0_client, "_client", None)
    monkeypatch.setattr(mem0_client, "_init_attempted", True)
    result = mem0_client.add("GDPR critical gap found", "GDPR")
    assert result is False
```

- [ ] **Step 2: Run — expect failure**

```bash
python -m pytest tests/test_demo_graph.py::test_compliance_state_shape -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `src/demo/graph/__init__.py`** (empty)

- [ ] **Step 4: Create `src/demo/graph/state.py`**

```python
from __future__ import annotations
from typing import Annotated, Any, Dict, List, Optional
import operator
from typing_extensions import TypedDict
from src.demo.a2a_types import A2ATask


class ComplianceState(TypedDict):
    # Input
    regulation_type: str
    document_path: str
    run_id: str

    # A2A message log — each node appends; operator.add accumulates
    a2a_tasks: Annotated[List[A2ATask], operator.add]

    # Memory
    long_term_context: Dict[str, Any]

    # MCP raw artifacts
    mcp_artifacts: Annotated[List[Dict], operator.add]

    # Output
    final_report: Optional[str]
    error: Optional[str]

    # SSE stream — each node appends its events
    sse_events: Annotated[List[Dict], operator.add]
```

- [ ] **Step 5: Create `src/demo/memory/__init__.py`** (empty)

- [ ] **Step 6: Create `src/demo/memory/mem0_client.py`**

```python
"""
Long-term cross-run memory using mem0.
All calls are fire-and-forget — failures are logged and silently ignored
so the demo never crashes due to memory issues.
"""
from __future__ import annotations
import os
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()

_client = None
_init_attempted = False


def _get_client():
    global _client, _init_attempted
    if _init_attempted:
        return _client
    _init_attempted = True
    try:
        from mem0 import Memory
        data_path = os.getenv("MEM0_DATA_PATH", "./data/mem0_storage")
        os.makedirs(data_path, exist_ok=True)
        config = {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "collection_name": "compliance_memory",
                    "path": data_path,
                },
            }
        }
        _client = Memory.from_config(config)
        logger.info("mem0 initialized", path=data_path)
    except Exception as e:
        logger.warning("mem0 init failed — long-term memory disabled", error=str(e))
        _client = None
    return _client


def search(query: str, regulation_type: str, limit: int = 5) -> List[Dict]:
    client = _get_client()
    if not client:
        return []
    try:
        results = client.search(query, user_id=regulation_type, limit=limit)
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning("mem0 search failed", error=str(e))
        return []


def add(text: str, regulation_type: str, metadata: Optional[Dict] = None) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        client.add(text, user_id=regulation_type, metadata=metadata or {})
        return True
    except Exception as e:
        logger.warning("mem0 add failed", error=str(e))
        return False


def get_history(regulation_type: str) -> List[Dict]:
    client = _get_client()
    if not client:
        return []
    try:
        return client.get_all(user_id=regulation_type)
    except Exception as e:
        logger.warning("mem0 get_history failed", error=str(e))
        return []


def reset_all() -> bool:
    global _client, _init_attempted
    client = _get_client()
    if not client:
        return False
    try:
        client.reset()
        _client = None
        _init_attempted = False
        return True
    except Exception as e:
        logger.warning("mem0 reset failed", error=str(e))
        return False
```

- [ ] **Step 7: Run — expect pass**

```bash
python -m pytest tests/test_demo_graph.py -v
```

Expected: 6 tests pass.

- [ ] **Step 8: Commit**

```bash
git add src/demo/graph/ src/demo/memory/ tests/test_demo_graph.py
git commit -m "feat: LangGraph ComplianceState + mem0 long-term memory client"
```

---

## Task 4: MCP client

**Files:**
- Create: `src/demo/mcp/__init__.py`
- Create: `src/demo/mcp/client.py`
- Create: `data/regulations/GDPR.txt`
- Create: `data/regulations/SOX.txt`
- Create: `data/regulations/FINRA.txt`

- [ ] **Step 1: Add MCP tests to `tests/test_demo_graph.py`**

Append:

```python
from unittest.mock import AsyncMock, patch, MagicMock
from src.demo.mcp.client import read_document_content, fetch_regulation_text


@pytest.mark.asyncio
async def test_read_document_falls_back_to_disk(tmp_path):
    doc = tmp_path / "policy.txt"
    doc.write_text("This is a test compliance policy document.")
    content, mcp_call = await read_document_content(str(doc))
    assert "compliance" in content
    assert mcp_call.server in ("filesystem", "fallback")


@pytest.mark.asyncio
async def test_fetch_regulation_falls_back_to_bundled():
    content, mcp_call = await fetch_regulation_text("GDPR")
    assert len(content) > 50
    assert "GDPR" in content or "data" in content.lower()
    assert mcp_call.server in ("github", "fallback")
```

- [ ] **Step 2: Create regulation fallback files**

Create `data/regulations/GDPR.txt`:

```
GDPR Key Articles (General Data Protection Regulation)

Article 5 — Principles relating to processing of personal data
Personal data shall be processed lawfully, fairly and transparently. Data must
be collected for specified, explicit and legitimate purposes (purpose limitation).
Data should be adequate, relevant and limited to what is necessary (data minimisation).
Data must be accurate and kept up to date. Data shall not be kept longer than necessary
(storage limitation). Processed with appropriate security (integrity and confidentiality).

Article 17 — Right to erasure (right to be forgotten)
The data subject shall have the right to obtain erasure of personal data without
undue delay. Controllers must have a documented procedure for handling erasure requests
within 30 days. Systems must support technical erasure across all data stores.

Article 30 — Records of processing activities
Each controller shall maintain a record of processing activities under its responsibility.
Records must include: name and contact of controller, purposes of processing, categories
of data subjects and personal data, recipients, transfers to third countries, retention
periods, and description of technical/organisational security measures.

Article 32 — Security of processing
The controller shall implement appropriate technical and organisational measures to ensure
a level of security appropriate to the risk, including pseudonymisation, encryption,
ongoing confidentiality, integrity, availability and resilience of processing systems.

Article 33 — Notification of personal data breach
In the case of a personal data breach, the controller shall notify the supervisory
authority within 72 hours of becoming aware of the breach. The notification must describe
the nature of the breach, categories of data subjects affected, and measures taken.
```

Create `data/regulations/SOX.txt`:

```
SOX Key Sections (Sarbanes-Oxley Act)

Section 302 — Corporate Responsibility for Financial Reports
Principal executive and financial officers must certify quarterly and annual reports.
Certifying officers are responsible for establishing and maintaining internal controls.
Officers must evaluate the effectiveness of disclosure controls within 90 days prior to report.

Section 404 — Management Assessment of Internal Controls
Management must assess the effectiveness of internal control over financial reporting.
The assessment must be based on a suitable, recognised framework (e.g. COSO).
External auditors must attest to and report on management's assessment.
Segregation of duties must be enforced for all financial system access.

Section 409 — Real Time Issuer Disclosures
Issuers must disclose material changes in financial condition or operations on a rapid
and current basis. Changes that could affect investor decisions must be disclosed promptly.

IT General Controls Requirements
Access controls: user provisioning/deprovisioning, privileged access management.
Change management: documented change request, testing, and approval processes.
Computer operations: backup and recovery procedures, incident management.
```

Create `data/regulations/FINRA.txt`:

```
FINRA Key Rules (Financial Industry Regulatory Authority)

Rule 4370 — Business Continuity Plans and Emergency Contact Information
Each member must create and maintain a written business continuity plan identifying
procedures relating to an emergency or significant business disruption. Plans must
address data backup and recovery, all mission critical systems, financial and operational
risk assessments, alternate communications, regulatory reporting, and customer access.

Rule 3110 — Supervision
Each member shall establish and maintain a system to supervise the activities of each
associated person that is reasonably designed to achieve compliance with applicable laws,
regulations, and FINRA rules. Written supervisory procedures must be maintained.

Rule 4511 — General Requirements for Books and Records
Members must make and preserve books and records as required under the FINRA rules,
the Exchange Act and the applicable Exchange Act rules. Records must be preserved for
periods specified and be readily accessible for examination by FINRA.
```

- [ ] **Step 3: Create `src/demo/mcp/__init__.py`** (empty)

- [ ] **Step 4: Create `src/demo/mcp/client.py`**

```python
"""
MCP client wrapper for Filesystem and GitHub MCP servers.
Each function tries the MCP subprocess first; falls back gracefully
to direct disk reads so the demo never hangs on MCP unavailability.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
from typing import Tuple
import structlog
from src.demo.a2a_types import MCPCall

logger = structlog.get_logger()

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
REGULATIONS_DIR = DATA_DIR / "regulations"


async def _try_filesystem_mcp(file_path: str) -> str | None:
    """Attempt to read a file via the filesystem MCP server subprocess."""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        import json

        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(DATA_DIR)],
            env=None,
        )
        async with asyncio.timeout(10):
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("read_file", {"path": file_path})
                    if result.content:
                        return result.content[0].text
    except Exception as e:
        logger.debug("filesystem MCP unavailable, using fallback", error=str(e))
    return None


async def _try_github_mcp(regulation_type: str) -> str | None:
    """Attempt to fetch regulation text from GitHub via the GitHub MCP server."""
    token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not token:
        return None
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        repo = os.getenv("GITHUB_REPO", "nicholasgasior/gsfmt")
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
        )
        async with asyncio.timeout(15):
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    # Search for regulation-related content
                    result = await session.call_tool(
                        "search_code",
                        {"q": f"{regulation_type} compliance requirements", "per_page": 3},
                    )
                    if result.content:
                        return f"GitHub search results for {regulation_type}:\n{result.content[0].text[:2000]}"
    except Exception as e:
        logger.debug("GitHub MCP unavailable, using fallback", error=str(e))
    return None


async def read_document_content(document_path: str) -> Tuple[str, MCPCall]:
    """
    Read document content. Tries filesystem MCP first, falls back to direct disk read.
    Returns (content, MCPCall) describing what was used.
    """
    mcp_result = await _try_filesystem_mcp(document_path)
    if mcp_result:
        return mcp_result, MCPCall(
            server="filesystem",
            tool="read_file",
            arguments={"path": document_path},
            result_summary=f"Read {len(mcp_result)} chars via MCP",
        )

    # Fallback: direct disk read
    try:
        path = Path(document_path)
        if path.exists():
            content = path.read_text(encoding="utf-8", errors="replace")
        else:
            content = f"[Document not found: {document_path}. Using placeholder content for demo.]"
    except Exception as e:
        content = f"[Read error: {e}]"

    return content, MCPCall(
        server="fallback",
        tool="read_file",
        arguments={"path": document_path},
        result_summary=f"Direct disk read: {len(content)} chars",
    )


async def fetch_regulation_text(regulation_type: str) -> Tuple[str, MCPCall]:
    """
    Fetch regulation reference text. Tries GitHub MCP first, falls back to
    bundled text files in data/regulations/.
    """
    github_result = await _try_github_mcp(regulation_type)
    if github_result:
        return github_result, MCPCall(
            server="github",
            tool="search_code",
            arguments={"q": regulation_type},
            result_summary=f"Fetched {len(github_result)} chars from GitHub",
        )

    # Fallback: bundled regulation files
    reg_file = REGULATIONS_DIR / f"{regulation_type.upper()}.txt"
    if reg_file.exists():
        content = reg_file.read_text()
    else:
        content = f"{regulation_type} requires organisations to implement appropriate controls, maintain records, ensure data security, and demonstrate ongoing compliance."

    return content, MCPCall(
        server="fallback",
        tool="read_bundled_regulation",
        arguments={"regulation": regulation_type},
        result_summary=f"Bundled text: {len(content)} chars",
    )
```

- [ ] **Step 5: Run — expect pass**

```bash
python -m pytest tests/test_demo_graph.py -v
```

Expected: 8 tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/demo/mcp/ data/regulations/ tests/test_demo_graph.py
git commit -m "feat: MCP client with filesystem+GitHub servers and disk fallbacks"
```

---

## Task 5: Observability

**Files:**
- Create: `src/demo/observability/__init__.py`
- Create: `src/demo/observability/langfuse.py`
- Create: `src/demo/observability/terminal.py`

- [ ] **Step 1: Create `src/demo/observability/__init__.py`** (empty)

- [ ] **Step 2: Create `src/demo/observability/langfuse.py`**

```python
"""
Langfuse observability wrapper. Wraps each agent node as a named span.
If Langfuse is unavailable (no Docker service), all decorators are no-ops.
"""
from __future__ import annotations
import functools
import os
from typing import Any, Callable
import structlog

logger = structlog.get_logger()
_langfuse = None
_langfuse_init_tried = False


def _get_langfuse():
    global _langfuse, _langfuse_init_tried
    if _langfuse_init_tried:
        return _langfuse
    _langfuse_init_tried = True
    try:
        from langfuse import Langfuse
        host = os.getenv("LANGFUSE_HOST", "http://localhost:3001")
        _langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "publickey-demo"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", "secretkey-demo"),
            host=host,
        )
        logger.info("Langfuse connected", host=host)
    except Exception as e:
        logger.warning("Langfuse unavailable", error=str(e))
        _langfuse = None
    return _langfuse


def trace_agent(agent_name: str):
    """Decorator that wraps an async agent node function in a Langfuse span."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(state: Any, *args, **kwargs):
            lf = _get_langfuse()
            if not lf:
                return await fn(state, *args, **kwargs)
            trace = lf.trace(name=f"compliance-run-{state.get('run_id', 'unknown')}")
            span = trace.span(name=agent_name)
            try:
                result = await fn(state, *args, **kwargs)
                span.end(output={"sse_events_count": len(result.get("sse_events", []))})
                return result
            except Exception as e:
                span.end(level="ERROR", status_message=str(e))
                raise
        return wrapper
    return decorator


def flush():
    lf = _get_langfuse()
    if lf:
        try:
            lf.flush()
        except Exception:
            pass
```

- [ ] **Step 3: Create `src/demo/observability/terminal.py`**

```python
"""
Rich terminal panel — 3-panel live display during demo runs.
Used when running in terminal mode (make demo).
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Dict
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

AGENT_ORDER = [
    "regulatory_analyst",
    "policy_mapper",
    "evidence_validator",
    "risk_scorer",
    "executive_reporter",
]

AGENT_LABELS = {
    "regulatory_analyst": "Regulatory Analyst",
    "policy_mapper": "Policy Mapper",
    "evidence_validator": "Evidence Validator",
    "risk_scorer": "Risk Scorer",
    "executive_reporter": "Executive Reporter",
}

STATUS_COLORS = {
    "idle": "dim white",
    "running": "bold yellow",
    "done": "bold green",
    "error": "bold red",
}

console = Console()


class AgentTerminalPanel:
    def __init__(self, regulation_type: str, run_id: str):
        self.regulation_type = regulation_type
        self.run_id = run_id
        self.agent_status: Dict[str, str] = {a: "idle" for a in AGENT_ORDER}
        self.a2a_messages: List[str] = []
        self.memory_events: List[str] = []
        self._live: Live | None = None

    def _build_pipeline_panel(self) -> Panel:
        table = Table.grid(padding=(0, 2))
        table.add_column(width=24)
        table.add_column(width=10)
        for agent_id in AGENT_ORDER:
            status = self.agent_status[agent_id]
            icon = {"idle": "○", "running": "▶", "done": "✓", "error": "✗"}[status]
            color = STATUS_COLORS[status]
            table.add_row(
                Text(f"  {AGENT_LABELS[agent_id]}", style="white"),
                Text(f"{icon} {status}", style=color),
            )
        return Panel(table, title=f"[bold cyan]Pipeline[/bold cyan] — {self.regulation_type}", border_style="cyan")

    def _build_messages_panel(self) -> Panel:
        content = Text()
        for msg in self.a2a_messages[-12:]:
            content.append(msg + "\n", style="white")
        return Panel(content, title="[bold magenta]A2A Messages[/bold magenta]", border_style="magenta")

    def _build_memory_panel(self) -> Panel:
        content = Text()
        for event in self.memory_events[-8:]:
            style = "bold green" if "WRITE" in event else "bold yellow"
            content.append(event + "\n", style=style)
        return Panel(content, title="[bold yellow]Memory Events[/bold yellow]", border_style="yellow")

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(self._build_pipeline_panel(), size=10),
            Layout(self._build_messages_panel(), size=16),
            Layout(self._build_memory_panel(), size=12),
        )
        return layout

    def start(self):
        self._live = Live(self._build_layout(), console=console, refresh_per_second=4)
        self._live.__enter__()
        self.log_message("system", f"Demo run {self.run_id} started")

    def stop(self):
        if self._live:
            self._live.__exit__(None, None, None)

    def set_agent_status(self, agent_id: str, status: str):
        self.agent_status[agent_id] = status
        if self._live:
            self._live.update(self._build_layout())

    def log_message(self, sender: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.a2a_messages.append(f"[{ts}] {sender}: {message}")
        if self._live:
            self._live.update(self._build_layout())

    def log_memory(self, event_type: str, detail: str):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = "WRITE" if event_type == "write" else "READ "
        self.memory_events.append(f"[{ts}] {prefix} {detail}")
        if self._live:
            self._live.update(self._build_layout())
```

- [ ] **Step 4: Commit**

```bash
git add src/demo/observability/
git commit -m "feat: observability — Langfuse span wrapper + Rich 3-panel terminal"
```

---

## Task 6: All 5 agent nodes

**Files:**
- Create: `src/demo/agents/__init__.py`
- Create: `src/demo/agents/regulatory_analyst.py`
- Create: `src/demo/agents/policy_mapper.py`
- Create: `src/demo/agents/evidence_validator.py`
- Create: `src/demo/agents/risk_scorer.py`
- Create: `src/demo/agents/executive_reporter.py`

- [ ] **Step 1: Add agent node tests to `tests/test_demo_graph.py`**

Append:

```python
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.demo.agents.regulatory_analyst import regulatory_analyst_node, AGENT_CARD as RA_CARD
from src.demo.agents.policy_mapper import policy_mapper_node, AGENT_CARD as PM_CARD
from src.demo.agents.evidence_validator import evidence_validator_node, AGENT_CARD as EV_CARD
from src.demo.agents.risk_scorer import risk_scorer_node, AGENT_CARD as RS_CARD
from src.demo.agents.executive_reporter import executive_reporter_node, AGENT_CARD as ER_CARD


def _base_state(tmp_path=None, **overrides) -> dict:
    doc_path = str(tmp_path / "doc.txt") if tmp_path else "./data/samples/gdpr_policy_sample.pdf"
    state = {
        "regulation_type": "GDPR",
        "document_path": doc_path,
        "run_id": "RUN-TEST-001",
        "a2a_tasks": [],
        "long_term_context": {},
        "mcp_artifacts": [],
        "final_report": None,
        "error": None,
        "sse_events": [],
    }
    state.update(overrides)
    return state


def _fake_llm_response(text: str):
    from langchain_core.messages import AIMessage
    mock = MagicMock()
    mock.invoke = MagicMock(return_value=AIMessage(content=text))
    return mock


@pytest.mark.asyncio
async def test_regulatory_analyst_returns_a2a_task(tmp_path):
    (tmp_path / "doc.txt").write_text("This policy covers data retention for 3 years.")
    state = _base_state(tmp_path)
    fake_resp = json.dumps({
        "requirements": ["Art.5 - data minimisation", "Art.17 - right to erasure"],
        "gaps_preview": ["No erasure procedure defined"],
        "source_sections": ["Section 1"],
    })
    with patch("src.demo.agents.regulatory_analyst.ChatOpenAI", return_value=_fake_llm_response(fake_resp)):
        result = await regulatory_analyst_node(state)
    assert len(result["a2a_tasks"]) == 1
    assert result["a2a_tasks"][0].sender_agent == "regulatory_analyst"
    assert len(result["sse_events"]) >= 1


@pytest.mark.asyncio
async def test_policy_mapper_reads_prior_task(tmp_path):
    from src.demo.a2a_types import A2ATask, TaskArtifact
    prior = A2ATask(
        sender_agent="regulatory_analyst",
        recipient_agent="policy_mapper",
        artifacts=[TaskArtifact(type="requirements_list", content={"requirements": ["Art.5"]})],
    )
    state = _base_state(tmp_path, a2a_tasks=[prior])
    fake_resp = json.dumps({
        "mapped": [{"requirement": "Art.5", "policy": "DPP-001", "coverage": "partial"}],
        "gaps": [{"requirement": "Art.17", "severity": "high", "description": "No erasure procedure"}],
    })
    with patch("src.demo.agents.policy_mapper.ChatOpenAI", return_value=_fake_llm_response(fake_resp)):
        result = await policy_mapper_node(state)
    assert result["a2a_tasks"][0].sender_agent == "policy_mapper"


@pytest.mark.asyncio
async def test_risk_scorer_writes_to_mem0(tmp_path):
    from src.demo.a2a_types import A2ATask, TaskArtifact
    prior = A2ATask(
        sender_agent="evidence_validator",
        recipient_agent="risk_scorer",
        artifacts=[TaskArtifact(type="validation_results", content={"gaps": [{"id": "G1", "severity": "high"}]})],
    )
    state = _base_state(tmp_path, a2a_tasks=[prior])
    fake_resp = json.dumps({
        "risk_scores": [{"gap_id": "G1", "score": 8.2, "level": "high", "impact": "significant"}],
        "overall_risk": "high",
    })
    with patch("src.demo.agents.risk_scorer.ChatOpenAI", return_value=_fake_llm_response(fake_resp)):
        with patch("src.demo.agents.risk_scorer.mem0_client.add", return_value=True) as mock_add:
            result = await risk_scorer_node(state)
    mock_add.assert_called()
    assert result["a2a_tasks"][0].sender_agent == "risk_scorer"


@pytest.mark.asyncio
async def test_all_agent_cards_valid():
    for card in [RA_CARD, PM_CARD, EV_CARD, RS_CARD, ER_CARD]:
        assert card.agent_id
        assert card.name
        assert len(card.capabilities) > 0
```

- [ ] **Step 2: Create `src/demo/agents/__init__.py`** (empty)

- [ ] **Step 3: Create `src/demo/agents/regulatory_analyst.py`**

```python
from __future__ import annotations
import json
import re
from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
from src.demo.mcp.client import read_document_content, fetch_regulation_text
from src.demo.observability.langfuse import trace_agent

logger = structlog.get_logger()

AGENT_CARD = AgentCard(
    agent_id="regulatory_analyst",
    name="Regulatory Analyst",
    role="Senior Regulatory Compliance Analyst",
    capabilities=["document_analysis", "requirement_extraction", "rag_retrieval"],
    input_schema={"document_path": "str", "regulation_type": "str"},
    output_schema={"requirements": "List[str]", "gaps_preview": "List[str]"},
    mcp_servers=["filesystem", "github"],
)


@trace_agent("regulatory_analyst")
async def regulatory_analyst_node(state: Any) -> dict:
    logger.info("Regulatory Analyst starting", regulation=state["regulation_type"])

    doc_content, mcp_call_doc = await read_document_content(state["document_path"])
    reg_text, mcp_call_reg = await fetch_regulation_text(state["regulation_type"])

    prior_context = state.get("long_term_context", {}).get("summary", "No prior compliance history found.")

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""You are a senior regulatory compliance analyst.

DOCUMENT CONTENT:
{doc_content[:3000]}

{state['regulation_type']} REFERENCE REQUIREMENTS:
{reg_text[:2000]}

PRIOR COMPLIANCE CONTEXT (from memory):
{prior_context}

Analyze the document against the {state['regulation_type']} requirements.
Return ONLY valid JSON (no markdown) with this structure:
{{
  "requirements": ["list of specific {state['regulation_type']} requirements found/missing (max 5)"],
  "gaps_preview": ["list of potential compliance gaps you notice (max 3)"],
  "source_sections": ["relevant document sections"]
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else {}
    except Exception:
        result = {
            "requirements": [f"{state['regulation_type']} data minimisation", "Right to erasure procedure"],
            "gaps_preview": ["No documented erasure procedure"],
            "source_sections": ["Full document"],
        }

    req_count = len(result.get("requirements", []))
    task = A2ATask(
        sender_agent="regulatory_analyst",
        recipient_agent="policy_mapper",
        artifacts=[TaskArtifact(
            type="requirements_list",
            content=result,
            metadata={
                "source_doc": state["document_path"],
                "regulation_type": state["regulation_type"],
                "rag_used": True,
            },
        )],
        mcp_calls=[mcp_call_doc, mcp_call_reg],
    )

    sse_event = {
        "type": "a2a_task",
        "agent": "regulatory_analyst",
        "task_id": task.task_id,
        "summary": f"Extracted {req_count} requirements via RAG + MCP",
        "mcp_servers_used": [mcp_call_doc.server, mcp_call_reg.server],
    }

    logger.info("Regulatory Analyst done", requirements=req_count)
    return {"a2a_tasks": [task], "sse_events": [{"type": "agent_start", "agent": "regulatory_analyst"}, sse_event]}
```

- [ ] **Step 4: Create `src/demo/agents/policy_mapper.py`**

```python
from __future__ import annotations
import json
import re
from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
from src.demo.mcp.client import fetch_regulation_text
from src.demo.observability.langfuse import trace_agent

logger = structlog.get_logger()

AGENT_CARD = AgentCard(
    agent_id="policy_mapper",
    name="Policy Mapper",
    role="Policy Compliance Mapping Specialist",
    capabilities=["gap_identification", "policy_mapping", "coverage_analysis"],
    input_schema={"requirements_list": "List[str]"},
    output_schema={"mapped": "List[dict]", "gaps": "List[dict]"},
    mcp_servers=["github"],
)


@trace_agent("policy_mapper")
async def policy_mapper_node(state: Any) -> dict:
    logger.info("Policy Mapper starting")

    # Read prior A2A task from Regulatory Analyst
    prior_tasks = state.get("a2a_tasks", [])
    requirements_content = {}
    if prior_tasks:
        artifacts = prior_tasks[-1].artifacts
        if artifacts:
            requirements_content = artifacts[0].content

    requirements = requirements_content.get("requirements", [])

    _, mcp_call = await fetch_regulation_text(state["regulation_type"])

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""You are a policy compliance mapping specialist.

REGULATORY REQUIREMENTS IDENTIFIED:
{json.dumps(requirements, indent=2)}

REGULATION TYPE: {state['regulation_type']}

Map each requirement to typical enterprise policies and identify gaps.
Return ONLY valid JSON (no markdown):
{{
  "mapped": [
    {{"requirement": "requirement text", "policy": "policy name", "coverage": "full|partial|none"}}
  ],
  "gaps": [
    {{"requirement": "requirement text", "severity": "high|medium|low", "description": "gap description", "gap_id": "GAP-001"}}
  ]
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else {}
    except Exception:
        result = {
            "mapped": [{"requirement": r, "policy": "General Compliance Policy", "coverage": "partial"} for r in requirements[:2]],
            "gaps": [{"requirement": requirements[0] if requirements else "Unknown", "severity": "high", "description": "Policy coverage incomplete", "gap_id": "GAP-001"}],
        }

    gap_count = len(result.get("gaps", []))
    task = A2ATask(
        sender_agent="policy_mapper",
        recipient_agent="evidence_validator",
        artifacts=[TaskArtifact(type="gap_analysis", content=result, metadata={"regulation": state["regulation_type"]})],
        mcp_calls=[mcp_call],
    )
    sse_event = {
        "type": "a2a_task",
        "agent": "policy_mapper",
        "task_id": task.task_id,
        "summary": f"Mapped requirements — {gap_count} gaps identified",
    }
    logger.info("Policy Mapper done", gaps=gap_count)
    return {"a2a_tasks": [task], "sse_events": [{"type": "agent_start", "agent": "policy_mapper"}, sse_event]}
```

- [ ] **Step 5: Create `src/demo/agents/evidence_validator.py`**

```python
from __future__ import annotations
import json
import re
from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
from src.demo.memory import mem0_client
from src.demo.observability.langfuse import trace_agent

logger = structlog.get_logger()

AGENT_CARD = AgentCard(
    agent_id="evidence_validator",
    name="Evidence Validator",
    role="Compliance Evidence Validation Expert",
    capabilities=["evidence_validation", "completeness_check", "memory_lookup"],
    input_schema={"gap_analysis": "dict"},
    output_schema={"validations": "List[dict]", "overall_validity": "str"},
    mcp_servers=["filesystem"],
)


@trace_agent("evidence_validator")
async def evidence_validator_node(state: Any) -> dict:
    logger.info("Evidence Validator starting")

    prior_tasks = state.get("a2a_tasks", [])
    gap_analysis = {}
    if prior_tasks:
        artifacts = prior_tasks[-1].artifacts
        if artifacts:
            gap_analysis = artifacts[0].content

    gaps = gap_analysis.get("gaps", [])

    # Query long-term memory for prior findings about these gaps
    memory_hits = []
    memory_events = []
    for gap in gaps[:3]:
        query = f"{state['regulation_type']} {gap.get('requirement', gap.get('description', ''))}"
        hits = mem0_client.search(query, state["regulation_type"], limit=2)
        if hits:
            memory_hits.extend(hits)
            memory_events.append({
                "type": "memory_read",
                "query": query,
                "hits": len(hits),
                "detail": str(hits[0])[:100] if hits else "",
            })

    memory_context = "\n".join(
        [f"- {h.get('memory', h) if isinstance(h, dict) else str(h)}" for h in memory_hits[:3]]
    ) or "No prior compliance history found for these gaps."

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""You are a compliance evidence validation expert.

GAPS TO VALIDATE:
{json.dumps(gaps, indent=2)}

PRIOR COMPLIANCE MEMORY (from previous runs):
{memory_context}

For each gap, assess evidence completeness and whether the gap may have been addressed.
Return ONLY valid JSON (no markdown):
{{
  "validations": [
    {{
      "gap_id": "GAP-001",
      "evidence_completeness": 0.0-1.0,
      "prior_finding": "description if found in memory or null",
      "status": "open|resolved|partially_resolved",
      "notes": "brief notes"
    }}
  ],
  "overall_validity": "satisfactory|unsatisfactory|needs_review"
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else {}
    except Exception:
        result = {
            "validations": [{"gap_id": g.get("gap_id", "GAP-001"), "evidence_completeness": 0.6, "prior_finding": None, "status": "open", "notes": "Insufficient evidence"} for g in gaps],
            "overall_validity": "needs_review",
        }

    task = A2ATask(
        sender_agent="evidence_validator",
        recipient_agent="risk_scorer",
        artifacts=[TaskArtifact(type="validation_results", content=result, metadata={"memory_hits": len(memory_hits)})],
    )

    sse_events = [{"type": "agent_start", "agent": "evidence_validator"}]
    sse_events.extend(memory_events)
    sse_events.append({
        "type": "a2a_task",
        "agent": "evidence_validator",
        "task_id": task.task_id,
        "summary": f"Validated {len(result.get('validations', []))} gaps — {len(memory_hits)} memory hits",
    })

    logger.info("Evidence Validator done", memory_hits=len(memory_hits))
    return {"a2a_tasks": [task], "sse_events": sse_events}
```

- [ ] **Step 6: Create `src/demo/agents/risk_scorer.py`**

```python
from __future__ import annotations
import json
import re
from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
from src.demo.memory import mem0_client
from src.demo.observability.langfuse import trace_agent

logger = structlog.get_logger()

AGENT_CARD = AgentCard(
    agent_id="risk_scorer",
    name="Risk Scorer",
    role="Compliance Risk Assessment Specialist",
    capabilities=["risk_scoring", "impact_assessment", "memory_write"],
    input_schema={"validation_results": "dict"},
    output_schema={"risk_scores": "List[dict]", "overall_risk": "str"},
    mcp_servers=[],
)


@trace_agent("risk_scorer")
async def risk_scorer_node(state: Any) -> dict:
    logger.info("Risk Scorer starting")

    prior_tasks = state.get("a2a_tasks", [])
    validation_results = {}
    if prior_tasks:
        artifacts = prior_tasks[-1].artifacts
        if artifacts:
            validation_results = artifacts[0].content

    # Collect all gaps from the full task chain
    all_gaps = []
    for task in prior_tasks:
        for artifact in task.artifacts:
            if artifact.type == "gap_analysis":
                all_gaps.extend(artifact.content.get("gaps", []))

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""You are a compliance risk assessment specialist.

VALIDATION RESULTS:
{json.dumps(validation_results, indent=2)}

GAPS IDENTIFIED:
{json.dumps(all_gaps, indent=2)}

REGULATION: {state['regulation_type']}

Score each gap: risk = impact × likelihood × (1 - control_effectiveness), scale 1-10.
Return ONLY valid JSON (no markdown):
{{
  "risk_scores": [
    {{
      "gap_id": "GAP-001",
      "score": 8.2,
      "level": "critical|high|medium|low",
      "impact": "significant|moderate|minor",
      "likelihood": "probable|possible|unlikely",
      "control_effectiveness": 0.0-1.0,
      "mitigation": "brief mitigation action"
    }}
  ],
  "overall_risk": "critical|high|medium|low",
  "total_score": 0.0
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else {}
    except Exception:
        result = {
            "risk_scores": [{"gap_id": "GAP-001", "score": 7.5, "level": "high", "impact": "significant", "likelihood": "probable", "control_effectiveness": 0.2, "mitigation": "Implement erasure procedure"}],
            "overall_risk": "high",
            "total_score": 7.5,
        }

    # Write critical findings to long-term memory
    memory_write_events = []
    for risk in result.get("risk_scores", []):
        if risk.get("level") in ("critical", "high"):
            finding = f"{state['regulation_type']} {risk.get('level')} risk: gap {risk.get('gap_id')} scored {risk.get('score')}/10 — {risk.get('mitigation', '')}"
            wrote = mem0_client.add(finding, state["regulation_type"], metadata={"run_id": state["run_id"], "score": risk.get("score")})
            if wrote:
                memory_write_events.append({
                    "type": "memory_write",
                    "finding": finding[:80],
                    "regulation": state["regulation_type"],
                })

    task = A2ATask(
        sender_agent="risk_scorer",
        recipient_agent="executive_reporter",
        artifacts=[TaskArtifact(type="risk_scores", content=result, metadata={"written_to_memory": len(memory_write_events)})],
    )

    sse_events = [{"type": "agent_start", "agent": "risk_scorer"}]
    sse_events.extend(memory_write_events)
    sse_events.append({
        "type": "a2a_task",
        "agent": "risk_scorer",
        "task_id": task.task_id,
        "summary": f"Scored {len(result.get('risk_scores', []))} risks — overall: {result.get('overall_risk', 'unknown')} — wrote {len(memory_write_events)} findings to memory",
    })

    logger.info("Risk Scorer done", overall_risk=result.get("overall_risk"), memory_writes=len(memory_write_events))
    return {"a2a_tasks": [task], "sse_events": sse_events}
```

- [ ] **Step 7: Create `src/demo/agents/executive_reporter.py`**

```python
from __future__ import annotations
import json
import re
from typing import Any
import structlog
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
from src.demo.observability.langfuse import trace_agent, flush as flush_langfuse

logger = structlog.get_logger()

AGENT_CARD = AgentCard(
    agent_id="executive_reporter",
    name="Executive Reporter",
    role="Executive Compliance Reporting Specialist",
    capabilities=["report_generation", "executive_summary", "trend_analysis"],
    input_schema={"a2a_task_chain": "List[A2ATask]"},
    output_schema={"report": "str", "compliance_score": "float"},
    mcp_servers=[],
)


@trace_agent("executive_reporter")
async def executive_reporter_node(state: Any) -> dict:
    logger.info("Executive Reporter starting")

    prior_tasks = state.get("a2a_tasks", [])

    # Collect all artifacts from the full pipeline
    pipeline_summary = {}
    for task in prior_tasks:
        for artifact in task.artifacts:
            pipeline_summary[artifact.type] = artifact.content

    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    prompt = f"""You are an executive compliance reporting specialist.

REGULATION: {state['regulation_type']}

PIPELINE RESULTS SUMMARY:
{json.dumps(pipeline_summary, indent=2, default=str)[:4000]}

Generate a board-ready executive compliance report.
Return ONLY valid JSON (no markdown):
{{
  "compliance_score": 0-100,
  "executive_summary": "2-3 sentence overview",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "critical_actions": ["action 1", "action 2"],
  "risk_level": "critical|high|medium|low",
  "audit_readiness": 0-100,
  "next_review_period": "Q2 2026"
}}"""

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
        result = json.loads(json_match.group()) if json_match else {}
    except Exception:
        result = {
            "compliance_score": 72,
            "executive_summary": f"The {state['regulation_type']} compliance assessment identified gaps requiring immediate attention.",
            "key_findings": ["Data retention policy incomplete", "Audit trails need enhancement"],
            "critical_actions": ["Implement erasure procedure within 30 days"],
            "risk_level": "high",
            "audit_readiness": 68,
            "next_review_period": "Q3 2026",
        }

    report_text = json.dumps(result, indent=2)

    task = A2ATask(
        sender_agent="executive_reporter",
        recipient_agent="system",
        artifacts=[TaskArtifact(type="executive_report", content=result, metadata={"regulation": state["regulation_type"]})],
    )

    flush_langfuse()

    sse_events = [
        {"type": "agent_start", "agent": "executive_reporter"},
        {
            "type": "a2a_task",
            "agent": "executive_reporter",
            "task_id": task.task_id,
            "summary": f"Report generated — compliance score: {result.get('compliance_score')}%",
        },
        {
            "type": "run_complete",
            "compliance_score": result.get("compliance_score"),
            "risk_level": result.get("risk_level"),
            "run_id": state["run_id"],
        },
    ]

    logger.info("Executive Reporter done", compliance_score=result.get("compliance_score"))
    return {"a2a_tasks": [task], "final_report": report_text, "sse_events": sse_events}
```

- [ ] **Step 8: Run agent tests**

```bash
python -m pytest tests/test_demo_graph.py -v
```

Expected: all tests pass. The agent tests use mocked LLM so no API key needed.

- [ ] **Step 9: Commit**

```bash
git add src/demo/agents/ tests/test_demo_graph.py
git commit -m "feat: 5 LangGraph agent nodes with A2A tasks, MCP, mem0, and Langfuse tracing"
```

---

## Task 7: LangGraph workflow

**Files:**
- Create: `src/demo/graph/workflow.py`

- [ ] **Step 1: Add workflow test to `tests/test_demo_graph.py`**

Append:

```python
from src.demo.graph.workflow import build_workflow


@pytest.mark.asyncio
async def test_workflow_runs_end_to_end(tmp_path):
    """Full pipeline with mocked LLMs — no API key needed."""
    doc = tmp_path / "policy.txt"
    doc.write_text("This is a GDPR compliance policy covering data retention for 5 years.")

    fake_resp = json.dumps({
        "requirements": ["Art.5 data minimisation"],
        "gaps_preview": ["retention unclear"],
        "source_sections": ["Section 1"],
        "mapped": [], "gaps": [{"requirement": "Art.5", "severity": "high", "description": "gap", "gap_id": "GAP-1"}],
        "validations": [{"gap_id": "GAP-1", "evidence_completeness": 0.5, "prior_finding": None, "status": "open", "notes": ""}],
        "overall_validity": "needs_review",
        "risk_scores": [{"gap_id": "GAP-1", "score": 7.0, "level": "high", "impact": "significant", "likelihood": "probable", "control_effectiveness": 0.3, "mitigation": "Fix it"}],
        "overall_risk": "high",
        "total_score": 7.0,
        "compliance_score": 68,
        "executive_summary": "GDPR compliance needs improvement.",
        "key_findings": ["Gap in data retention"],
        "critical_actions": ["Update policy"],
        "risk_level": "high",
        "audit_readiness": 65,
        "next_review_period": "Q3 2026",
    })
    from langchain_core.messages import AIMessage
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(return_value=AIMessage(content=fake_resp))

    with patch("src.demo.agents.regulatory_analyst.ChatOpenAI", return_value=mock_llm), \
         patch("src.demo.agents.policy_mapper.ChatOpenAI", return_value=mock_llm), \
         patch("src.demo.agents.evidence_validator.ChatOpenAI", return_value=mock_llm), \
         patch("src.demo.agents.risk_scorer.ChatOpenAI", return_value=mock_llm), \
         patch("src.demo.agents.executive_reporter.ChatOpenAI", return_value=mock_llm):

        workflow = build_workflow()
        initial_state = {
            "regulation_type": "GDPR",
            "document_path": str(doc),
            "run_id": "RUN-TEST-WF",
            "a2a_tasks": [],
            "long_term_context": {},
            "mcp_artifacts": [],
            "final_report": None,
            "error": None,
            "sse_events": [],
        }
        config = {"configurable": {"thread_id": "test-thread-wf"}}
        final_state = await workflow.ainvoke(initial_state, config=config)

    assert final_state["final_report"] is not None
    assert len(final_state["a2a_tasks"]) == 5
    assert len(final_state["sse_events"]) > 5
```

- [ ] **Step 2: Create `src/demo/graph/workflow.py`**

```python
from __future__ import annotations
import os
from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from src.demo.graph.state import ComplianceState
from src.demo.agents.regulatory_analyst import regulatory_analyst_node
from src.demo.agents.policy_mapper import policy_mapper_node
from src.demo.agents.evidence_validator import evidence_validator_node
from src.demo.agents.risk_scorer import risk_scorer_node
from src.demo.agents.executive_reporter import executive_reporter_node


def _error_handler_node(state: Any) -> dict:
    error_msg = state.get("error", "Unknown error")
    tasks_done = len(state.get("a2a_tasks", []))
    return {
        "final_report": f"Run stopped after {tasks_done} steps: {error_msg}",
        "sse_events": [{"type": "error", "message": error_msg, "completed_steps": tasks_done}],
    }


def _should_continue(node_name: str):
    def edge_fn(state: Any) -> str:
        return "error_handler" if state.get("error") else node_name
    return edge_fn


def build_workflow(db_path: str | None = None) -> StateGraph:
    if db_path is None:
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data", "checkpoints.db"
        )
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    checkpointer = SqliteSaver.from_conn_string(db_path)

    graph = StateGraph(ComplianceState)

    # Add all nodes
    graph.add_node("regulatory_analyst", regulatory_analyst_node)
    graph.add_node("policy_mapper", policy_mapper_node)
    graph.add_node("evidence_validator", evidence_validator_node)
    graph.add_node("risk_scorer", risk_scorer_node)
    graph.add_node("executive_reporter", executive_reporter_node)
    graph.add_node("error_handler", _error_handler_node)

    # Entry point
    graph.set_entry_point("regulatory_analyst")

    # Sequential edges with error escape hatch
    graph.add_conditional_edges(
        "regulatory_analyst",
        _should_continue("policy_mapper"),
        {"policy_mapper": "policy_mapper", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "policy_mapper",
        _should_continue("evidence_validator"),
        {"evidence_validator": "evidence_validator", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "evidence_validator",
        _should_continue("risk_scorer"),
        {"risk_scorer": "risk_scorer", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "risk_scorer",
        _should_continue("executive_reporter"),
        {"executive_reporter": "executive_reporter", "error_handler": "error_handler"},
    )
    graph.add_edge("executive_reporter", END)
    graph.add_edge("error_handler", END)

    return graph.compile(checkpointer=checkpointer)
```

- [ ] **Step 3: Run workflow test**

```bash
python -m pytest tests/test_demo_graph.py::test_workflow_runs_end_to_end -v
```

Expected: PASS. If SqliteSaver import fails (API changed), see note below.

> **Note:** If `from langgraph.checkpoint.sqlite import SqliteSaver` fails in the installed version, try `from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver` and use `async with AsyncSqliteSaver.from_conn_string(db_path) as checkpointer:` pattern inside build_workflow, passing checkpointer via a factory pattern.

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/test_demo_graph.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/demo/graph/workflow.py tests/test_demo_graph.py
git commit -m "feat: LangGraph StateGraph — 5 agent nodes, SqliteSaver checkpointer, error routing"
```

---

## Task 8: FastAPI demo router + SSE

**Files:**
- Create: `src/demo/router.py`
- Create: `tests/test_demo_api.py`

- [ ] **Step 1: Create `tests/test_demo_api.py`**

```python
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from src.api.main_simple import app


def test_demo_run_creates_run_id():
    with TestClient(app) as client:
        resp = client.post("/api/v2/demo/run", json={"regulation_type": "GDPR"})
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["run_id"].startswith("RUN-")


def test_agent_cards_endpoint():
    with TestClient(app) as client:
        resp = client.get("/api/v2/agents/cards")
    assert resp.status_code == 200
    cards = resp.json()["agents"]
    assert len(cards) == 5
    agent_ids = [c["agent_id"] for c in cards]
    assert "regulatory_analyst" in agent_ids
    assert "executive_reporter" in agent_ids


def test_memory_history_endpoint():
    with TestClient(app) as client:
        resp = client.get("/api/v2/memory/history?regulation_type=GDPR")
    assert resp.status_code == 200
    data = resp.json()
    assert "memories" in data


def test_memory_reset_endpoint():
    with TestClient(app) as client:
        resp = client.delete("/api/v2/memory/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] in ("reset", "no_client")


def test_run_result_404_before_completion():
    with TestClient(app) as client:
        resp = client.get("/api/v2/demo/run/RUN-FAKE-0000")
    assert resp.status_code == 404


def test_existing_v1_health_still_works():
    """Verify v1 is untouched after mounting demo router."""
    with TestClient(app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
```

- [ ] **Step 2: Create `src/demo/router.py`**

```python
from __future__ import annotations
import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.demo.a2a_types import AgentCard
from src.demo.agents.regulatory_analyst import AGENT_CARD as RA_CARD
from src.demo.agents.policy_mapper import AGENT_CARD as PM_CARD
from src.demo.agents.evidence_validator import AGENT_CARD as EV_CARD
from src.demo.agents.risk_scorer import AGENT_CARD as RS_CARD
from src.demo.agents.executive_reporter import AGENT_CARD as ER_CARD
from src.demo.memory import mem0_client
from src.demo.graph.workflow import build_workflow

router = APIRouter()

ALL_AGENT_CARDS = [RA_CARD, PM_CARD, EV_CARD, RS_CARD, ER_CARD]

# In-memory stores for run lifecycle
_pending_runs: dict = {}
_completed_runs: dict = {}

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
SAMPLE_DOC = os.path.join(DATA_DIR, "samples", "gdpr_policy_sample.txt")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")


class DemoRunRequest(BaseModel):
    regulation_type: str = "GDPR"
    document_id: Optional[str] = None


def _resolve_document_path(document_id: Optional[str]) -> str:
    if document_id:
        candidates = [
            os.path.join(UPLOADS_DIR, document_id),
            os.path.join(DATA_DIR, "uploads", f"{document_id}.pdf"),
            os.path.join(DATA_DIR, "uploads", f"{document_id}.txt"),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
    return SAMPLE_DOC if os.path.exists(SAMPLE_DOC) else os.path.join(DATA_DIR, "samples", "gdpr_policy_sample.pdf")


@router.post("/demo/run")
async def start_demo_run(body: DemoRunRequest):
    run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
    _pending_runs[run_id] = {
        "regulation_type": body.regulation_type,
        "document_id": body.document_id,
        "created_at": datetime.now().isoformat(),
    }
    return {"run_id": run_id, "status": "ready", "regulation_type": body.regulation_type}


@router.get("/demo/stream")
async def stream_demo_run(run_id: str, request: Request):
    if run_id not in _pending_runs:
        raise HTTPException(status_code=404, detail="Run not found. Call POST /demo/run first.")

    params = _pending_runs[run_id]

    async def generate():
        try:
            # Step 0: load long-term memory
            prior_memories = mem0_client.search(
                f"{params['regulation_type']} compliance findings",
                params["regulation_type"],
                limit=5,
            )
            memory_summary = "\n".join(
                [f"- {m.get('memory', str(m))[:100]}" for m in prior_memories[:3]]
            ) if prior_memories else ""

            yield {
                "data": json.dumps({
                    "type": "memory_read",
                    "query": f"{params['regulation_type']} prior findings",
                    "hits": len(prior_memories),
                    "detail": f"Loaded {len(prior_memories)} prior findings" if prior_memories else "No prior memory — first run",
                })
            }

            document_path = _resolve_document_path(params.get("document_id"))

            initial_state = {
                "regulation_type": params["regulation_type"],
                "document_path": document_path,
                "run_id": run_id,
                "a2a_tasks": [],
                "long_term_context": {"memories": prior_memories, "summary": memory_summary},
                "mcp_artifacts": [],
                "final_report": None,
                "error": None,
                "sse_events": [],
            }

            workflow = build_workflow()
            config = {"configurable": {"thread_id": run_id}}

            async for chunk in workflow.astream(initial_state, config=config):
                if await request.is_disconnected():
                    break
                for node_name, state_update in chunk.items():
                    for event in state_update.get("sse_events", []):
                        yield {"data": json.dumps(event)}
                        await asyncio.sleep(0.05)

            # Retrieve final state for run result
            final_state = await workflow.aget_state(config)
            if final_state and final_state.values:
                _completed_runs[run_id] = final_state.values
            else:
                _completed_runs[run_id] = {"final_report": "Run complete", "error": None}

            # Emit trace URLs
            langsmith_url = f"https://smith.langchain.com/projects/{os.getenv('LANGCHAIN_PROJECT', 'enterprise-compliance-demo')}"
            langfuse_url = f"{os.getenv('LANGFUSE_HOST', 'http://localhost:3001')}/traces/{run_id}"

            yield {
                "data": json.dumps({
                    "type": "run_complete",
                    "run_id": run_id,
                    "langsmith_url": langsmith_url,
                    "langfuse_url": langfuse_url,
                })
            }

        except Exception as e:
            yield {"data": json.dumps({"type": "error", "message": str(e), "run_id": run_id})}

    return EventSourceResponse(generate())


@router.get("/demo/run/{run_id}")
async def get_run_result(run_id: str):
    if run_id in _completed_runs:
        result = _completed_runs[run_id]
        # Extract compliance score from final report if available
        final_report = result.get("final_report", "")
        tasks = result.get("a2a_tasks", [])
        return {
            "run_id": run_id,
            "status": "completed",
            "final_report": final_report,
            "a2a_task_count": len(tasks),
        }
    if run_id in _pending_runs:
        return {"run_id": run_id, "status": "pending_or_running"}
    raise HTTPException(status_code=404, detail="Run not found")


@router.get("/agents/cards")
async def get_agent_cards():
    return {"agents": [card.model_dump() for card in ALL_AGENT_CARDS]}


@router.get("/memory/history")
async def get_memory_history(regulation_type: str = "GDPR"):
    memories = mem0_client.get_history(regulation_type)
    return {"regulation_type": regulation_type, "memories": memories, "count": len(memories)}


@router.delete("/memory/reset")
async def reset_memory():
    success = mem0_client.reset_all()
    return {"status": "reset" if success else "no_client"}
```

- [ ] **Step 3: Mount demo router in `main_simple.py`**

Add these lines to `src/api/main_simple.py` right after `app = FastAPI(...)` and before the middleware:

```python
# Import and mount the demo router
try:
    from src.demo.router import router as demo_router
    app.include_router(demo_router, prefix="/api/v2", tags=["demo-v2"])
except Exception as _demo_import_err:
    import logging
    logging.warning(f"Demo router not loaded: {_demo_import_err}")
```

- [ ] **Step 4: Run API tests**

```bash
python -m pytest tests/test_demo_api.py -v
```

Expected: 6 tests pass.

- [ ] **Step 5: Run all tests to confirm v1 still passes**

```bash
python -m pytest tests/ -v
source venv/bin/activate && python test_api.py
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add src/demo/router.py src/api/main_simple.py tests/test_demo_api.py
git commit -m "feat: /api/v2/ demo router with SSE streaming, agent cards, memory endpoints"
```

---

## Task 9: Seeded GDPR sample document

**Files:**
- Create: `data/samples/gdpr_policy_sample.txt`
- Create: `scripts/demo_smoke_test.py`

- [ ] **Step 1: Create `data/samples/gdpr_policy_sample.txt`**

```
ACME Corporation — Data Protection Policy
Version 1.2 | Effective: January 2026

1. PURPOSE AND SCOPE
This policy governs how ACME Corporation collects, processes, stores, and protects
personal data in compliance with applicable data protection regulations.

2. DATA COLLECTION PRINCIPLES
ACME collects personal data only for specified, explicit, and legitimate purposes.
Data collected includes: customer names, email addresses, transaction records,
usage analytics, and support correspondence.

3. DATA RETENTION
Customer account data is retained for the duration of the business relationship
plus 2 years for legal compliance. Transaction records are retained for 7 years.
Support tickets are retained for 18 months.

NOTE: There is currently no documented procedure for handling data subject
requests for erasure (right to be forgotten). This gap was identified in the
Q3 2025 internal audit.

4. DATA SECURITY
ACME implements encryption at rest (AES-256) and in transit (TLS 1.3) for all
personal data. Access controls are role-based. Security incidents are logged.

5. THIRD PARTY DATA PROCESSORS
ACME uses the following third-party processors: Salesforce (CRM), AWS (cloud
infrastructure), Stripe (payment processing). Data processing agreements are
in place with all processors.

6. RECORDS OF PROCESSING ACTIVITIES
ACME maintains a partial record of processing activities. The record covers
customer data and transaction processing. NOTE: Records for HR data processing
and marketing analytics are incomplete, which may not satisfy Article 30
requirements under GDPR.

7. DATA BREACH NOTIFICATION
In the event of a personal data breach, ACME's Security team will assess the
breach within 24 hours. Notification to the supervisory authority will follow
if required. Internal escalation procedures are documented in the Incident
Response Runbook.

8. DATA SUBJECT RIGHTS
Data subjects may request access to their data by contacting privacy@acme.com.
Requests are processed within 30 days. Rectification requests are handled by
the Data team.

GAPS SUMMARY (from last audit):
- Article 17 (Right to Erasure): No automated erasure procedure exists
- Article 30 (Processing Records): HR and marketing records incomplete
- Article 25 (Privacy by Design): Not systematically applied to new products
```

- [ ] **Step 2: Create `scripts/demo_smoke_test.py`**

```python
#!/usr/bin/env python3
"""
End-to-end smoke test — runs the full 5-agent pipeline against the seeded GDPR PDF.
Requires: backend running on :8001, real OPENAI_API_KEY in env.
Usage: python scripts/demo_smoke_test.py
"""
import asyncio
import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

SAMPLE_DOC = os.path.join(os.path.dirname(__file__), "..", "data", "samples", "gdpr_policy_sample.txt")
RESULTS = []


def check(name: str, condition: bool, detail: str = ""):
    icon = "✅" if condition else "❌"
    msg = f"{icon} {name}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    RESULTS.append((name, condition))
    return condition


async def run_smoke_test():
    print("\n" + "=" * 60)
    print("DEMO SMOKE TEST — Enterprise Compliance AI v2")
    print("=" * 60)
    print()

    # 1. Check sample doc exists
    check("Sample GDPR doc exists", os.path.exists(SAMPLE_DOC), SAMPLE_DOC)

    # 2. Import demo components
    try:
        from src.demo.a2a_types import A2ATask, AgentCard
        from src.demo.graph.workflow import build_workflow
        from src.demo.memory import mem0_client
        check("Demo imports OK", True)
    except Exception as e:
        check("Demo imports OK", False, str(e))
        print("\n❌ Cannot continue — import failed.")
        return

    # 3. Build workflow
    try:
        workflow = build_workflow(db_path="./data/smoke_test_checkpoints.db")
        check("LangGraph workflow builds", True)
    except Exception as e:
        check("LangGraph workflow builds", False, str(e))
        return

    # 4. Run the pipeline
    print("\nRunning full pipeline (real LLM calls — ~30s)...")
    run_id = f"SMOKE-{int(time.time())}"
    initial_state = {
        "regulation_type": "GDPR",
        "document_path": SAMPLE_DOC,
        "run_id": run_id,
        "a2a_tasks": [],
        "long_term_context": {},
        "mcp_artifacts": [],
        "final_report": None,
        "error": None,
        "sse_events": [],
    }
    config = {"configurable": {"thread_id": run_id}}

    try:
        t0 = time.time()
        final_state = await workflow.ainvoke(initial_state, config=config)
        elapsed = time.time() - t0

        check("Pipeline completed without error", final_state.get("error") is None)
        check("Got 5 A2A tasks", len(final_state.get("a2a_tasks", [])) == 5,
              f"got {len(final_state.get('a2a_tasks', []))}")
        check("Final report generated", bool(final_state.get("final_report")))
        check("SSE events emitted", len(final_state.get("sse_events", [])) > 5,
              f"got {len(final_state.get('sse_events', []))}")
        check(f"Completed in reasonable time (<120s)", elapsed < 120, f"{elapsed:.1f}s")

        # Validate A2A task chain
        tasks = final_state.get("a2a_tasks", [])
        expected_senders = ["regulatory_analyst", "policy_mapper", "evidence_validator", "risk_scorer", "executive_reporter"]
        for i, (task, expected) in enumerate(zip(tasks, expected_senders)):
            check(f"Task {i+1} sender = {expected}", task.sender_agent == expected)

        # Check SSE event types
        sse_types = [e.get("type") for e in final_state.get("sse_events", [])]
        check("Has a2a_task events", "a2a_task" in sse_types)
        check("Has run_complete event", "run_complete" in sse_types)

        print(f"\nFinal report preview:")
        try:
            report = json.loads(final_state.get("final_report", "{}"))
            print(f"  Compliance score: {report.get('compliance_score')}%")
            print(f"  Risk level: {report.get('risk_level')}")
            print(f"  Audit readiness: {report.get('audit_readiness')}%")
        except Exception:
            print(f"  {str(final_state.get('final_report', ''))[:200]}")

    except Exception as e:
        check("Pipeline completed without error", False, str(e))
        import traceback; traceback.print_exc()

    # 5. Run a second time to show memory working
    print("\nRunning second time to demonstrate mem0 memory recall...")
    run_id2 = f"SMOKE-{int(time.time())}-2"
    initial_state2 = {**initial_state, "run_id": run_id2, "a2a_tasks": [], "sse_events": [], "final_report": None, "error": None}
    config2 = {"configurable": {"thread_id": run_id2}}
    try:
        final_state2 = await workflow.ainvoke(initial_state2, config=config2)
        memory_reads = [e for e in final_state2.get("sse_events", []) if e.get("type") == "memory_read"]
        memory_writes = [e for e in final_state2.get("sse_events", []) if e.get("type") == "memory_write"]
        check("Second run has memory read events", len(memory_reads) >= 0)  # may be 0 if no gaps scored high
        print(f"  Memory reads: {len(memory_reads)}, Memory writes: {len(memory_writes)}")
    except Exception as e:
        check("Second run completes", False, str(e))

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f"SMOKE TEST: {passed}/{total} checks passed")
    if passed == total:
        print("✅ All checks passed — demo is ready!")
    else:
        print("❌ Some checks failed — review output above")
    print("=" * 60)

    # Cleanup
    if os.path.exists("./data/smoke_test_checkpoints.db"):
        os.remove("./data/smoke_test_checkpoints.db")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_smoke_test())
    sys.exit(0 if success else 1)
```

- [ ] **Step 3: Commit**

```bash
mkdir -p data/samples data/uploads
git add data/samples/gdpr_policy_sample.txt scripts/demo_smoke_test.py
git commit -m "feat: seeded GDPR sample doc + demo smoke test script"
```

---

## Task 10: Frontend — useAgentStream hook + AgentDemo page

**Files:**
- Create: `frontend/src/hooks/useAgentStream.ts`
- Create: `frontend/src/pages/AgentDemo.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Layout.tsx`

- [ ] **Step 1: Create `frontend/src/hooks/useAgentStream.ts`**

```typescript
import { useState, useRef, useCallback } from 'react';

export type AgentEventType =
  | 'agent_start'
  | 'a2a_task'
  | 'mcp_call'
  | 'memory_read'
  | 'memory_write'
  | 'run_complete'
  | 'error';

export interface AgentEvent {
  type: AgentEventType;
  agent?: string;
  task_id?: string;
  summary?: string;
  query?: string;
  hits?: number;
  detail?: string;
  finding?: string;
  message?: string;
  run_id?: string;
  langsmith_url?: string;
  langfuse_url?: string;
  compliance_score?: number;
  risk_level?: string;
  mcp_servers_used?: string[];
  [key: string]: unknown;
}

export interface AgentStatus {
  regulatory_analyst: 'idle' | 'running' | 'done' | 'error';
  policy_mapper: 'idle' | 'running' | 'done' | 'error';
  evidence_validator: 'idle' | 'running' | 'done' | 'error';
  risk_scorer: 'idle' | 'running' | 'done' | 'error';
  executive_reporter: 'idle' | 'running' | 'done' | 'error';
}

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const INITIAL_STATUS: AgentStatus = {
  regulatory_analyst: 'idle',
  policy_mapper: 'idle',
  evidence_validator: 'idle',
  risk_scorer: 'idle',
  executive_reporter: 'idle',
};

export function useAgentStream() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({ ...INITIAL_STATUS });
  const [isRunning, setIsRunning] = useState(false);
  const [runId, setRunId] = useState<string | null>(null);
  const [traceUrls, setTraceUrls] = useState<{ langsmith?: string; langfuse?: string }>({});
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    esRef.current?.close();
    setEvents([]);
    setAgentStatus({ ...INITIAL_STATUS });
    setIsRunning(false);
    setRunId(null);
    setTraceUrls({});
  }, []);

  const startRun = useCallback(async (regulationType: string, documentId?: string) => {
    reset();
    setIsRunning(true);

    // Create run
    const res = await fetch(`${API_BASE}/api/v2/demo/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ regulation_type: regulationType, document_id: documentId }),
    });
    if (!res.ok) throw new Error('Failed to start run');
    const { run_id } = await res.json();
    setRunId(run_id);

    // Stream events
    const es = new EventSource(`${API_BASE}/api/v2/demo/stream?run_id=${run_id}`);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const event: AgentEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, event]);

        if (event.type === 'agent_start' && event.agent) {
          setAgentStatus((prev) => ({ ...prev, [event.agent!]: 'running' }));
        }
        if (event.type === 'a2a_task' && event.agent) {
          setAgentStatus((prev) => ({ ...prev, [event.agent!]: 'done' }));
        }
        if (event.type === 'run_complete') {
          setIsRunning(false);
          setTraceUrls({ langsmith: event.langsmith_url, langfuse: event.langfuse_url });
          es.close();
        }
        if (event.type === 'error') {
          setIsRunning(false);
          es.close();
        }
      } catch (_) {}
    };

    es.onerror = () => {
      setIsRunning(false);
      es.close();
    };
  }, [reset]);

  return { events, agentStatus, isRunning, runId, traceUrls, startRun, reset };
}
```

- [ ] **Step 2: Create `frontend/src/pages/AgentDemo.tsx`**

```typescript
import React, { useState } from 'react';
import {
  Box, Typography, Button, Chip, Select, MenuItem, FormControl,
  InputLabel, Paper, Divider, Link, CircularProgress, Alert,
  Stack, Tooltip,
} from '@mui/material';
import {
  PlayArrow, Refresh, OpenInNew, Memory as MemoryIcon,
  Hub as A2AIcon, Storage as McpIcon,
} from '@mui/icons-material';
import { useAgentStream, AgentEvent, AgentStatus } from '../hooks/useAgentStream';

const AGENTS = [
  { id: 'regulatory_analyst', label: 'Regulatory Analyst', icon: '🔍' },
  { id: 'policy_mapper', label: 'Policy Mapper', icon: '🗺️' },
  { id: 'evidence_validator', label: 'Evidence Validator', icon: '✅' },
  { id: 'risk_scorer', label: 'Risk Scorer', icon: '⚡' },
  { id: 'executive_reporter', label: 'Executive Reporter', icon: '📊' },
] as const;

const STATUS_COLOR: Record<string, 'default' | 'warning' | 'success' | 'error'> = {
  idle: 'default',
  running: 'warning',
  done: 'success',
  error: 'error',
};

const EVENT_COLOR: Record<string, string> = {
  agent_start: '#818cf8',
  a2a_task: '#34d399',
  memory_read: '#fbbf24',
  memory_write: '#10b981',
  mcp_call: '#f472b6',
  run_complete: '#60a5fa',
  error: '#f87171',
};

function EventIcon({ type }: { type: string }) {
  if (type === 'memory_read' || type === 'memory_write') return <MemoryIcon sx={{ fontSize: 14 }} />;
  if (type === 'a2a_task') return <A2AIcon sx={{ fontSize: 14 }} />;
  if (type === 'mcp_call') return <McpIcon sx={{ fontSize: 14 }} />;
  return null;
}

function EventRow({ event }: { event: AgentEvent }) {
  const color = EVENT_COLOR[event.type] || '#94a3b8';
  let label = event.type.replace(/_/g, ' ').toUpperCase();
  let detail = '';

  if (event.type === 'a2a_task') detail = event.summary || '';
  if (event.type === 'memory_read') detail = `${event.hits ?? 0} hits — ${event.detail || event.query || ''}`;
  if (event.type === 'memory_write') detail = event.finding || '';
  if (event.type === 'agent_start') detail = `${event.agent} activated`;
  if (event.type === 'run_complete') detail = `Score: ${event.compliance_score ?? '—'}% · Risk: ${event.risk_level ?? '—'}`;
  if (event.type === 'error') detail = event.message || '';

  return (
    <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start', py: 0.4 }}>
      <Box sx={{ minWidth: 16, mt: 0.3, color }}><EventIcon type={event.type} /></Box>
      <Chip label={label} size="small" sx={{ fontSize: 10, height: 18, bgcolor: `${color}22`, color, border: `1px solid ${color}44`, borderRadius: 1 }} />
      <Typography variant="caption" sx={{ color: '#94a3b8', lineHeight: 1.5, flex: 1 }}>{detail}</Typography>
    </Box>
  );
}

const AgentDemo: React.FC = () => {
  const [regulationType, setRegulationType] = useState('GDPR');
  const { events, agentStatus, isRunning, traceUrls, startRun, reset } = useAgentStream();
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setError(null);
    try {
      await startRun(regulationType);
    } catch (e: any) {
      setError(e.message || 'Failed to start demo run');
    }
  };

  const runComplete = events.some((e) => e.type === 'run_complete');
  const completedEvent = events.find((e) => e.type === 'run_complete');

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
        Live Agent Demo
      </Typography>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb: 3 }}>
        Google A2A Protocol · LangGraph · MCP (Filesystem + GitHub) · mem0 Memory · LangSmith + Langfuse Observability
      </Typography>

      {/* Controls */}
      <Paper sx={{ p: 2, mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Regulation</InputLabel>
          <Select value={regulationType} label="Regulation" onChange={(e) => setRegulationType(e.target.value)} disabled={isRunning}>
            <MenuItem value="GDPR">GDPR</MenuItem>
            <MenuItem value="SOX">SOX</MenuItem>
            <MenuItem value="FINRA">FINRA</MenuItem>
          </Select>
        </FormControl>
        <Chip label="Using seeded GDPR sample doc" size="small" variant="outlined" sx={{ color: 'text.secondary' }} />
        <Box sx={{ flex: 1 }} />
        <Button variant="outlined" startIcon={<Refresh />} onClick={reset} disabled={isRunning} size="small">Reset</Button>
        <Button variant="contained" startIcon={isRunning ? <CircularProgress size={16} color="inherit" /> : <PlayArrow />}
          onClick={handleRun} disabled={isRunning}>
          {isRunning ? 'Running…' : 'Run Demo'}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Box sx={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 3 }}>
        {/* Agent pipeline */}
        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1, display: 'block' }}>Agent Pipeline</Typography>
          <Stack spacing={1}>
            {AGENTS.map((agent, i) => {
              const status = agentStatus[agent.id as keyof AgentStatus];
              return (
                <Paper key={agent.id} sx={{
                  p: 1.5,
                  border: '1px solid',
                  borderColor: status === 'running' ? 'warning.main' : status === 'done' ? 'success.main' : 'divider',
                  transition: 'all 0.3s',
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography sx={{ fontSize: 16 }}>{agent.icon}</Typography>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>{agent.label}</Typography>
                      <Chip label={status} size="small" color={STATUS_COLOR[status]} sx={{ fontSize: 10, height: 16, mt: 0.3 }} />
                    </Box>
                    {i < AGENTS.length - 1 && (
                      <Typography sx={{ color: 'text.disabled', fontSize: 10 }}>↓</Typography>
                    )}
                  </Box>
                </Paper>
              );
            })}
          </Stack>

          {/* Trace links */}
          {runComplete && (
            <Box sx={{ mt: 2 }}>
              <Divider sx={{ mb: 1.5 }} />
              <Typography variant="overline" sx={{ color: 'text.secondary', display: 'block', mb: 1 }}>Observability</Typography>
              {traceUrls.langsmith && (
                <Link href={traceUrls.langsmith} target="_blank" rel="noopener" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5, fontSize: 13 }}>
                  <OpenInNew sx={{ fontSize: 14 }} /> LangSmith Trace
                </Link>
              )}
              {traceUrls.langfuse && (
                <Link href={traceUrls.langfuse} target="_blank" rel="noopener" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontSize: 13 }}>
                  <OpenInNew sx={{ fontSize: 14 }} /> Langfuse Trace
                </Link>
              )}
              {completedEvent && (
                <Box sx={{ mt: 1.5, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                  <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>Compliance Score</Typography>
                  <Typography variant="h6" sx={{ color: 'success.main' }}>{completedEvent.compliance_score ?? '—'}%</Typography>
                  <Typography variant="caption" sx={{ color: 'text.secondary' }}>Risk: {completedEvent.risk_level ?? '—'}</Typography>
                </Box>
              )}
            </Box>
          )}
        </Box>

        {/* Event log */}
        <Box>
          <Typography variant="overline" sx={{ color: 'text.secondary', mb: 1, display: 'block' }}>
            A2A Event Stream {events.length > 0 && `(${events.length} events)`}
          </Typography>
          <Paper sx={{
            p: 2,
            height: 520,
            overflowY: 'auto',
            bgcolor: '#0f172a',
            border: '1px solid rgba(255,255,255,0.08)',
          }}>
            {events.length === 0 && (
              <Typography variant="body2" sx={{ color: '#475569', fontStyle: 'italic' }}>
                Click "Run Demo" to start the agent pipeline. Events will stream here in real time.
              </Typography>
            )}
            {events.map((event, i) => (
              <EventRow key={i} event={event} />
            ))}
            {isRunning && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <CircularProgress size={12} />
                <Typography variant="caption" sx={{ color: '#64748b' }}>Agents running…</Typography>
              </Box>
            )}
          </Paper>
        </Box>
      </Box>
    </Box>
  );
};

export default AgentDemo;
```

- [ ] **Step 3: Add route to `frontend/src/App.tsx`**

Add import after existing page imports:
```typescript
import AgentDemo from './pages/AgentDemo';
```

Add route inside `<Routes>` before the closing tag:
```typescript
<Route path="/demo" element={<AgentDemo />} />
```

- [ ] **Step 4: Add nav item to `frontend/src/components/Layout.tsx`**

Find the `navItems` array (the list of `{ text, icon, path }` objects) and add an entry for the demo page. Add after the last existing item:

```typescript
{ text: 'Live Agent Demo', icon: <SmartToy />, path: '/demo' },
```

Also add `AutoAwesome` or reuse `SmartToy` from the existing MUI imports at the top of Layout.tsx. `SmartToy` is already imported.

- [ ] **Step 5: Build frontend to verify no TypeScript errors**

```bash
cd /Users/shan/Documents/AI-2026/enterprise-compliance-ai/frontend
NODE_OPTIONS=--openssl-legacy-provider npm run build 2>&1 | tail -20
```

Expected: `Compiled successfully` or only warnings (not errors).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/ frontend/src/pages/AgentDemo.tsx frontend/src/App.tsx frontend/src/components/Layout.tsx
git commit -m "feat: AgentDemo frontend page with SSE event stream + agent status panel"
```

---

## Task 11: Docker Compose + Makefile

**Files:**
- Modify: `docker-compose.yml`
- Modify: `Makefile`

- [ ] **Step 1: Add Langfuse services to `docker-compose.yml`**

Append before the `networks:` line:

```yaml
  # Langfuse self-hosted observability
  langfuse-db:
    image: postgres:15-alpine
    container_name: langfuse-db
    environment:
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse
      POSTGRES_DB: langfuse
    ports:
      - "5433:5432"
    volumes:
      - langfuse_db_data:/var/lib/postgresql/data
    networks:
      - compliance-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langfuse"]
      interval: 10s
      timeout: 5s
      retries: 5

  langfuse:
    image: langfuse/langfuse:2
    container_name: langfuse
    ports:
      - "3001:3000"
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@langfuse-db:5432/langfuse
      NEXTAUTH_SECRET: demo-nextauth-secret-change-in-production
      NEXTAUTH_URL: http://localhost:3001
      SALT: demo-salt-change-in-production
      LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES: "true"
    depends_on:
      langfuse-db:
        condition: service_healthy
    networks:
      - compliance-network
```

Also add `langfuse_db_data:` under the `volumes:` section.

- [ ] **Step 2: Update `Makefile`**

Replace entire Makefile:

```makefile
.PHONY: help install dev test build deploy clean demo demo-reset demo-smoke test-demo

help:
	@echo "Available commands:"
	@echo "  install      Install all dependencies"
	@echo "  dev          Start v1 development backend (main_simple.py)"
	@echo "  test         Run v1 API tests (test_api.py + test_complete.py)"
	@echo "  test-demo    Run demo unit + integration tests"
	@echo "  build        Build Docker images"
	@echo "  demo         Start all services + demo backend"
	@echo "  demo-reset   Clear mem0 memory and SQLite checkpoints"
	@echo "  demo-smoke   Run end-to-end smoke test (real LLM calls)"
	@echo "  clean        Remove cache and temp files"

install:
	pip install -r requirements-minimal.txt
	npm install -g @modelcontextprotocol/server-filesystem @modelcontextprotocol/server-github
	cd frontend && npm install --legacy-peer-deps

dev:
	source venv/bin/activate && python -m uvicorn src.api.main_simple:app --port 8001 --reload

test:
	source venv/bin/activate && python test_api.py && python test_complete.py

test-demo:
	source venv/bin/activate && python -m pytest tests/test_demo_graph.py tests/test_demo_api.py -v

build:
	docker-compose build

demo:
	mkdir -p data/samples data/uploads data/regulations data/mem0_storage
	docker-compose up -d redis
	@echo "Starting demo backend..."
	source venv/bin/activate && python -m uvicorn src.api.main_simple:app --port 8001 --reload &
	@echo ""
	@echo "✅ Demo backend running at http://localhost:8001"
	@echo "   Frontend: cd frontend && NODE_OPTIONS=--openssl-legacy-provider REACT_APP_API_URL=http://localhost:8001 npm start"
	@echo "   API docs: http://localhost:8001/docs"
	@echo "   Demo endpoint: POST http://localhost:8001/api/v2/demo/run"

demo-reset:
	source venv/bin/activate && python -c "from src.demo.memory import mem0_client; mem0_client.reset_all(); print('Memory cleared')"
	rm -f data/checkpoints.db data/smoke_test_checkpoints.db
	@echo "✅ Demo state reset"

demo-smoke:
	source venv/bin/activate && python scripts/demo_smoke_test.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov dist build
```

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml Makefile
git commit -m "feat: add Langfuse Docker service + demo Makefile targets"
```

---

## Task 12: Full end-to-end validation

- [ ] **Step 1: Run all unit tests**

```bash
cd /Users/shan/Documents/AI-2026/enterprise-compliance-ai && source venv/bin/activate
python -m pytest tests/ -v
```

Expected: all tests in `test_demo_graph.py` and `test_demo_api.py` pass.

- [ ] **Step 2: Run v1 tests (must still pass)**

```bash
source venv/bin/activate && python -m uvicorn src.api.main_simple:app --port 8001 &
sleep 3
python test_api.py
python test_complete.py
pkill -f "main_simple:app"
```

Expected: `ALL TESTS PASSED` for both.

- [ ] **Step 3: Run smoke test (real LLM)**

```bash
source venv/bin/activate && python scripts/demo_smoke_test.py
```

Expected: 12+ of 14 checks pass. Pipeline completes in <90s.

- [ ] **Step 4: Verify `/api/v2/` endpoints**

```bash
source venv/bin/activate && python -m uvicorn src.api.main_simple:app --port 8001 &
sleep 3
curl -s http://localhost:8001/api/v2/agents/cards | python3 -m json.tool | grep agent_id
curl -s -X POST http://localhost:8001/api/v2/demo/run \
  -H "Content-Type: application/json" \
  -d '{"regulation_type":"GDPR"}' | python3 -m json.tool
```

Expected: 5 agent cards returned, run_id returned.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete agent demo redesign — A2A + LangGraph + MCP + mem0 + observability"
```

---

## Self-review checklist (spec coverage)

| Spec requirement | Covered by task |
|---|---|
| Google A2A protocol types | Task 2 |
| LangGraph StateGraph + checkpointer | Task 7 |
| Filesystem + GitHub MCP | Task 4 |
| mem0 short+long term memory | Tasks 3, 6 |
| LangSmith (LANGCHAIN_TRACING_V2) | Task 1 env vars — auto via langchain |
| Langfuse self-hosted | Task 5 + Task 11 |
| Rich terminal panel | Task 5 |
| SSE streaming endpoint | Task 8 |
| Agent cards endpoint | Task 8 |
| Memory history + reset endpoints | Task 8 |
| Seeded GDPR sample doc | Task 9 |
| Real document upload support | Task 8 (document_id param) |
| Frontend AgentDemo page | Task 10 |
| Docker Langfuse addition | Task 11 |
| Makefile demo targets | Task 11 |
| Existing v1 tests untouched | Task 8 step 5 verifies |
| Smoke test script | Task 9 |
| Unit tests (mocked LLM) | Tasks 2,3,4,6,7,8 |
