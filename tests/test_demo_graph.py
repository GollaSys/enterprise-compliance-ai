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


# ── Task 3: ComplianceState + mem0 client ─────────────────────────────────

class TestComplianceState:
    def test_state_initial_structure(self):
        from src.demo.graph.state import ComplianceState
        # TypedDict — instantiate as a plain dict and verify keys exist
        state: ComplianceState = {
            "regulation_type": "GDPR",
            "document_path": "./data/policy.pdf",
            "a2a_tasks": [],
            "sse_events": [],
            "long_term_context": [],
            "short_term_memory": {},
            "run_id": "run-abc",
            "error": None,
        }
        assert state["regulation_type"] == "GDPR"
        assert state["a2a_tasks"] == []

    def test_state_a2a_tasks_is_annotated_list(self):
        """a2a_tasks uses operator.add reducer — appends, never overwrites."""
        import operator
        from typing import get_type_hints, Annotated
        from src.demo.graph.state import ComplianceState
        hints = get_type_hints(ComplianceState, include_extras=True)
        a2a_hint = hints["a2a_tasks"]
        # Annotated[list[...], operator.add] — check it's Annotated
        assert hasattr(a2a_hint, "__metadata__"), "a2a_tasks must be Annotated with reducer"
        assert a2a_hint.__metadata__[0] is operator.add


class TestMem0Client:
    def test_search_returns_list_on_success(self, tmp_path):
        from src.demo.memory.mem0_client import Mem0Client
        client = Mem0Client(data_path=str(tmp_path))
        results = client.search("GDPR data retention", user_id="demo")
        assert isinstance(results, list)

    def test_search_returns_empty_list_on_failure(self, tmp_path):
        """mem0 failures must be silent — demo never crashes from memory errors."""
        from src.demo.memory.mem0_client import Mem0Client
        client = Mem0Client(data_path=str(tmp_path))
        # Force failure by making data_path invalid after init
        client._memory = None
        results = client.search("anything", user_id="demo")
        assert results == []

    def test_add_returns_bool(self, tmp_path):
        from src.demo.memory.mem0_client import Mem0Client
        client = Mem0Client(data_path=str(tmp_path))
        ok = client.add("GDPR gap: data retention, score 8.2", user_id="demo")
        assert isinstance(ok, bool)

    def test_add_returns_false_on_failure(self, tmp_path):
        from src.demo.memory.mem0_client import Mem0Client
        client = Mem0Client(data_path=str(tmp_path))
        client._memory = None
        ok = client.add("anything", user_id="demo")
        assert ok is False
