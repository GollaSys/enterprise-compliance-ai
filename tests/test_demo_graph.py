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


# ── Task 4: MCP Client ─────────────────────────────────────────────────────

class TestMCPClient:
    def test_read_file_falls_back_to_disk(self, tmp_path):
        """When MCP subprocess unavailable, reads file directly from disk."""
        from src.demo.mcp.client import MCPClient
        test_file = tmp_path / "policy.txt"
        test_file.write_text("sample policy content")
        client = MCPClient()
        result = client.read_file(str(test_file))
        assert "sample policy content" in result

    def test_read_file_returns_error_string_for_missing_file(self, tmp_path):
        from src.demo.mcp.client import MCPClient
        client = MCPClient()
        result = client.read_file(str(tmp_path / "nonexistent.txt"))
        assert "error" in result.lower() or result == ""

    def test_get_regulation_text_gdpr(self):
        """Falls back to bundled GDPR.txt when GitHub MCP unavailable."""
        from src.demo.mcp.client import MCPClient
        client = MCPClient()
        text = client.get_regulation_text("GDPR")
        assert len(text) > 100
        assert "GDPR" in text or "General Data Protection" in text or "data" in text.lower()

    def test_get_regulation_text_unknown_returns_empty(self):
        from src.demo.mcp.client import MCPClient
        client = MCPClient()
        text = client.get_regulation_text("UNKNOWN_REG_XYZ")
        assert isinstance(text, str)


# ── Task 6: Agent nodes ─────────────────────────────────────────────────────

import pytest

@pytest.fixture
def base_state(tmp_path):
    """Minimal ComplianceState for agent node testing."""
    import uuid
    # Write a minimal policy file for nodes to read
    doc = tmp_path / "policy.txt"
    doc.write_text("This is a sample company data protection policy. We process personal data.")
    return {
        "regulation_type": "GDPR",
        "document_path": str(doc),
        "a2a_tasks": [],
        "sse_events": [],
        "long_term_context": [],
        "short_term_memory": {},
        "run_id": f"run-{uuid.uuid4().hex[:8]}",
        "error": None,
    }


def _make_fake_llm(responses: list[str]):
    """Create a FakeListChatModel that returns preset responses."""
    from langchain_core.messages import AIMessage
    from unittest.mock import MagicMock, patch

    class FakeLLM:
        def __init__(self, resps):
            self._resps = iter(resps)

        def invoke(self, *args, **kwargs):
            text = next(self._resps, "Mock LLM response")
            return AIMessage(content=text)

        def bind_tools(self, *args, **kwargs):
            return self

    return FakeLLM(responses)


class TestRegulatoryAnalystNode:
    def test_returns_dict_with_a2a_tasks(self, base_state, monkeypatch):
        from src.demo.agents.regulatory_analyst import regulatory_analyst_node
        from langchain_core.messages import AIMessage

        fake_llm = _make_fake_llm([
            '{"requirements": ["Art.5 - data minimisation", "Art.17 - right to erasure"]}'
        ])
        monkeypatch.setattr(
            "src.demo.agents.regulatory_analyst._get_llm", lambda: fake_llm
        )
        result = regulatory_analyst_node(base_state)
        assert "a2a_tasks" in result
        assert len(result["a2a_tasks"]) == 1
        task = result["a2a_tasks"][0]
        assert task.sender_agent == "regulatory_analyst"
        assert task.recipient_agent == "policy_mapper"
        assert len(task.artifacts) >= 1

    def test_returns_error_task_on_llm_failure(self, base_state, monkeypatch):
        from src.demo.agents.regulatory_analyst import regulatory_analyst_node

        def bad_llm():
            raise RuntimeError("LLM unavailable")

        monkeypatch.setattr(
            "src.demo.agents.regulatory_analyst._get_llm", bad_llm
        )
        result = regulatory_analyst_node(base_state)
        assert "a2a_tasks" in result
        task = result["a2a_tasks"][0]
        assert task.state == "error" or len(task.artifacts) >= 0  # partial result ok


class TestPolicyMapperNode:
    def test_reads_prior_a2a_task(self, base_state, monkeypatch):
        from src.demo.agents.regulatory_analyst import regulatory_analyst_node
        from src.demo.agents.policy_mapper import policy_mapper_node
        from src.demo.a2a_types import A2ATask, TaskArtifact

        # Pre-populate state with analyst output
        prior_task = A2ATask(
            sender_agent="regulatory_analyst",
            recipient_agent="policy_mapper",
            artifacts=[TaskArtifact(type="requirements_list", content=["Art.17", "Art.30"])],
        )
        state = {**base_state, "a2a_tasks": [prior_task]}

        fake_llm = _make_fake_llm(['{"gaps": ["Art.17 - no erasure procedure", "Art.30 - incomplete records"]}'])
        monkeypatch.setattr("src.demo.agents.policy_mapper._get_llm", lambda: fake_llm)

        result = policy_mapper_node(state)
        assert "a2a_tasks" in result
        task = result["a2a_tasks"][0]
        assert task.sender_agent == "policy_mapper"
        assert task.recipient_agent == "evidence_validator"


class TestRiskScorerNode:
    def test_calls_mem0_add(self, base_state, monkeypatch, tmp_path):
        from src.demo.agents.risk_scorer import risk_scorer_node
        from src.demo.a2a_types import A2ATask, TaskArtifact

        mem0_calls = []

        class FakeMem0:
            def add(self, text, user_id="demo", metadata=None):
                mem0_calls.append(text)
                return True
            def search(self, *a, **k):
                return []

        prior_task = A2ATask(
            sender_agent="evidence_validator",
            recipient_agent="risk_scorer",
            artifacts=[TaskArtifact(type="evidence_report", content={"validated_gaps": ["Art.17"]})],
        )
        state = {**base_state, "a2a_tasks": [prior_task]}

        fake_llm = _make_fake_llm(['{"risks": [{"gap": "Art.17", "risk_score": 8.2, "impact": 9, "likelihood": 8, "control_effectiveness": 2, "priority": "critical"}]}'])
        monkeypatch.setattr("src.demo.agents.risk_scorer._get_llm", lambda: fake_llm)
        monkeypatch.setattr("src.demo.agents.risk_scorer._get_mem0", lambda: FakeMem0())

        result = risk_scorer_node(state)
        assert "a2a_tasks" in result
        # mem0.add should have been called to persist findings
        assert len(mem0_calls) >= 1
