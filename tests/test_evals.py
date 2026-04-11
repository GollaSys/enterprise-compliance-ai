"""CI eval suite: runs the full LangSmith evaluation and asserts score thresholds.

Mark: pytest -m eval   (slow — makes real LLM calls)
Skip in fast CI with: pytest -m "not eval"
"""
import sys
import uuid
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
