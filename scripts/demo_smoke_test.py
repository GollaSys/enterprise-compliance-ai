#!/usr/bin/env python3
"""Demo smoke test — runs the full compliance pipeline with real LLM calls.

Usage:
    source venv/bin/activate
    python scripts/demo_smoke_test.py

Expected runtime: ~30-60s depending on OpenAI latency.
Prints PASS/FAIL per step. Exit code 0 = all passed, 1 = any failed.
"""
import sys
import time
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


def _check(label: str, condition: bool, detail: str = "") -> bool:
    icon = "✅ PASS" if condition else "❌ FAIL"
    print(f"  {icon}  {label}" + (f" — {detail}" if detail else ""))
    return condition


def run_smoke_test():
    print("\n" + "═" * 60)
    print("  Enterprise Compliance AI — Demo Smoke Test")
    print("═" * 60)

    results = []
    t_start = time.time()

    # ── Step 1: A2A types import ────────────────────────────────
    print("\n[1/6] A2A Protocol Types")
    try:
        from src.demo.a2a_types import A2ATask, TaskArtifact, AgentCard
        task = A2ATask(
            sender_agent="test", recipient_agent="test",
            artifacts=[TaskArtifact(type="test", content="hello")]
        )
        results.append(_check("A2ATask creates and serialises", task.task_id.startswith("task-")))
    except Exception as e:
        results.append(_check("A2A types import", False, str(e)))

    # ── Step 2: MCP client + regulation text ───────────────────
    print("\n[2/6] MCP Client + Regulation Text")
    try:
        from src.demo.mcp.client import MCPClient
        client = MCPClient()
        gdpr_text = client.get_regulation_text("GDPR")
        results.append(_check("GDPR regulation text loaded", len(gdpr_text) > 100,
                               f"{len(gdpr_text)} chars"))
        doc_text = client.read_file("data/samples/gdpr_policy_sample.txt")
        results.append(_check("Sample GDPR doc readable", len(doc_text) > 100,
                               f"{len(doc_text)} chars"))
    except Exception as e:
        results.append(_check("MCP client", False, str(e)))

    # ── Step 3: mem0 client ─────────────────────────────────────
    print("\n[3/6] mem0 Long-Term Memory")
    try:
        from src.demo.memory.mem0_client import Mem0Client
        mem = Mem0Client()
        ok = mem.add("smoke_test: GDPR test finding, score 7.0", user_id="smoke_test")
        results.append(_check("mem0.add() returns bool", isinstance(ok, bool)))
        results_list = mem.search("GDPR test finding", user_id="smoke_test")
        results.append(_check("mem0.search() returns list", isinstance(results_list, list)))
    except Exception as e:
        results.append(_check("mem0 client", False, str(e)))

    # ── Step 4: Workflow compilation ────────────────────────────
    print("\n[4/6] LangGraph Workflow")
    try:
        from src.demo.graph.workflow import build_workflow
        app = build_workflow()
        graph_repr = str(app.get_graph())
        all_nodes_present = all(
            n in graph_repr for n in
            ["regulatory_analyst", "policy_mapper", "evidence_validator",
             "risk_scorer", "executive_reporter"]
        )
        results.append(_check("All 5 agent nodes compiled", all_nodes_present))
    except Exception as e:
        results.append(_check("Workflow compilation", False, str(e)))

    # ── Step 5: Full pipeline (real LLM) ───────────────────────
    print("\n[5/6] Full Pipeline (real LLM calls)")
    print("       This may take 30-60s...")
    try:
        from src.demo.graph.workflow import run_compliance_pipeline
        run_id = f"smoke-{uuid.uuid4().hex[:6]}"
        initial_state = {
            "regulation_type": "GDPR",
            "document_path": "data/samples/gdpr_policy_sample.txt",
            "a2a_tasks": [],
            "sse_events": [],
            "long_term_context": [],
            "short_term_memory": {},
            "run_id": run_id,
            "error": None,
        }
        t_pipeline = time.time()
        final_state = run_compliance_pipeline(initial_state)
        elapsed = time.time() - t_pipeline

        a2a_tasks = final_state.get("a2a_tasks", [])
        sse_events = final_state.get("sse_events", [])
        agent_names = [t.sender_agent for t in a2a_tasks]

        results.append(_check("Pipeline completes without error",
                               final_state.get("error") is None))
        results.append(_check("All 5 agents ran",
                               len(a2a_tasks) == 5,
                               f"got {len(a2a_tasks)} tasks"))
        results.append(_check("regulatory_analyst ran", "regulatory_analyst" in agent_names))
        results.append(_check("executive_reporter ran", "executive_reporter" in agent_names))
        results.append(_check("SSE events emitted", len(sse_events) >= 5,
                               f"{len(sse_events)} events"))
        results.append(_check(f"Pipeline runtime reasonable",
                               elapsed < 120, f"{elapsed:.1f}s"))

        # Check executive report content
        report_tasks = [t for t in a2a_tasks if t.sender_agent == "executive_reporter"]
        if report_tasks:
            report_artifact = next(
                (a for a in report_tasks[0].artifacts if a.type == "executive_report"), None
            )
            if report_artifact:
                report_text = report_artifact.content.get("report", "")
                results.append(_check("Executive report has content",
                                       len(report_text) > 50, f"{len(report_text)} chars"))

        print(f"\n       ⏱  Pipeline completed in {elapsed:.1f}s")

    except Exception as e:
        results.append(_check("Full pipeline run", False, str(e)))
        import traceback
        traceback.print_exc()

    # ── Step 6: API endpoints ───────────────────────────────────
    print("\n[6/6] API Endpoints")
    try:
        from fastapi.testclient import TestClient
        from src.api.main_simple import app
        tc = TestClient(app)

        r = tc.get("/health")
        results.append(_check("GET /health", r.status_code == 200))
        r = tc.get("/api/v2/demo/health")
        results.append(_check("GET /api/v2/demo/health", r.status_code == 200))
        r = tc.get("/api/v2/demo/agents")
        results.append(_check("GET /api/v2/demo/agents returns 5 agents",
                               r.status_code == 200 and len(r.json()) == 5,
                               f"got {len(r.json()) if r.status_code == 200 else r.status_code}"))
    except Exception as e:
        results.append(_check("API endpoints", False, str(e)))

    # ── Summary ─────────────────────────────────────────────────
    total = time.time() - t_start
    passed = sum(results)
    failed = len(results) - passed

    print("\n" + "═" * 60)
    print(f"  Results: {passed}/{len(results)} passed  ({total:.1f}s total)")
    if failed:
        print(f"  ❌ {failed} test(s) FAILED")
    else:
        print("  ✅ All tests PASSED — demo is ready!")
    print("═" * 60 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_smoke_test())
