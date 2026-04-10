"""Google A2A Protocol types for agent-to-agent communication.

These Pydantic models define the envelope format that flows between
LangGraph nodes via shared state. Each agent reads the last A2ATask
in state.a2a_tasks and appends its own.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class TaskState(str):
    """String constants for A2A task lifecycle states."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class TaskArtifact(BaseModel):
    """A single output artifact produced by an agent node."""
    type: str
    content: Any
    metadata: dict[str, Any] = Field(default_factory=dict)


class MCPCall(BaseModel):
    """Record of a Model Context Protocol tool invocation."""
    server: str          # "filesystem" | "github"
    tool: str            # e.g. "read_file", "get_file_contents"
    args: dict[str, Any] = Field(default_factory=dict)


class A2ATask(BaseModel):
    """Agent-to-agent message envelope (Google A2A Protocol shape)."""
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    sender_agent: str
    recipient_agent: str
    state: str = TaskState.COMPLETED
    artifacts: list[TaskArtifact] = Field(default_factory=list)
    mcp_calls: list[MCPCall] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


class AgentCard(BaseModel):
    """Agent capability advertisement (A2A discovery metadata)."""
    name: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
