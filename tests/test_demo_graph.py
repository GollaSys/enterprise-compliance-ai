"""Tests for the demo agent graph: A2A types, state, mem0, MCP, agents, workflow."""
import pytest
from datetime import datetime, timezone


# ── Task 2: A2A Protocol Types ─────────────────────────────────────────────

class TestA2ATypes:
    def test_task_artifact_creates_with_required_fields(self):
        from src.demo.a2a_types import TaskArtifact
        artifact = TaskArtifact(type="requirements_list", content=["Art.5", "Art.17"])
        assert artifact.type == "requirements_list"
        assert artifact.content == ["Art.5", "Art.17"]
        assert artifact.metadata == {}

    def test_task_artifact_accepts_metadata(self):
        from src.demo.a2a_types import TaskArtifact
        artifact = TaskArtifact(
            type="gap_analysis",
            content={"gaps": ["Art.17"]},
            metadata={"source_doc": "policy.pdf", "rag_chunks_used": 4},
        )
        assert artifact.metadata["source_doc"] == "policy.pdf"

    def test_mcp_call_model(self):
        from src.demo.a2a_types import MCPCall
        call = MCPCall(server="filesystem", tool="read_file", args={"path": "./data/policy.pdf"})
        assert call.server == "filesystem"
        assert call.tool == "read_file"

    def test_a2a_task_defaults(self):
        from src.demo.a2a_types import A2ATask, TaskArtifact, TaskState
        artifact = TaskArtifact(type="test", content="hello")
        task = A2ATask(
            sender_agent="regulatory_analyst",
            recipient_agent="policy_mapper",
            artifacts=[artifact],
        )
        assert task.state == TaskState.COMPLETED
        assert task.task_id.startswith("task-")
        assert isinstance(task.timestamp, datetime)
        assert task.mcp_calls == []

    def test_a2a_task_state_values(self):
        from src.demo.a2a_types import TaskState
        assert TaskState.PENDING == "pending"
        assert TaskState.IN_PROGRESS == "in_progress"
        assert TaskState.COMPLETED == "completed"
        assert TaskState.ERROR == "error"

    def test_a2a_task_serialises_to_dict(self):
        from src.demo.a2a_types import A2ATask, TaskArtifact
        artifact = TaskArtifact(type="report", content={"score": 7})
        task = A2ATask(
            sender_agent="risk_scorer",
            recipient_agent="executive_reporter",
            artifacts=[artifact],
        )
        d = task.model_dump()
        assert d["sender_agent"] == "risk_scorer"
        assert isinstance(d["timestamp"], datetime)

    def test_agent_card_model(self):
        from src.demo.a2a_types import AgentCard
        card = AgentCard(
            name="regulatory_analyst",
            description="Extracts GDPR requirements from documents",
            capabilities=["rag", "mcp_filesystem", "mcp_github"],
            input_schema={"document_path": "str"},
            output_schema={"requirements": "list"},
        )
        assert card.name == "regulatory_analyst"
        assert "rag" in card.capabilities
