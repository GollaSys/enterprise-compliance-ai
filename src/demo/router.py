"""FastAPI router for /api/v2/demo/ endpoints.

Provides:
  GET  /api/v2/demo/health          — health check
  GET  /api/v2/demo/agents          — agent cards (A2A discovery)
  POST /api/v2/demo/run             — synchronous full pipeline run
  GET  /api/v2/demo/stream          — SSE streaming pipeline run
"""
import json
import logging
import os
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.demo.a2a_types import AgentCard
from src.demo.graph.workflow import astream_compliance_pipeline, run_compliance_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/demo", tags=["demo"])

# Default seeded GDPR sample path
_DEFAULT_DOC = str(Path(__file__).parent.parent.parent / "data" / "samples" / "gdpr_policy_sample.txt")

# Agent capability registry
_AGENT_CARDS = [
    AgentCard(
        name="regulatory_analyst",
        description="Extracts regulatory requirements from policy documents using RAG + MCP",
        capabilities=["rag", "mcp_filesystem", "mcp_github", "langfuse_traced"],
        input_schema={"document_path": "str", "regulation_type": "str"},
        output_schema={"requirements_list": "list[str]"},
    ),
    AgentCard(
        name="policy_mapper",
        description="Maps requirements to internal policies and identifies compliance gaps",
        capabilities=["mcp_github", "langfuse_traced", "a2a_consumer"],
        input_schema={"requirements_list": "list[str]"},
        output_schema={"gaps": "list[str]", "covered": "list[str]"},
    ),
    AgentCard(
        name="evidence_validator",
        description="Validates evidence and surfaces prior findings from mem0 long-term memory",
        capabilities=["mem0_search", "langfuse_traced", "a2a_consumer"],
        input_schema={"gap_analysis": "dict"},
        output_schema={"validated_gaps": "list[dict]"},
    ),
    AgentCard(
        name="risk_scorer",
        description="Scores risks using impact × likelihood × (1 - control_effectiveness), writes to mem0",
        capabilities=["mem0_write", "langfuse_traced", "a2a_consumer"],
        input_schema={"validated_gaps": "list[dict]"},
        output_schema={"risk_scores": "list[dict]"},
    ),
    AgentCard(
        name="executive_reporter",
        description="Generates board-ready compliance summary with LangSmith + Langfuse trace links",
        capabilities=["langfuse_traced", "langsmith_traced", "a2a_consumer"],
        input_schema={"all_prior_tasks": "list"},
        output_schema={"executive_report": "str", "trace_urls": "dict"},
    ),
]


class DemoRunRequest(BaseModel):
    regulation_type: str = "GDPR"
    document_path: str | None = None
    document_id: str | None = None  # for uploaded docs from /api/v1/documents/upload


class DemoStreamRequest(BaseModel):
    regulation_type: str = "GDPR"
    document_path: str | None = None


@router.get("/health")
async def demo_health():
    return {"status": "ok", "version": "v2", "features": ["a2a", "rag", "mcp", "mem0", "langfuse"]}


@router.get("/agents")
async def list_agents():
    """Return agent cards for A2A protocol discovery."""
    return [card.model_dump() for card in _AGENT_CARDS]


@router.post("/run")
async def run_demo(request: DemoRunRequest):
    """Run the full compliance pipeline synchronously.

    Returns the final state including all A2A tasks and the executive report.
    """
    doc_path = _resolve_document_path(request.document_path, request.document_id)
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    # Load long-term memory before starting the graph
    long_term_context = _load_long_term_memory(request.regulation_type)

    initial_state = {
        "regulation_type": request.regulation_type,
        "document_path": doc_path,
        "a2a_tasks": [],
        "sse_events": [],
        "long_term_context": long_term_context,
        "short_term_memory": {},
        "run_id": run_id,
        "error": None,
    }

    try:
        final_state = run_compliance_pipeline(initial_state)
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))

    # Serialize A2A tasks for JSON response
    serialized_tasks = [t.model_dump(mode="json") for t in final_state.get("a2a_tasks", [])]

    return {
        "run_id": run_id,
        "regulation_type": request.regulation_type,
        "document_path": doc_path,
        "a2a_tasks": serialized_tasks,
        "sse_events": final_state.get("sse_events", []),
        "error": final_state.get("error"),
    }


@router.get("/stream")
async def stream_demo(regulation_type: str = "GDPR", document_path: str | None = None):
    """Stream the compliance pipeline as Server-Sent Events.

    Each SSE event corresponds to one agent completing.
    Frontend receives real-time updates as the pipeline progresses.
    """
    doc_path = _resolve_document_path(document_path, None)
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    long_term_context = _load_long_term_memory(regulation_type)

    initial_state = {
        "regulation_type": regulation_type,
        "document_path": doc_path,
        "a2a_tasks": [],
        "sse_events": [],
        "long_term_context": long_term_context,
        "short_term_memory": {},
        "run_id": run_id,
        "error": None,
    }

    async def event_generator() -> AsyncGenerator[dict, None]:
        # Start event
        yield {
            "event": "start",
            "data": json.dumps({"run_id": run_id, "regulation_type": regulation_type}),
        }

        try:
            async for chunk in astream_compliance_pipeline(initial_state):
                for sse_event in chunk.get("sse_events", []):
                    yield {
                        "event": sse_event.get("type", "agent_update"),
                        "data": json.dumps(sse_event),
                    }

            yield {"event": "done", "data": json.dumps({"run_id": run_id, "status": "completed"})}

        except Exception as exc:
            logger.error("SSE stream error: %s", exc)
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc), "run_id": run_id}),
            }

    return EventSourceResponse(event_generator())


def _resolve_document_path(document_path: str | None, document_id: str | None) -> str:
    """Resolve document path from request, uploaded doc ID, or seeded default."""
    if document_path and Path(document_path).exists():
        return document_path

    if document_id:
        upload_path = Path("data/uploads") / document_id
        if upload_path.exists():
            return str(upload_path)

    # Fall back to seeded GDPR sample
    if Path(_DEFAULT_DOC).exists():
        return _DEFAULT_DOC

    # Last resort: return the path even if it doesn't exist (agents handle missing files)
    return _DEFAULT_DOC


def _load_long_term_memory(regulation_type: str) -> list:
    """Load prior findings from mem0 before the graph starts."""
    try:
        from src.demo.memory.mem0_client import Mem0Client
        mem0 = Mem0Client()
        results = mem0.search(f"{regulation_type} prior findings", user_id="demo")
        if results:
            logger.info("mem0 hit: %d prior %s findings loaded", len(results), regulation_type)
        return results
    except Exception as exc:
        logger.warning("mem0 pre-load failed: %s", exc)
        return []
