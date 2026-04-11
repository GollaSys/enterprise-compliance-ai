# Eval Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangSmith Evaluations API + pytest CI eval suite for the 5-agent compliance demo pipeline.

**Architecture:** `evals/dataset.py` seeds a LangSmith dataset, `evals/judges.py` defines 4 heuristic + 1 LLM-as-judge evaluators, `evals/run_evals.py` runs `langsmith.evaluate()` and saves JSON, `tests/test_evals.py` asserts thresholds for CI.

**Tech Stack:** langsmith 0.7.30, langchain-openai, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `evals/__init__.py` | Create | Package marker |
| `evals/dataset.py` | Create | Seed/upsert LangSmith dataset with 3 examples |
| `evals/judges.py` | Create | 5 evaluator functions (4 heuristic + 1 LLM-as-judge) |
| `evals/run_evals.py` | Create | CLI: run evaluate(), print table, save JSON |
| `tests/test_evals.py` | Create | pytest CI: assert score thresholds |
| `.gitignore` | Modify | Ignore `evals/results/` |

---

## Task 1: Package skeleton + dataset seeder

**Files:**
- Create: `evals/__init__.py`
- Create: `evals/dataset.py`

- [ ] **Step 1: Create `evals/__init__.py`**

```python
# evals/__init__.py
```

- [ ] **Step 2: Create `evals/dataset.py`**

```python
"""Seed the LangSmith eval dataset for the compliance demo pipeline.

Run directly to create/upsert the dataset:
    python evals/dataset.py
"""
from langsmith import Client

DATASET_NAME = "compliance-demo-eval"

# Example 2: minimal GDPR policy — deliberately missing Art.17 + Art.30
_GDPR_MINIMAL = """ACME CORP — DATA PROTECTION POLICY v0.1

We collect personal data (name, email, IP address) to provide our service.
Data is stored on secure servers in the EU.
We share data with payment processors and analytics vendors where required.
Users can contact privacy@acme.com to request a copy of their data.
We retain data for as long as the account is active.
We comply with applicable data protection laws.
"""

# Example 3: SOX financial controls — missing segregation of duties
_SOX_FINANCIAL = """FINANCIAL CONTROLS POLICY v1.0

The finance department manages all financial transactions.
One senior accountant handles both payment approvals and disbursements.
Monthly reconciliations are performed by the same team that processes payments.
We conduct an annual external audit. All transactions are logged in our ERP.
Journal entries are approved by the CFO on a quarterly basis.
Access to the general ledger is restricted to finance staff.
"""

_EXAMPLES = [
    {
        "inputs": {
            "document_path": "data/samples/gdpr_policy_sample.txt",
            "regulation_type": "GDPR",
        }
    },
    {
        "inputs": {
            "document_text": _GDPR_MINIMAL,
            "regulation_type": "GDPR",
        }
    },
    {
        "inputs": {
            "document_text": _SOX_FINANCIAL,
            "regulation_type": "SOX",
        }
    },
]


def seed_dataset() -> str:
    """Create or verify the LangSmith eval dataset. Returns dataset name."""
    client = Client()
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        print(f"Dataset '{DATASET_NAME}' already exists — skipping seed")
        return DATASET_NAME

    dataset = client.create_dataset(
        DATASET_NAME,
        description="Compliance demo pipeline eval dataset — 3 examples (GDPR x2, SOX x1)",
    )
    for ex in _EXAMPLES:
        client.create_example(inputs=ex["inputs"], dataset_id=dataset.id)
    print(f"Created dataset '{DATASET_NAME}' with {len(_EXAMPLES)} examples")
    return DATASET_NAME


if __name__ == "__main__":
    import os, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv(override=True)
    seed_dataset()
```

- [ ] **Step 3: Smoke-test dataset seeder**

```bash
source venv/bin/activate
python evals/dataset.py
```

Expected output:
```
Created dataset 'compliance-demo-eval' with 3 examples
```

Running again should print:
```
Dataset 'compliance-demo-eval' already exists — skipping seed
```

- [ ] **Step 4: Commit**

```bash
git add evals/__init__.py evals/dataset.py
git commit -m "feat: add eval dataset seeder (compliance-demo-eval, 3 examples)"
```

---

## Task 2: Heuristic evaluators

**Files:**
- Create: `evals/judges.py`

All judges receive `(row: ExperimentResultRow)` — langsmith 0.7.x passes the full row dict.
`row["run"].outputs` contains the pipeline state with `a2a_tasks` as a **list of dicts** (JSON-serialized).

- [ ] **Step 1: Create `evals/judges.py` with the 4 heuristic evaluators**

```python
"""Evaluator functions for the compliance demo eval suite.

Each evaluator has signature: (inputs, outputs) -> dict
where outputs is the return value of run_pipeline() — the full
LangGraph state dict with a2a_tasks as a list of plain dicts
(LangSmith serializes Pydantic objects to JSON before passing to evaluators).

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
```

- [ ] **Step 2: Write unit tests for heuristic judges**

Create `tests/test_judges.py`:

```python
"""Unit tests for eval judge functions."""
import pytest
from evals.judges import (
    pipeline_completeness,
    requirements_extracted,
    gaps_identified,
    risk_scores_valid,
)

# ── helpers ─────────────────────────────────────────────────────────────────

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


ALL_AGENTS = ["regulatory_analyst", "policy_mapper", "evidence_validator", "risk_scorer", "executive_reporter"]

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


# ── pipeline_completeness ────────────────────────────────────────────────────

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


# ── requirements_extracted ───────────────────────────────────────────────────

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


# ── gaps_identified ──────────────────────────────────────────────────────────

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


# ── risk_scores_valid ────────────────────────────────────────────────────────

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
```

- [ ] **Step 3: Run unit tests — verify they pass**

```bash
source venv/bin/activate
python -m pytest tests/test_judges.py -v
```

Expected: all 12 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add evals/judges.py tests/test_judges.py
git commit -m "feat: add heuristic eval judges + unit tests"
```

---

## Task 3: LLM-as-judge (report_coherence)

**Files:**
- Modify: `evals/judges.py` — append `report_coherence` function

- [ ] **Step 1: Append `report_coherence` to `evals/judges.py`**

Add at the end of the file:

```python

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
```

- [ ] **Step 2: Smoke-test report_coherence with a fake outputs dict**

```bash
source venv/bin/activate && python3 -c "
import sys; sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv(override=True)
from evals.judges import report_coherence

outputs = {
  'a2a_tasks': [
    {'sender_agent': 'policy_mapper', 'recipient_agent': 'evidence_validator', 'artifacts': [
        {'type': 'gap_analysis', 'content': {'gaps': ['Art.17 - no erasure procedure'], 'covered': []}, 'metadata': {}}
    ]},
    {'sender_agent': 'executive_reporter', 'recipient_agent': 'user', 'artifacts': [
        {'type': 'executive_report', 'content': {'report': 'We must implement an Art.17 erasure procedure immediately. Recommend appointing a DPO to own this.'}, 'metadata': {}}
    ]},
  ]
}
result = report_coherence({}, outputs)
print('score:', result['score'])
assert 0.0 <= result['score'] <= 1.0, 'score out of range'
print('OK')
"
```

Expected: prints a score between 0.0 and 1.0 and `OK`.

- [ ] **Step 3: Commit**

```bash
git add evals/judges.py
git commit -m "feat: add LLM-as-judge report_coherence evaluator"
```

---

## Task 4: CLI run script

**Files:**
- Create: `evals/run_evals.py`

- [ ] **Step 1: Create `evals/run_evals.py`**

```python
#!/usr/bin/env python3
"""CLI: run the compliance demo eval suite.

Usage:
    python evals/run_evals.py

Prints a score table per evaluator and saves timestamped JSON to evals/results/.
Also creates a LangSmith Experiment visible in the dataset's Experiments tab.
"""
import json
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from langsmith import evaluate
from evals.dataset import seed_dataset, DATASET_NAME
from evals.judges import (
    gaps_identified,
    pipeline_completeness,
    report_coherence,
    requirements_extracted,
    risk_scores_valid,
)
from src.demo.graph.workflow import run_compliance_pipeline

EVALUATORS = [
    pipeline_completeness,
    requirements_extracted,
    gaps_identified,
    risk_scores_valid,
    report_coherence,
]

THRESHOLDS: dict[str, float] = {
    "pipeline_completeness": 1.0,
    "requirements_extracted": 1.0,
    "gaps_identified": 1.0,
    "risk_scores_valid": 1.0,
    "report_coherence": 0.7,
}


def run_pipeline(inputs: dict) -> dict:
    """Adapter: LangSmith example input → run_compliance_pipeline state output."""
    doc_path = inputs.get("document_path", "")

    if "document_text" in inputs:
        tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w")
        tmp.write(inputs["document_text"])
        tmp.close()
        doc_path = tmp.name

    state = {
        "regulation_type": inputs["regulation_type"],
        "document_path": doc_path,
        "run_id": f"eval-{uuid.uuid4().hex[:8]}",
        "a2a_tasks": [],
        "sse_events": [],
        "long_term_context": [],
        "short_term_memory": {},
        "error": None,
    }
    return run_compliance_pipeline(state)


def main() -> int:
    seed_dataset()

    prefix = f"eval-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    print(f"\nRunning experiment: {prefix}")
    print(f"Dataset:            {DATASET_NAME}")
    print(f"Evaluators:         {[e.__name__ for e in EVALUATORS]}\n")

    results = evaluate(
        run_pipeline,
        data=DATASET_NAME,
        evaluators=EVALUATORS,
        experiment_prefix=prefix,
        max_concurrency=1,
    )

    # Aggregate scores from ExperimentResultRow objects
    scores_by_key: dict[str, list[float]] = {}
    per_example = []

    for row in results:
        example_scores: dict[str, float] = {}
        for fb in row["evaluation_results"]["results"]:
            key = fb.key
            score = float(fb.score) if fb.score is not None else 0.0
            example_scores[key] = score
            scores_by_key.setdefault(key, []).append(score)
        per_example.append({
            "example_id": str(row["example"].id),
            "scores": example_scores,
        })

    means = {k: sum(v) / len(v) for k, v in scores_by_key.items()}

    # Print results table
    print(f"\n{'=' * 56}")
    print(f"{'EVAL RESULTS':^56}")
    print(f"{'=' * 56}")
    print(f"{'Evaluator':<32} {'Mean':>6}  {'Threshold':>9}  Status")
    print(f"{'-' * 56}")

    all_pass = True
    for key in THRESHOLDS:
        mean = means.get(key, 0.0)
        threshold = THRESHOLDS[key]
        passed = mean >= threshold
        if not passed:
            all_pass = False
        status = "PASS" if passed else "FAIL"
        print(f"{key:<32} {mean:>6.3f}  {threshold:>9.1f}  {status}")

    print(f"{'=' * 56}")
    overall = "PASS" if all_pass else "FAIL"
    print(f"{'Overall: ' + overall:>56}")
    print(f"{'LangSmith URL: ' + (results.url or 'n/a'):>56}\n")

    # Save JSON
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_path = results_dir / f"{ts}-eval.json"
    out_path.write_text(json.dumps({
        "experiment": prefix,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": DATASET_NAME,
        "langsmith_url": results.url,
        "summary": means,
        "thresholds": THRESHOLDS,
        "overall_pass": all_pass,
        "per_example": per_example,
    }, indent=2))
    print(f"Results saved → {out_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Update `.gitignore` to exclude result files**

Add to `.gitignore`:
```
evals/results/
```

- [ ] **Step 3: Commit**

```bash
git add evals/run_evals.py .gitignore
git commit -m "feat: add eval CLI runner (run_evals.py)"
```

---

## Task 5: pytest CI wrapper

**Files:**
- Create: `tests/test_evals.py`

- [ ] **Step 1: Create `tests/test_evals.py`**

```python
"""CI eval suite: runs the full LangSmith evaluation and asserts score thresholds.

Mark: pytest -m eval   (slow — makes real LLM calls)
Skip in fast CI with: pytest -m "not eval"
"""
import uuid
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

THRESHOLDS = {
    "pipeline_completeness": 1.0,
    "requirements_extracted": 1.0,
    "gaps_identified": 1.0,
    "risk_scores_valid": 1.0,
    "report_coherence": 0.7,
}


@pytest.mark.eval
def test_eval_suite_passes_thresholds():
    """Full eval suite: run all 5 evaluators across 3 examples, assert thresholds."""
    from dotenv import load_dotenv
    load_dotenv(override=True)

    from langsmith import evaluate
    from evals.dataset import seed_dataset, DATASET_NAME
    from evals.judges import (
        gaps_identified,
        pipeline_completeness,
        report_coherence,
        requirements_extracted,
        risk_scores_valid,
    )
    from evals.run_evals import run_pipeline

    seed_dataset()

    results = evaluate(
        run_pipeline,
        data=DATASET_NAME,
        evaluators=[
            pipeline_completeness,
            requirements_extracted,
            gaps_identified,
            risk_scores_valid,
            report_coherence,
        ],
        experiment_prefix=f"ci-{uuid.uuid4().hex[:8]}",
        max_concurrency=1,
    )

    scores_by_key: dict[str, list[float]] = {}
    for row in results:
        for fb in row["evaluation_results"]["results"]:
            score = float(fb.score) if fb.score is not None else 0.0
            scores_by_key.setdefault(fb.key, []).append(score)

    means = {k: sum(v) / len(v) for k, v in scores_by_key.items()}

    failures = [
        f"  {key}: mean={means.get(key, 0.0):.3f} < threshold={threshold}"
        for key, threshold in THRESHOLDS.items()
        if means.get(key, 0.0) < threshold
    ]

    assert not failures, "Eval thresholds not met:\n" + "\n".join(failures)
```

- [ ] **Step 2: Register `eval` mark in `pytest.ini` or `pyproject.toml`**

Check if `pytest.ini` exists:
```bash
ls pytest.ini pyproject.toml setup.cfg 2>/dev/null
```

If none exist, create `pytest.ini`:
```ini
[pytest]
markers =
    eval: slow eval tests that make real LLM calls (deselect with -m "not eval")
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_evals.py pytest.ini
git commit -m "feat: add pytest CI eval wrapper (test_evals.py)"
```

---

## Task 6: Run the full eval suite end-to-end

- [ ] **Step 1: Run unit tests to confirm judges are correct**

```bash
source venv/bin/activate
python -m pytest tests/test_judges.py -v
```

Expected: 12/12 PASS.

- [ ] **Step 2: Run the CLI eval**

```bash
source venv/bin/activate
python evals/run_evals.py
```

Expected: score table printed, all heuristic judges PASS, `report_coherence` ≥ 0.7, JSON saved to `evals/results/`.

- [ ] **Step 3: Run the pytest eval**

```bash
source venv/bin/activate
python -m pytest tests/test_evals.py -v -m eval
```

Expected: `test_eval_suite_passes_thresholds` PASS.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete eval suite — dataset, judges, CLI, pytest CI"
```
