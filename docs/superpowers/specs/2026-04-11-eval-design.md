# Eval Design: Compliance Demo Pipeline

**Date:** 2026-04-11
**Scope:** LangSmith Evaluations API + pytest CI wrapper for the 5-agent demo track
**Status:** Approved

---

## Goals

1. **Regression gate** — catch code changes that break pipeline output quality (runs in CI via pytest)
2. **LLM quality measurement** — score output quality with LLM-as-judge, tracked over time in LangSmith Experiments

---

## File Structure

```
evals/
  __init__.py
  dataset.py       # creates/upserts LangSmith dataset + examples
  judges.py        # all evaluator functions (heuristic + LLM-as-judge)
  run_evals.py     # CLI: runs evaluate(), prints results, saves JSON

evals/results/     # gitignored — timestamped JSON output from run_evals.py

tests/
  test_evals.py    # pytest CI: calls evaluate(), asserts score thresholds
```

---

## LangSmith Dataset

**Name:** `compliance-demo-eval`

3 examples — `inputs` only, no ground truth (LLM-as-judge does not require it):

| # | document_path | regulation_type | Notes |
|---|---|---|---|
| 1 | `data/samples/gdpr_policy_sample.txt` | GDPR | Existing seeded doc |
| 2 | *(inline text)* | GDPR | Minimal policy, deliberately missing Art.17 + Art.30 procedures |
| 3 | *(inline text)* | SOX | Financial controls policy, missing segregation of duties |

Examples 2 and 3 store their document text inline in the LangSmith example. `dataset.py` writes them to a temp file before passing `document_path` to the pipeline.

`dataset.py` is idempotent — calling it twice upserts rather than duplicating examples.

---

## Target Function

`langsmith.evaluate()` requires a single callable: `inputs -> outputs`.

```python
# evals/run_evals.py
def run_pipeline(inputs: dict) -> dict:
    """Adapter: LangSmith example input → run_compliance_pipeline output."""
    doc_path = inputs["document_path"]

    # Inline examples store text under "document_text" key
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
```

The return value (full LangGraph state dict) is stored as `run.outputs` and passed to every evaluator.

**Note:** LangSmith serializes `run.outputs` to JSON, so `a2a_tasks` arrives in judges as a list of plain dicts, not `A2ATask` Pydantic objects. All judges must use dict key access (e.g. `task["sender_agent"]`), not attribute access.

---

## Evaluators

All defined in `evals/judges.py`. Each has signature `(run: Run, example: Example) -> dict`.

### Heuristic Evaluators (fast, deterministic, no LLM cost)

**`pipeline_completeness`**
- Checks: exactly 5 agent tasks completed, zero artifacts with `metadata.mock == True`
- Score: `1` (pass) or `0` (fail)
- Regression signal: any mock fallback means an LLM call failed silently

**`requirements_extracted`**
- Checks: `regulatory_analyst` artifact contains ≥ 3 items referencing "Art." or an article pattern
- Score: `1` or `0`
- Regression signal: prompt broke, LLM returned garbage, or MCP/RAG failed

**`gaps_identified`**
- Checks: `policy_mapper` artifact `gaps` list has ≥ 1 entry containing an article reference
- Score: `1` or `0`
- Regression signal: gap analysis empty or malformed

**`risk_scores_valid`**
- Checks: all `risk_scorer` risks have `risk_score` in [1, 10] and `priority` in `{critical, high, medium, low}`
- Score: `1` or `0`
- Regression signal: JSON parsing broke or LLM returned out-of-range values

### LLM-as-Judge Evaluator

**`report_coherence`**
- Model: `gpt-4o-mini`, temperature 0
- Inputs passed to judge: executive report text + gaps list from `policy_mapper`
- Rubric (1–5, normalised to 0.0–1.0):
  - 5 — Report explicitly addresses every identified gap with a concrete recommendation
  - 4 — Report addresses most gaps, recommendations present but vague on one
  - 3 — Report mentions gaps but recommendations are generic
  - 2 — Report is superficial, gaps mentioned without recommendations
  - 1 — Report does not reflect the identified gaps at all
- Score: float 0.0–1.0

---

## CI Thresholds (`tests/test_evals.py`)

| Evaluator | Threshold | Meaning |
|---|---|---|
| `pipeline_completeness` | mean ≥ 1.0 | All examples must pass — any mock = regression |
| `requirements_extracted` | mean ≥ 1.0 | All examples must extract ≥ 3 requirements |
| `gaps_identified` | mean ≥ 1.0 | All examples must identify ≥ 1 gap |
| `risk_scores_valid` | mean ≥ 1.0 | All risk scores must be well-formed |
| `report_coherence` | mean ≥ 0.7 | Allows one weaker example across 3 |

pytest fails the suite if any threshold is not met, blocking the PR.

---

## Local CLI (`evals/run_evals.py`)

```
python evals/run_evals.py
```

Prints a rich table of scores per example per evaluator, then saves:
```
evals/results/2026-04-11T16-05-00-eval.json
```

JSON structure:
```json
{
  "run_id": "eval-abc123",
  "timestamp": "2026-04-11T16:05:00Z",
  "dataset": "compliance-demo-eval",
  "summary": {"pipeline_completeness": 1.0, "report_coherence": 0.82, ...},
  "per_example": [...]
}
```

---

## LangSmith Integration

- `langsmith.evaluate()` automatically creates an **Experiment** under the `compliance-demo-eval` dataset in LangSmith
- Each eval run appears as a named experiment (timestamped) in the LangSmith Experiments tab
- Scores are comparable across experiments — score drift over time is visible in the dashboard
- The `report_coherence` LLM call is itself traced as a child run under the experiment

---

## Dependencies

No new packages required beyond what is already installed:
- `langsmith` (v0.7.30, already installed)
- `langchain-openai` (already installed)
- `pytest` (already installed)

---

## Out of Scope

- Golden dataset / reference answers (LLM-as-judge only)
- Per-agent latency benchmarking
- Langfuse integration for evals
- Evaluating the legacy CrewAI agent path (`src/agents/`)
