from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
import structlog
from crewai import Agent, Task
from crewai.tools import BaseTool as CrewBaseTool
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


def make_crewai_tool(tool_name: str, tool_description: str, func: Callable) -> CrewBaseTool:
    """Wrap a plain callable into a CrewAI-compatible BaseTool instance."""
    _func = func  # capture in closure

    class _DynamicTool(CrewBaseTool):
        name: str = tool_name
        description: str = tool_description

        def _run(self, *args: Any, **kwargs: Any) -> Any:
            return _func(*args, **kwargs)

    return _DynamicTool()


class BaseComplianceAgent(ABC):
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[CrewBaseTool]] = None,
        verbose: bool = True,
        max_iter: int = 10,
        memory: bool = True,
    ):
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.tools = tools or []
        self.verbose = verbose
        self.max_iter = max_iter
        self.memory = memory
        self.agent = self._create_agent()
        self.logger = logger.bind(agent=name)

    def _create_agent(self) -> Agent:
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            tools=self.tools,
            verbose=self.verbose,
            max_iter=self.max_iter,
            memory=self.memory,
            allow_delegation=False,
        )

    @abstractmethod
    def create_task(self, **kwargs) -> Task:
        pass

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute(self, task: Task) -> Any:
        try:
            self.logger.info(f"Executing task", task_description=task.description[:100])
            result = self.agent.execute_task(task)
            self.logger.info(f"Task completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Task execution failed", error=str(e))
            raise

    def add_tool(self, tool: CrewBaseTool) -> None:
        self.tools.append(tool)
        self.agent.tools.append(tool)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "agent_name": self.name,
            "role": self.role,
            "tools_count": len(self.tools),
            "max_iterations": self.max_iter,
        }