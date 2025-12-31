"""Base agent class and common agent utilities."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .blackboard import GitLabBlackboard
from .gitlab_client import GitLabClient
from .models import AgentRole, Task, TaskStatus
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all specialist agents."""

    def __init__(
        self,
        role: AgentRole,
        blackboard: GitLabBlackboard,
        gitlab_client: GitLabClient,
        ollama_client: OllamaClient,
    ) -> None:
        """Initialize the agent."""
        self.role = role
        self.blackboard = blackboard
        self.gitlab = gitlab_client
        self.llm = ollama_client

    @abstractmethod
    async def can_handle(self, task: Task) -> bool:
        """Check if this agent can handle the given task."""
        pass

    @abstractmethod
    async def execute(self, task: Task) -> dict[str, Any]:
        """Execute the task and return results."""
        pass

    async def process_task(self, task: Task) -> None:
        """Process a task from start to finish."""
        try:
            logger.info("Agent %s processing task %s", self.role.value, task.id)
            
            await self.blackboard.update_task(task.id, status=TaskStatus.IN_PROGRESS)
            
            if not await self.can_handle(task):
                raise ValueError(f"Agent {self.role.value} cannot handle this task")
            
            result = await self.execute(task)
            
            await self.blackboard.update_task(
                task.id,
                status=TaskStatus.COMPLETED,
                output_data=result,
            )
            
            logger.info("Agent %s completed task %s", self.role.value, task.id)
            
        except Exception as e:
            logger.error("Agent %s failed task %s: %s", self.role.value, task.id, e)
            await self.blackboard.update_task(
                task.id,
                status=TaskStatus.FAILED,
                error=str(e),
            )
            raise

    async def generate_response(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate LLM response for agent reasoning."""
        if system is None:
            system = f"You are a {self.role.value} agent specializing in GitLab operations."
        
        return await self.llm.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        """Chat with LLM for complex reasoning."""
        return await self.llm.chat(
            messages=messages,
            temperature=temperature,
        )
