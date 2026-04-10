"""Executive Reporter agent node.

Reads all prior A2ATasks, generates a board-ready compliance summary,
and returns the final state with trace URLs.
"""
import json
import logging
import os

from src.demo.a2a_types import A2ATask, TaskArtifact, TaskState

logger = logging.getLogger(__name__)


def _get_llm():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def executive_reporter_node(state: dict) -> dict:
    """LangGraph node: generate executive compliance report."""
    all_tasks = state.get("a2a_tasks", [])
    reg_type = state.get("regulation_type", "GDPR")
    run_id = state.get("run_id", "unknown")

    # Aggregate all prior findings
    requirements = []
    gaps = []
    risks = []

    for task in all_tasks:
        for artifact in task.artifacts:
            if artifact.type == "requirements_list":
                requirements = artifact.content
            elif artifact.type == "gap_analysis":
                gaps = artifact.content.get("gaps", [])
            elif artifact.type == "risk_scores":
                risks = artifact.content.get("risks", [])

    # Sort risks by score (descending)
    risks_sorted = sorted(risks, key=lambda r: r.get("risk_score", 0), reverse=True)
    critical_count = sum(1 for r in risks_sorted if r.get("risk_score", 0) >= 7.0)

    prompt = f"""You are a Chief Compliance Officer writing a board-level summary.

REGULATION: {reg_type}
REQUIREMENTS CHECKED: {len(requirements)}
GAPS IDENTIFIED: {len(gaps)}
RISKS SCORED: {len(risks_sorted)}
CRITICAL RISKS (score ≥ 7): {critical_count}

TOP RISKS:
{json.dumps(risks_sorted[:3], indent=2)}

Write a concise 3-paragraph executive summary:
1. Overall compliance posture (1-2 sentences)
2. Top 2-3 critical findings requiring immediate action
3. Recommended next steps

Keep it board-level — no technical jargon."""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        report_text = response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.error("executive_reporter_node LLM failed: %s", exc)
        report_text = (
            f"COMPLIANCE SUMMARY — {reg_type}\n\n"
            f"Requirements reviewed: {len(requirements)}. "
            f"Gaps identified: {len(gaps)}. "
            f"Critical risks: {critical_count}.\n\n"
            f"Immediate action required on {len(gaps)} compliance gaps. "
            f"See detailed risk scores for prioritization."
        )

    # Build trace URLs for observability links
    langsmith_url = ""
    langfuse_url = ""
    try:
        from src.demo.observability.langfuse import get_trace_url
        langfuse_url = get_trace_url(run_id)
    except Exception:
        pass

    langsmith_project = os.environ.get("LANGCHAIN_PROJECT", "enterprise-compliance-demo")
    if os.environ.get("LANGCHAIN_TRACING_V2") == "true":
        langsmith_url = f"https://smith.langchain.com/o/default/projects/{langsmith_project}"

    artifact = TaskArtifact(
        type="executive_report",
        content={
            "report": report_text,
            "summary_stats": {
                "requirements_checked": len(requirements),
                "gaps_identified": len(gaps),
                "risks_scored": len(risks_sorted),
                "critical_risks": critical_count,
                "regulation": reg_type,
            },
            "trace_urls": {
                "langsmith": langsmith_url,
                "langfuse": langfuse_url,
            },
        },
    )
    task = A2ATask(
        sender_agent="executive_reporter",
        recipient_agent="user",
        artifacts=[artifact],
    )

    sse_event = {
        "type": "run_complete",
        "agent": "executive_reporter",
        "status": "completed",
        "task_id": task.task_id,
        "summary": f"Report generated — {critical_count} critical risks",
        "trace_urls": {"langsmith": langsmith_url, "langfuse": langfuse_url},
    }

    return {"a2a_tasks": [task], "sse_events": [sse_event]}
