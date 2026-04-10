"""LangGraph state definition for the compliance demo workflow.

Uses Annotated reducers so multiple agent nodes can append to
a2a_tasks and sse_events without overwriting each other's output.
"""
import operator
from typing import Annotated, Any, TypedDict

from src.demo.a2a_types import A2ATask


class ComplianceState(TypedDict):
    """Shared state passed between all LangGraph nodes."""

    # ── Inputs ────────────────────────────────────────────────────────────
    regulation_type: str          # e.g. "GDPR", "SOX", "FINRA"
    document_path: str            # absolute or relative path to policy doc

    # ── Agent communication (append-only via operator.add reducer) ────────
    a2a_tasks: Annotated[list[A2ATask], operator.add]

    # ── SSE event stream (append-only) ────────────────────────────────────
    sse_events: Annotated[list[dict[str, Any]], operator.add]

    # ── Memory ────────────────────────────────────────────────────────────
    long_term_context: list[dict[str, Any]]   # loaded from mem0 before graph
    short_term_memory: dict[str, Any]         # SqliteSaver checkpointer data

    # ── Run metadata ──────────────────────────────────────────────────────
    run_id: str
    error: str | None
