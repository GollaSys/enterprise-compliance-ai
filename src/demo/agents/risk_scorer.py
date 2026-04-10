"""Risk Scorer agent node.

Scores each validated gap using risk = impact × likelihood × (1 - control_effectiveness).
Writes findings to mem0 for future runs.

This is the "memory write moment" — findings are persisted so that
subsequent runs can surface them as prior context.
"""
import json
import logging

from src.demo.a2a_types import A2ATask, TaskArtifact, TaskState

logger = logging.getLogger(__name__)


def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def _get_mem0():
    from src.demo.memory.mem0_client import Mem0Client
    return Mem0Client()


def risk_scorer_node(state: dict) -> dict:
    """LangGraph node: score risks + persist findings to mem0."""
    prior_tasks = state.get("a2a_tasks", [])
    validated_gaps = []
    for task in reversed(prior_tasks):
        for artifact in task.artifacts:
            if artifact.type == "evidence_report":
                validated_gaps = artifact.content.get("validated_gaps", [])
                break
        if validated_gaps:
            break

    reg_type = state.get("regulation_type", "GDPR")
    run_id = state.get("run_id", "unknown")

    if not validated_gaps:
        validated_gaps = [{"gap": "No gaps found", "severity": "low", "repeat_finding": False, "notes": ""}]

    prompt = f"""You are a compliance risk scoring expert. Score each gap using this formula:
risk_score = impact × likelihood × (1 - control_effectiveness)
Where each factor is 1-10. Output a final risk_score from 1-10.

VALIDATED GAPS:
{json.dumps(validated_gaps, indent=2)}

Respond with JSON: {{"risks": [{{"gap": "...", "risk_score": 8.2, "impact": 9, "likelihood": 8, "control_effectiveness": 2, "priority": "critical|high|medium|low"}}]}}"""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            risks = parsed.get("risks", [])
        except json.JSONDecodeError:
            # Deterministic fallback scores based on severity
            severity_scores = {"critical": 9.0, "high": 7.5, "medium": 5.0, "low": 2.5}
            risks = [
                {
                    "gap": g.get("gap", "Unknown"),
                    "risk_score": severity_scores.get(g.get("severity", "medium"), 5.0),
                    "impact": 8,
                    "likelihood": 7,
                    "control_effectiveness": 2,
                    "priority": g.get("severity", "medium"),
                }
                for g in validated_gaps
            ]

    except Exception as exc:
        logger.error("risk_scorer_node LLM failed: %s — using fallback scores", exc)
        risks = [
            {
                "gap": g.get("gap", "Unknown"),
                "risk_score": 7.0,
                "impact": 8,
                "likelihood": 7,
                "control_effectiveness": 3,
                "priority": "high",
                "mock": True,
            }
            for g in validated_gaps
        ]

    # Persist findings to mem0 (fire-and-forget)
    mem0 = _get_mem0()
    stored_count = 0
    for risk in risks[:5]:  # store top 5
        if risk.get("risk_score", 0) >= 5.0:
            ok = mem0.add(
                f"{reg_type} critical gap: {risk['gap']}, score {risk['risk_score']:.1f}, run_id={run_id}",
                user_id="demo",
                metadata={"regulation": reg_type, "run_id": run_id, "score": risk["risk_score"]},
            )
            if ok:
                stored_count += 1

    artifact = TaskArtifact(
        type="risk_scores",
        content={"risks": risks, "run_id": run_id},
        metadata={"findings_stored": stored_count, "regulation": reg_type},
    )
    task = A2ATask(
        sender_agent="risk_scorer",
        recipient_agent="executive_reporter",
        artifacts=[artifact],
    )

    sse_event = {
        "type": "agent_update",
        "agent": "risk_scorer",
        "status": task.state,
        "task_id": task.task_id,
        "summary": f"Scored {len(risks)} risks, stored {stored_count} to memory",
        "memory_writes": stored_count,
    }

    return {"a2a_tasks": [task], "sse_events": [sse_event]}
