"""Evidence Validator agent node.

Queries mem0 for prior findings on the same gaps, validates evidence
from the policy document, and emits an A2ATask for the Risk Scorer.

This is the "memory demo moment" — if the Risk Scorer flagged a gap in
a prior run, mem0 surfaces: "Previously critical — check if mitigated."
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


def evidence_validator_node(state: dict) -> dict:
    """LangGraph node: validate evidence + surface prior memory findings."""
    prior_tasks = state.get("a2a_tasks", [])
    gaps = []
    for task in reversed(prior_tasks):
        for artifact in task.artifacts:
            if artifact.type == "gap_analysis":
                gaps = artifact.content.get("gaps", [])
                break
        if gaps:
            break

    if not gaps:
        gaps = ["No gaps identified"]

    reg_type = state.get("regulation_type", "GDPR")

    # Query mem0 for prior findings on these gaps
    mem0 = _get_mem0()
    prior_findings = []
    for gap in gaps[:3]:  # check top 3 gaps
        results = mem0.search(f"{reg_type} {gap}", user_id="demo")
        if results:
            prior_findings.extend(results[:1])

    prior_context = ""
    if prior_findings:
        prior_context = f"\nPrior run findings from memory:\n{json.dumps(prior_findings[:3], indent=2)}"
        logger.info("mem0 hit: %d prior findings for %s gaps", len(prior_findings), reg_type)

    prompt = f"""You are a compliance evidence validator. For each gap, determine:
1. Whether evidence of mitigation exists (likely not for gaps)
2. Severity: critical / high / medium / low
3. Whether this is a repeat finding (if noted in prior findings)

GAPS TO VALIDATE:
{json.dumps(gaps, indent=2)}
{prior_context}

Respond with JSON: {{"validated_gaps": [{{"gap": "...", "severity": "critical|high|medium|low", "repeat_finding": true|false, "notes": "..."}}]}}"""

    try:
        llm = _get_llm()
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        try:
            parsed = json.loads(content)
            validated = parsed.get("validated_gaps", [])
        except json.JSONDecodeError:
            validated = [{"gap": g, "severity": "high", "repeat_finding": False, "notes": ""} for g in gaps]

        artifact = TaskArtifact(
            type="evidence_report",
            content={"validated_gaps": validated, "prior_findings_used": len(prior_findings)},
            metadata={"memory_hit": len(prior_findings) > 0},
        )
        task = A2ATask(
            sender_agent="evidence_validator",
            recipient_agent="risk_scorer",
            artifacts=[artifact],
        )

    except Exception as exc:
        logger.error("evidence_validator_node failed: %s", exc)
        artifact = TaskArtifact(
            type="evidence_report",
            content={"validated_gaps": [{"gap": g, "severity": "high", "repeat_finding": False, "notes": "mock"} for g in gaps[:3]]},
            metadata={"mock": True},
        )
        task = A2ATask(
            sender_agent="evidence_validator",
            recipient_agent="risk_scorer",
            artifacts=[artifact],
            state=TaskState.ERROR,
            error=str(exc),
        )

    sse_event = {
        "type": "agent_update",
        "agent": "evidence_validator",
        "status": task.state,
        "task_id": task.task_id,
        "summary": f"Validated {len(gaps)} gaps, {len(prior_findings)} memory hits",
        "memory_hits": len(prior_findings),
    }

    return {"a2a_tasks": [task], "sse_events": [sse_event]}
