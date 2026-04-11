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
    url = results.url or "n/a"
    print(f"LangSmith: {url}\n")

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
