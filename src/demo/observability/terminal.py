"""Rich terminal panel for live demo visualization.

Shows a 3-panel live layout:
  ┌─────────────────┬──────────────────┬──────────────────┐
  │  Pipeline       │  A2A Messages    │  Memory Events   │
  │  Status         │                  │                  │
  └─────────────────┴──────────────────┴──────────────────┘

Usage:
    panel = AgentTerminalPanel()
    panel.start()
    panel.update_agent("regulatory_analyst", "running")
    panel.log_a2a(task)
    panel.log_memory("hit", "2 prior GDPR findings loaded")
    panel.stop()
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Any

from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Agent pipeline order for display
_AGENTS = [
    "regulatory_analyst",
    "policy_mapper",
    "evidence_validator",
    "risk_scorer",
    "executive_reporter",
]

_STATUS_ICONS = {
    "pending": "⏳",
    "running": "🔄",
    "completed": "✅",
    "error": "❌",
}

_STATUS_COLORS = {
    "pending": "dim white",
    "running": "bold yellow",
    "completed": "bold green",
    "error": "bold red",
}


class AgentTerminalPanel:
    """Live 3-panel Rich terminal display for the demo pipeline."""

    def __init__(self) -> None:
        self._console = Console()
        self._lock = threading.Lock()
        self._agent_status: dict[str, str] = {a: "pending" for a in _AGENTS}
        self._a2a_log: list[str] = []
        self._memory_log: list[str] = []
        self._live: Live | None = None

    def start(self) -> None:
        """Start the live terminal display."""
        self._live = Live(
            self._build_layout(),
            console=self._console,
            refresh_per_second=4,
            screen=False,
        )
        self._live.start()

    def stop(self) -> None:
        """Stop the live display."""
        if self._live:
            self._live.stop()

    def update_agent(self, agent_name: str, status: str) -> None:
        """Update an agent's status in the pipeline panel."""
        with self._lock:
            self._agent_status[agent_name] = status
            if self._live:
                self._live.update(self._build_layout())

    def log_a2a(self, task: Any) -> None:
        """Log an A2A task handoff to the messages panel."""
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            msg = (
                f"[dim]{ts}[/dim] "
                f"[cyan]{task.sender_agent}[/cyan] → "
                f"[green]{task.recipient_agent}[/green] "
                f"[dim]({task.task_id})[/dim]"
            )
            self._a2a_log.append(msg)
            # Keep last 20 messages
            self._a2a_log = self._a2a_log[-20:]
            if self._live:
                self._live.update(self._build_layout())

    def log_memory(self, event_type: str, message: str) -> None:
        """Log a memory event (hit/miss/write) to the memory panel.

        event_type: 'hit' | 'miss' | 'write'
        """
        with self._lock:
            ts = datetime.now().strftime("%H:%M:%S")
            color = {"hit": "yellow", "miss": "dim", "write": "magenta"}.get(event_type, "white")
            icon = {"hit": "🧠", "miss": "○", "write": "💾"}.get(event_type, "•")
            msg = f"[dim]{ts}[/dim] {icon} [{color}]{message}[/{color}]"
            self._memory_log.append(msg)
            self._memory_log = self._memory_log[-20:]
            if self._live:
                self._live.update(self._build_layout())

    def print(self, message: str) -> None:
        """Print a message outside the live panels."""
        if self._live:
            self._live.console.print(message)
        else:
            self._console.print(message)

    def _build_pipeline_table(self) -> Table:
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column("Icon", width=3)
        table.add_column("Agent")
        table.add_column("Status", width=10)
        for agent in _AGENTS:
            status = self._agent_status.get(agent, "pending")
            icon = _STATUS_ICONS.get(status, "•")
            color = _STATUS_COLORS.get(status, "white")
            display_name = agent.replace("_", " ").title()
            table.add_row(icon, f"[{color}]{display_name}[/{color}]", f"[{color}]{status}[/{color}]")
        return table

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_row(
            Layout(name="pipeline", ratio=1),
            Layout(name="a2a", ratio=1),
            Layout(name="memory", ratio=1),
        )

        layout["pipeline"].update(
            Panel(self._build_pipeline_table(), title="[bold blue]Pipeline[/bold blue]", border_style="blue")
        )

        a2a_text = Text.from_markup("\n".join(self._a2a_log) or "[dim]Waiting for agent messages...[/dim]")
        layout["a2a"].update(
            Panel(a2a_text, title="[bold cyan]A2A Messages[/bold cyan]", border_style="cyan")
        )

        mem_text = Text.from_markup("\n".join(self._memory_log) or "[dim]No memory events yet...[/dim]")
        layout["memory"].update(
            Panel(mem_text, title="[bold magenta]Memory Events[/bold magenta]", border_style="magenta")
        )

        return layout
