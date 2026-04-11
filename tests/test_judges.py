"""Unit tests for eval judge functions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evals.judges import (
    gaps_identified,
    pipeline_completeness,
    requirements_extracted,
    risk_scores_valid,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def _make_outputs(tasks: list[dict]) -> dict:
    return {"a2a_tasks": tasks, "sse_events": [], "error": None}


def _make_task(sender: str, recipient: str, artifacts: list[dict], mock: bool = False) -> dict:
    art_list = []
    for a in artifacts:
        meta = {"mock": True} if mock else {}
        art_list.append({"type": a["type"], "content": a["content"], "metadata": meta})
    return {
        "sender_agent": sender,
        "recipient_agent": recipient,
        "state": "completed",
        "artifacts": art_list,
        "mcp_calls": [],
        "error": None,
    }


def _full_pipeline_outputs(mock: bool = False) -> dict:
    tasks = [
        _make_task("regulatory_analyst", "policy_mapper",
                   [{"type": "requirements_list", "content": ["Art.5 - minimisation", "Art.17 - erasure", "Art.30 - records"]}], mock),
        _make_task("policy_mapper", "evidence_validator",
                   [{"type": "gap_analysis", "content": {"gaps": ["Art.17 - no erasure procedure"], "covered": ["Art.5"]}}], mock),
        _make_task("evidence_validator", "risk_scorer",
                   [{"type": "evidence_report", "content": {"validated_gaps": [{"gap": "Art.17", "severity": "high"}]}}], mock),
        _make_task("risk_scorer", "executive_reporter",
                   [{"type": "risk_report", "content": {"risks": [{"gap": "Art.17", "risk_score": 7.5, "impact": 8, "likelihood": 7, "control_effectiveness": 3, "priority": "high"}]}}], mock),
        _make_task("executive_reporter", "user",
                   [{"type": "executive_report", "content": {"report": "We found gaps in Art.17.", "summary_stats": {}}}], mock),
    ]
    return _make_outputs(tasks)


# ── pipeline_completeness ─────────────────────────────────────────────────────

def test_pipeline_completeness_passes_all_agents_no_mocks():
    result = pipeline_completeness({}, _full_pipeline_outputs(mock=False))
    assert result == {"key": "pipeline_completeness", "score": 1}


def test_pipeline_completeness_fails_when_mock():
    result = pipeline_completeness({}, _full_pipeline_outputs(mock=True))
    assert result == {"key": "pipeline_completeness", "score": 0}


def test_pipeline_completeness_fails_missing_agent():
    outputs = _make_outputs([
        _make_task("regulatory_analyst", "policy_mapper", [{"type": "requirements_list", "content": []}]),
    ])
    result = pipeline_completeness({}, outputs)
    assert result == {"key": "pipeline_completeness", "score": 0}


# ── requirements_extracted ────────────────────────────────────────────────────

def test_requirements_extracted_passes_three_articles():
    outputs = _make_outputs([
        _make_task("regulatory_analyst", "policy_mapper",
                   [{"type": "requirements_list", "content": ["Art.5 - x", "Art.17 - y", "Art.30 - z"]}]),
    ])
    assert requirements_extracted({}, outputs) == {"key": "requirements_extracted", "score": 1}


def test_requirements_extracted_fails_fewer_than_three():
    outputs = _make_outputs([
        _make_task("regulatory_analyst", "policy_mapper",
                   [{"type": "requirements_list", "content": ["Art.5 - x", "Art.17 - y"]}]),
    ])
    assert requirements_extracted({}, outputs) == {"key": "requirements_extracted", "score": 0}


def test_requirements_extracted_fails_no_article_refs():
    outputs = _make_outputs([
        _make_task("regulatory_analyst", "policy_mapper",
                   [{"type": "requirements_list", "content": ["data minimisation", "right to erasure", "records"]}]),
    ])
    assert requirements_extracted({}, outputs) == {"key": "requirements_extracted", "score": 0}


# ── gaps_identified ───────────────────────────────────────────────────────────

def test_gaps_identified_passes_with_gap():
    outputs = _make_outputs([
        _make_task("policy_mapper", "evidence_validator",
                   [{"type": "gap_analysis", "content": {"gaps": ["Art.17 - no erasure procedure"], "covered": []}}]),
    ])
    assert gaps_identified({}, outputs) == {"key": "gaps_identified", "score": 1}


def test_gaps_identified_fails_empty_gaps():
    outputs = _make_outputs([
        _make_task("policy_mapper", "evidence_validator",
                   [{"type": "gap_analysis", "content": {"gaps": [], "covered": []}}]),
    ])
    assert gaps_identified({}, outputs) == {"key": "gaps_identified", "score": 0}


# ── risk_scores_valid ─────────────────────────────────────────────────────────

def test_risk_scores_valid_passes_correct_schema():
    outputs = _make_outputs([
        _make_task("risk_scorer", "executive_reporter",
                   [{"type": "risk_report", "content": {"risks": [
                       {"gap": "Art.17", "risk_score": 7.5, "impact": 8, "likelihood": 7, "control_effectiveness": 3, "priority": "high"}
                   ]}}]),
    ])
    assert risk_scores_valid({}, outputs) == {"key": "risk_scores_valid", "score": 1}


def test_risk_scores_valid_fails_out_of_range():
    outputs = _make_outputs([
        _make_task("risk_scorer", "executive_reporter",
                   [{"type": "risk_report", "content": {"risks": [
                       {"gap": "Art.17", "risk_score": 15.0, "priority": "high"}
                   ]}}]),
    ])
    assert risk_scores_valid({}, outputs) == {"key": "risk_scores_valid", "score": 0}


def test_risk_scores_valid_fails_invalid_priority():
    outputs = _make_outputs([
        _make_task("risk_scorer", "executive_reporter",
                   [{"type": "risk_report", "content": {"risks": [
                       {"gap": "Art.17", "risk_score": 7.5, "priority": "urgent"}
                   ]}}]),
    ])
    assert risk_scores_valid({}, outputs) == {"key": "risk_scores_valid", "score": 0}
