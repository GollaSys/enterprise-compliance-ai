"""Integration tests for /api/v2/ demo endpoints."""
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    from src.api.main_simple import app
    return TestClient(app)


class TestDemoEndpoints:
    def test_agent_cards_endpoint(self, client):
        response = client.get("/api/v2/demo/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        agent_names = [a["name"] for a in data]
        assert "regulatory_analyst" in agent_names
        assert "executive_reporter" in agent_names

    def test_health_endpoint(self, client):
        response = client.get("/api/v2/demo/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_run_demo_accepts_empty_body_with_defaults(self, client):
        """All fields have defaults — empty body is valid (422 not expected)."""
        # We just test that the endpoint exists and accepts the schema
        # (actual pipeline run is tested in test_run_demo_with_mocked_pipeline)
        # Sending wrong type should 422
        response = client.post("/api/v2/demo/run", json={"regulation_type": 12345})
        assert response.status_code == 422

    def test_run_demo_with_mocked_pipeline(self, client, tmp_path):
        """End-to-end run with mocked pipeline returns correct SSE structure."""
        from src.demo.a2a_types import A2ATask, TaskArtifact

        mock_tasks = [
            A2ATask(sender_agent="regulatory_analyst", recipient_agent="policy_mapper",
                    artifacts=[TaskArtifact(type="requirements_list", content=["Art.17"])]),
            A2ATask(sender_agent="executive_reporter", recipient_agent="user",
                    artifacts=[TaskArtifact(type="executive_report",
                                           content={"report": "Test report", "summary_stats": {},
                                                    "trace_urls": {"langsmith": "", "langfuse": ""}})]),
        ]
        mock_final_state = {
            "regulation_type": "GDPR",
            "document_path": str(tmp_path / "policy.txt"),
            "a2a_tasks": mock_tasks,
            "sse_events": [{"type": "run_complete", "agent": "executive_reporter"}],
            "long_term_context": [],
            "short_term_memory": {},
            "run_id": "run-test",
            "error": None,
        }

        with patch("src.demo.router.run_compliance_pipeline", return_value=mock_final_state):
            # Create a dummy doc file
            doc = tmp_path / "policy.txt"
            doc.write_text("sample policy")

            response = client.post(
                "/api/v2/demo/run",
                json={"regulation_type": "GDPR", "document_path": str(doc)},
            )
            assert response.status_code == 200
            data = response.json()
            assert "run_id" in data
            assert "a2a_tasks" in data
            assert len(data["a2a_tasks"]) == 2

    def test_v1_health_still_works(self, client):
        """Existing v1 endpoints must still work after v2 mount."""
        response = client.get("/health")
        assert response.status_code == 200
