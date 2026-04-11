"""LangGraph compliance demo workflow.

Builds a sequential StateGraph:
  START → regulatory_analyst → policy_mapper → evidence_validator
        → risk_scorer → executive_reporter → END

Each node can route to error_handler on failure.
SqliteSaver provides short-term checkpointing for sync runs;
AsyncSqliteSaver is used for the async SSE streaming path.
"""
import logging
import sqlite3
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.demo.graph.state import ComplianceState

logger = logging.getLogger(__name__)

_DB_PATH = "./data/checkpoints.db"


def _error_handler_node(state: dict) -> dict:
    """Catch-all error handler — emits an SSE event and routes to END."""
    error = state.get("error", "Unknown error")
    logger.error("Pipeline error: %s", error)
    sse_event = {
        "type": "pipeline_error",
        "agent": "error_handler",
        "status": "error",
        "message": str(error),
    }
    return {"sse_events": [sse_event]}


def _safe_node(node_fn):
    """Wrap a node function so errors write to state.error and don't crash the graph."""
    def wrapper(state: dict) -> dict:
        try:
            return node_fn(state)
        except Exception as exc:
            logger.error("Node %s failed: %s", node_fn.__name__, exc)
            return {"error": str(exc), "sse_events": [{"type": "node_error", "agent": node_fn.__name__, "error": str(exc)}]}
    wrapper.__name__ = node_fn.__name__
    return wrapper


def _should_continue(state: dict) -> str:
    """Route to error_handler if state.error is set, else continue normally."""
    return "error_handler" if state.get("error") else "continue"


def _build_graph() -> StateGraph:
    """Build the uncompiled StateGraph (shared by sync and async paths)."""
    from src.demo.agents.regulatory_analyst import regulatory_analyst_node
    from src.demo.agents.policy_mapper import policy_mapper_node
    from src.demo.agents.evidence_validator import evidence_validator_node
    from src.demo.agents.risk_scorer import risk_scorer_node
    from src.demo.agents.executive_reporter import executive_reporter_node

    graph = StateGraph(ComplianceState)

    # Add all agent nodes (wrapped for error safety)
    graph.add_node("regulatory_analyst", _safe_node(regulatory_analyst_node))
    graph.add_node("policy_mapper", _safe_node(policy_mapper_node))
    graph.add_node("evidence_validator", _safe_node(evidence_validator_node))
    graph.add_node("risk_scorer", _safe_node(risk_scorer_node))
    graph.add_node("executive_reporter", _safe_node(executive_reporter_node))
    graph.add_node("error_handler", _error_handler_node)

    # Sequential edges with error routing after each node
    graph.add_edge(START, "regulatory_analyst")
    graph.add_conditional_edges(
        "regulatory_analyst",
        _should_continue,
        {"continue": "policy_mapper", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "policy_mapper",
        _should_continue,
        {"continue": "evidence_validator", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "evidence_validator",
        _should_continue,
        {"continue": "risk_scorer", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "risk_scorer",
        _should_continue,
        {"continue": "executive_reporter", "error_handler": "error_handler"},
    )
    graph.add_edge("executive_reporter", END)
    graph.add_edge("error_handler", END)

    return graph


def build_workflow() -> Any:
    """Build and compile the compliance demo StateGraph (sync path)."""
    graph = _build_graph()
    # Compile with SqliteSaver checkpointer
    try:
        conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        return graph.compile(checkpointer=checkpointer)
    except Exception as exc:
        logger.warning("SqliteSaver init failed (%s) — compiling without checkpointer", exc)
        return graph.compile()


def run_compliance_pipeline(initial_state: dict) -> dict:
    """Run the compiled workflow synchronously and return the final state."""
    app = build_workflow()
    config = {"configurable": {"thread_id": initial_state.get("run_id", "default")}}

    # LangGraph invoke returns the final accumulated state
    final_state = app.invoke(initial_state, config=config)
    return final_state


async def astream_compliance_pipeline(initial_state: dict):
    """Stream workflow events for SSE delivery.

    Uses AsyncSqliteSaver so app.astream() can await checkpoint reads/writes.
    Yields dicts: {"node": str, "sse_events": list, "a2a_tasks": list}
    """
    graph = _build_graph()
    config = {"configurable": {"thread_id": initial_state.get("run_id", "default")}}

    async with AsyncSqliteSaver.from_conn_string(_DB_PATH) as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        async for chunk in app.astream(initial_state, config=config):
            # chunk is {node_name: state_update_dict}
            for node_name, state_update in chunk.items():
                yield {
                    "node": node_name,
                    "sse_events": state_update.get("sse_events", []),
                    "a2a_tasks": state_update.get("a2a_tasks", []),
                }
