"""Regulatory Analyst agent node.

Reads the policy document (via MCP/disk), extracts GDPR/SOX/FINRA requirements
using RAG + LLM, and emits an A2ATask for the Policy Mapper.
"""
import json
import logging
import os

from src.demo.a2a_types import A2ATask, MCPCall, TaskArtifact, TaskState
from src.demo.mcp.client import MCPClient

logger = logging.getLogger(__name__)


def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def regulatory_analyst_node(state: dict) -> dict:
    """LangGraph node: extract regulatory requirements from document."""
    mcp = MCPClient()
    mcp_calls = []

    # Step 1: Read document via MCP/disk
    doc_path = state.get("document_path", "")
    doc_text = mcp.read_file(doc_path) if doc_path else ""
    if doc_path:
        mcp_calls.append(MCPCall(server="filesystem", tool="read_file", args={"path": doc_path}))

    # Truncate for LLM context window
    doc_excerpt = doc_text[:4000] if doc_text else "(no document provided)"

    # Step 2: Fetch regulation reference text
    reg_type = state.get("regulation_type", "GDPR")
    reg_text = mcp.get_regulation_text(reg_type)[:2000]
    mcp_calls.append(MCPCall(server="github", tool="get_file_contents", args={"regulation": reg_type}))

    # Step 3: Load prior memory context
    long_term = state.get("long_term_context", [])
    memory_context = ""
    if long_term:
        memory_context = f"\nPrior findings from memory:\n{json.dumps(long_term[:3], indent=2)}"

    # Step 4: LLM extraction
    prompt = f"""You are a regulatory compliance analyst. Analyse this policy document against {reg_type} requirements.

REGULATION REFERENCE:
{reg_text}

POLICY DOCUMENT:
{doc_excerpt}
{memory_context}

Extract a list of specific {reg_type} articles/requirements that apply to this document.
Respond with JSON: {{"requirements": ["Art.X - description", ...]}}
Include 3-7 key requirements."""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Parse JSON response, with fallback
        try:
            parsed = json.loads(content)
            requirements = parsed.get("requirements", [content])
        except json.JSONDecodeError:
            # LLM returned plain text — wrap it
            requirements = [line.strip() for line in content.split("\n") if line.strip()][:7]

        artifact = TaskArtifact(
            type="requirements_list",
            content=requirements,
            metadata={"regulation": reg_type, "source_doc": doc_path, "rag_chunks_used": 1},
        )
        task = A2ATask(
            sender_agent="regulatory_analyst",
            recipient_agent="policy_mapper",
            artifacts=[artifact],
            mcp_calls=mcp_calls,
        )

    except Exception as exc:
        logger.error("regulatory_analyst_node failed: %s", exc)
        # Return partial mock result so pipeline can continue
        artifact = TaskArtifact(
            type="requirements_list",
            content=[f"Mock: {reg_type} requirements (LLM unavailable)", "Art.5 - data minimisation", "Art.17 - right to erasure"],
            metadata={"mock": True, "error": str(exc)},
        )
        task = A2ATask(
            sender_agent="regulatory_analyst",
            recipient_agent="policy_mapper",
            artifacts=[artifact],
            state=TaskState.ERROR,
            error=str(exc),
        )

    sse_event = {
        "type": "agent_update",
        "agent": "regulatory_analyst",
        "status": task.state,
        "task_id": task.task_id,
        "summary": f"Extracted {len(task.artifacts[0].content if task.artifacts else [])} requirements",
    }

    return {"a2a_tasks": [task], "sse_events": [sse_event]}
