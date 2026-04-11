"""Evaluator functions for the compliance demo eval suite.

Each evaluator has signature: (inputs, outputs) -> dict
where outputs is the return value of run_pipeline() — the full
LangGraph state dict with a2a_tasks as a list of plain dicts
(LangSmith serializes Pydantic objects to JSON before passing to evaluators).

LangSmith 0.7.x uses parameter name introspection:
  - "inputs"  → example.inputs  (the dataset example inputs dict)
  - "outputs" → run.outputs     (the pipeline's return value dict)

Returns: {"key": str, "score": float}  (score 0 or 1 for heuristics)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _get_tasks(outputs: dict) -> list[dict]:
    return outputs.get("a2a_tasks", []) if outputs else []


def _task_by_agent(tasks: list[dict], agent: str) -> dict | None:
    return next((t for t in tasks if isinstance(t, dict) and t.get("sender_agent") == agent), None)


def _artifacts(task: dict) -> list[dict]:
    return [a for a in task.get("artifacts", []) if isinstance(a, dict)]


# ── Heuristic evaluators ────────────────────────────────────────────────────

def pipeline_completeness(inputs: dict, outputs: dict) -> dict:
    """All 5 agents ran and zero artifacts used the mock fallback."""
    tasks = _get_tasks(outputs)
    expected = {"regulatory_analyst", "policy_mapper", "evidence_validator", "risk_scorer", "executive_reporter"}
    found = {t["sender_agent"] for t in tasks if isinstance(t, dict)}

    has_all = found >= expected
    has_no_mocks = not any(
        a.get("metadata", {}).get("mock", False)
        for t in tasks
        for a in _artifacts(t)
    )
    return {"key": "pipeline_completeness", "score": int(has_all and has_no_mocks)}


def requirements_extracted(inputs: dict, outputs: dict) -> dict:
    """regulatory_analyst produced >= 3 requirements with article references."""
    tasks = _get_tasks(outputs)
    task = _task_by_agent(tasks, "regulatory_analyst")
    if not task:
        return {"key": "requirements_extracted", "score": 0}

    arts = _artifacts(task)
    content = arts[0].get("content", []) if arts else []
    if not isinstance(content, list):
        return {"key": "requirements_extracted", "score": 0}

    article_refs = [
        r for r in content
        if isinstance(r, str) and ("Art." in r or "art." in r.lower() or "Section" in r or "Rule" in r)
    ]
    return {"key": "requirements_extracted", "score": int(len(article_refs) >= 3)}


def gaps_identified(inputs: dict, outputs: dict) -> dict:
    """policy_mapper produced >= 1 gap entry."""
    tasks = _get_tasks(outputs)
    task = _task_by_agent(tasks, "policy_mapper")
    if not task:
        return {"key": "gaps_identified", "score": 0}

    arts = _artifacts(task)
    content = arts[0].get("content", {}) if arts else {}
    gaps = content.get("gaps", []) if isinstance(content, dict) else []
    non_empty = [g for g in gaps if isinstance(g, str) and len(g.strip()) > 3]
    return {"key": "gaps_identified", "score": int(len(non_empty) >= 1)}


def risk_scores_valid(inputs: dict, outputs: dict) -> dict:
    """All risk_scorer risks have score in [1,10] and valid priority label."""
    tasks = _get_tasks(outputs)
    task = _task_by_agent(tasks, "risk_scorer")
    if not task:
        return {"key": "risk_scores_valid", "score": 0}

    arts = _artifacts(task)
    content = arts[0].get("content", {}) if arts else {}
    risks = content.get("risks", []) if isinstance(content, dict) else []
    if not risks:
        return {"key": "risk_scores_valid", "score": 0}

    valid_priorities = {"critical", "high", "medium", "low"}
    all_valid = all(
        isinstance(r, dict)
        and isinstance(r.get("risk_score"), (int, float))
        and 1 <= r["risk_score"] <= 10
        and str(r.get("priority", "")).lower() in valid_priorities
        for r in risks
    )
    return {"key": "risk_scores_valid", "score": int(all_valid)}


# ── LLM-as-judge ────────────────────────────────────────────────────────────

def report_coherence(inputs: dict, outputs: dict) -> dict:
    """LLM-as-judge: does the executive report address the identified gaps?

    Rubric (1–5, normalised to 0.0–1.0):
      5 — Explicitly addresses every gap with concrete recommendations
      4 — Addresses most gaps, recommendations present but vague on one
      3 — Mentions gaps but recommendations are generic
      2 — Superficial, gaps mentioned without recommendations
      1 — Does not reflect the identified gaps at all
    """
    from langchain_openai import ChatOpenAI

    tasks = _get_tasks(outputs)

    er_task = _task_by_agent(tasks, "executive_reporter")
    if not er_task:
        return {"key": "report_coherence", "score": 0.0}

    er_arts = _artifacts(er_task)
    report_text = ""
    if er_arts:
        content = er_arts[0].get("content", {})
        if isinstance(content, dict):
            report_text = content.get("report", "")
        elif isinstance(content, str):
            report_text = content

    pm_task = _task_by_agent(tasks, "policy_mapper")
    gaps: list = []
    if pm_task:
        pm_arts = _artifacts(pm_task)
        if pm_arts:
            pm_content = pm_arts[0].get("content", {})
            if isinstance(pm_content, dict):
                gaps = pm_content.get("gaps", [])

    if not report_text:
        return {"key": "report_coherence", "score": 0.0}

    prompt = f"""You are evaluating the quality of a compliance executive report.

IDENTIFIED GAPS:
{gaps}

EXECUTIVE REPORT:
{report_text[:2000]}

Score the report 1-5:
5 - Explicitly addresses every gap with a concrete recommendation
4 - Addresses most gaps; recommendations present but vague on one
3 - Mentions gaps but recommendations are generic
2 - Superficial; gaps mentioned without recommendations
1 - Does not reflect the identified gaps at all

Respond with ONLY a single integer (1, 2, 3, 4, or 5). No other text."""

    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm.invoke(prompt)
        raw = int(response.content.strip()[0])
        score = (raw - 1) / 4.0  # normalise to 0.0–1.0
    except Exception as exc:
        logger.warning("report_coherence judge failed: %s", exc)
        score = 0.0

    return {"key": "report_coherence", "score": score}
