"""Policy Mapper agent node.

Reads the requirements A2ATask from the Regulatory Analyst,
maps them to internal policy coverage, and identifies gaps.
Emits an A2ATask for the Evidence Validator.
"""
import json
import logging

from src.demo.a2a_types import A2ATask, MCPCall, TaskArtifact, TaskState
from src.demo.mcp.client import MCPClient

logger = logging.getLogger(__name__)


def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def policy_mapper_node(state: dict) -> dict:
    """LangGraph node: map requirements to policies, identify coverage gaps."""
    mcp = MCPClient()
    mcp_calls = []

    # Read prior A2ATask from Regulatory Analyst (agent-to-agent communication)
    prior_tasks = state.get("a2a_tasks", [])
    requirements = []
    if prior_tasks:
        last_task = prior_tasks[-1]
        for artifact in last_task.artifacts:
            if artifact.type == "requirements_list":
                requirements = artifact.content
                break

    if not requirements:
        requirements = ["No requirements found — using defaults", "Art.5", "Art.17"]

    reg_type = state.get("regulation_type", "GDPR")
    reg_text = mcp.get_regulation_text(reg_type)[:1500]
    mcp_calls.append(MCPCall(server="github", tool="get_file_contents", args={"regulation": reg_type}))

    prompt = f"""You are a compliance policy mapping expert. Given these {reg_type} requirements,
identify which ones are likely COVERED and which are GAPS in a typical company policy.

REQUIREMENTS TO MAP:
{json.dumps(requirements, indent=2)}

REGULATION CONTEXT:
{reg_text[:800]}

For each requirement, determine if a standard policy would cover it or if it's a gap.
Focus on identifying 2-4 specific compliance gaps.

Respond with JSON: {{"gaps": ["Art.X - gap description", ...], "covered": ["Art.Y - covered", ...]}}"""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            gaps = parsed.get("gaps", [])
            covered = parsed.get("covered", [])
        except json.JSONDecodeError:
            gaps = ["Art.17 - right to erasure procedure missing", "Art.30 - incomplete records"]
            covered = requirements[:2]

        artifact = TaskArtifact(
            type="gap_analysis",
            content={"gaps": gaps, "covered": covered},
            metadata={"requirements_analysed": len(requirements)},
        )
        task = A2ATask(
            sender_agent="policy_mapper",
            recipient_agent="evidence_validator",
            artifacts=[artifact],
            mcp_calls=mcp_calls,
        )

    except Exception as exc:
        logger.error("policy_mapper_node failed: %s", exc)
        artifact = TaskArtifact(
            type="gap_analysis",
            content={"gaps": ["Art.17 - mock gap", "Art.30 - mock gap"], "covered": []},
            metadata={"mock": True, "error": str(exc)},
        )
        task = A2ATask(
            sender_agent="policy_mapper",
            recipient_agent="evidence_validator",
            artifacts=[artifact],
            state=TaskState.ERROR,
            error=str(exc),
        )

    sse_event = {
        "type": "agent_update",
        "agent": "policy_mapper",
        "status": task.state,
        "task_id": task.task_id,
        "summary": f"Found {len(task.artifacts[0].content.get('gaps', []) if task.artifacts else [])} gaps",
    }

    return {"a2a_tasks": [task], "sse_events": [sse_event]}
