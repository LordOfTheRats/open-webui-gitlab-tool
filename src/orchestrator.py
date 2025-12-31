"""Orchestrator for managing agents and task execution."""

import asyncio
import logging
from typing import Any, Optional

from .agents import create_agents
from .blackboard import GitLabBlackboard, blackboard
from .config import settings
from .gitlab_client import GitLabClient
from .models import AgentRole, OperationType, Task, TaskStatus
from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class Orchestrator:
    """Orchestrates agent execution and task management."""

    def __init__(
        self,
        gitlab_client: Optional[GitLabClient] = None,
        ollama_client: Optional[OllamaClient] = None,
        blackboard_instance: Optional[GitLabBlackboard] = None,
    ) -> None:
        """Initialize orchestrator."""
        self.gitlab = gitlab_client or GitLabClient()
        self.ollama = ollama_client or OllamaClient()
        self.blackboard = blackboard_instance or blackboard
        self.agents = create_agents(self.blackboard, self.gitlab, self.ollama)
        self._running = False
        self._tasks: dict[str, asyncio.Task[None]] = {}

    async def submit_task(
        self,
        agent_role: AgentRole,
        operation_type: OperationType,
        input_data: dict[str, Any],
        requires_approval: bool = False,
    ) -> Task:
        """Submit a new task for execution."""
        task = await self.blackboard.create_task(
            operation_type=operation_type,
            agent_role=agent_role,
            input_data=input_data,
            requires_approval=requires_approval,
        )
        
        # Execute task asynchronously
        asyncio_task = asyncio.create_task(self._execute_task(task.id))
        self._tasks[task.id] = asyncio_task
        
        return task

    async def _execute_task(self, task_id: str) -> None:
        """Execute a task with the appropriate agent."""
        try:
            task = await self.blackboard.get_task(task_id)
            if not task:
                logger.error("Task %s not found", task_id)
                return
            
            # Check if approval is needed
            if task.requires_approval and not task.approval_status:
                # Request approval will be handled externally
                await self.blackboard.update_task(task_id, status=TaskStatus.REQUIRES_APPROVAL)
                logger.info("Task %s requires approval", task_id)
                return
            
            # Find appropriate agent
            agent = self.agents.get(task.agent_role)
            if not agent:
                raise ValueError(f"No agent found for role {task.agent_role}")
            
            # Execute with timeout
            async with asyncio.timeout(settings.agent_timeout):
                await agent.process_task(task)
                
        except asyncio.TimeoutError:
            logger.error("Task %s timed out", task_id)
            await self.blackboard.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error="Task execution timeout",
            )
        except Exception as e:
            logger.error("Task %s execution failed: %s", task_id, e)
            await self.blackboard.update_task(
                task_id,
                status=TaskStatus.FAILED,
                error=str(e),
            )
        finally:
            self._tasks.pop(task_id, None)

    async def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get current status of a task."""
        return await self.blackboard.get_task(task_id)

    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None,
    ) -> Task:
        """Wait for a task to complete."""
        if timeout is None:
            timeout = float(settings.agent_timeout)
        
        start_time = asyncio.get_event_loop().time()
        
        while True:
            task = await self.blackboard.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                return task
            
            if task.status == TaskStatus.REQUIRES_APPROVAL:
                # Wait for approval
                await asyncio.sleep(1)
                continue
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
            
            await asyncio.sleep(0.5)

    async def approve_task(
        self,
        approval_id: str,
        approved: bool,
        comment: Optional[str] = None,
    ) -> None:
        """Approve or reject a task approval request."""
        await self.blackboard.resolve_approval(approval_id, approved, comment)
        
        # Find the approval to get task_id
        approval = self.blackboard.approval_requests.get(approval_id)
        if approval and approved:
            # Resume task execution
            asyncio_task = asyncio.create_task(self._execute_task(approval.task_id))
            self._tasks[approval.task_id] = asyncio_task

    async def get_pending_approvals(self) -> list[Any]:
        """Get all pending approval requests."""
        return await self.blackboard.get_pending_approvals()

    async def cleanup(self) -> None:
        """Clean up orchestrator resources."""
        # Cancel all running tasks
        for task in self._tasks.values():
            task.cancel()
        
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        
        self._tasks.clear()


# Global orchestrator instance
orchestrator = Orchestrator()
