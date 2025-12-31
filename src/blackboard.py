"""Flock blackboard implementation for agent coordination."""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from flock import Blackboard, BlackboardConfig

from .config import settings
from .models import (
    AgentRole,
    ApprovalRequest,
    ApprovalStatus,
    BlackboardMessage,
    OperationType,
    Task,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class GitLabBlackboard:
    """Blackboard for coordinating GitLab operations across agents."""

    def __init__(self) -> None:
        """Initialize the blackboard."""
        config = BlackboardConfig(
            name="gitlab-orchestrator",
            description="Coordinates GitLab operations using specialist agents",
        )
        self.board = Blackboard(config)
        self.tasks: dict[str, Task] = {}
        self.messages: list[BlackboardMessage] = []
        self.approval_requests: dict[str, ApprovalRequest] = {}
        self._lock = asyncio.Lock()

    async def create_task(
        self,
        operation_type: OperationType,
        agent_role: AgentRole,
        input_data: dict[str, Any],
        requires_approval: bool = False,
    ) -> Task:
        """Create a new task on the blackboard."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            operation_type=operation_type,
            agent_role=agent_role,
            status=TaskStatus.PENDING,
            input_data=input_data,
            created_at=datetime.utcnow(),
            requires_approval=requires_approval,
        )
        
        async with self._lock:
            self.tasks[task_id] = task
            await self.post_message(
                agent_role=AgentRole.PROJECT_PLANNER,
                content={
                    "event": "task_created",
                    "task_id": task_id,
                    "operation": operation_type.value,
                },
                task_id=task_id,
            )
        
        logger.info("Created task %s for agent %s", task_id, agent_role.value)
        return task

    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        output_data: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Update task status and data."""
        async with self._lock:
            if task_id not in self.tasks:
                raise ValueError(f"Task {task_id} not found")
            
            task = self.tasks[task_id]
            
            if status:
                task.status = status
                
            if output_data is not None:
                task.output_data = output_data
                
            if error:
                task.error = error
                
            if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                task.completed_at = datetime.utcnow()
            
            await self.post_message(
                agent_role=task.agent_role,
                content={
                    "event": "task_updated",
                    "task_id": task_id,
                    "status": status.value if status else task.status.value,
                },
                task_id=task_id,
            )
        
        logger.info("Updated task %s: status=%s", task_id, status)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID."""
        return self.tasks.get(task_id)

    async def post_message(
        self,
        agent_role: AgentRole,
        content: dict[str, Any],
        task_id: Optional[str] = None,
    ) -> BlackboardMessage:
        """Post a message to the blackboard."""
        message = BlackboardMessage(
            id=str(uuid.uuid4()),
            agent_role=agent_role,
            timestamp=datetime.utcnow(),
            content=content,
            task_id=task_id,
        )
        
        async with self._lock:
            self.messages.append(message)
            # Keep only last 1000 messages to prevent memory bloat
            if len(self.messages) > 1000:
                self.messages = self.messages[-1000:]
        
        return message

    async def get_messages(
        self,
        task_id: Optional[str] = None,
        agent_role: Optional[AgentRole] = None,
        since: Optional[datetime] = None,
    ) -> list[BlackboardMessage]:
        """Retrieve messages from the blackboard with filters."""
        messages = self.messages.copy()
        
        if task_id:
            messages = [m for m in messages if m.task_id == task_id]
        
        if agent_role:
            messages = [m for m in messages if m.agent_role == agent_role]
        
        if since:
            messages = [m for m in messages if m.timestamp >= since]
        
        return messages

    async def request_approval(
        self,
        task_id: str,
        operation_type: OperationType,
        description: str,
        details: dict[str, Any],
    ) -> ApprovalRequest:
        """Create an approval request."""
        approval_id = str(uuid.uuid4())
        approval = ApprovalRequest(
            id=approval_id,
            task_id=task_id,
            operation_type=operation_type,
            description=description,
            details=details,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(seconds=settings.approval_timeout),
            status=ApprovalStatus.PENDING,
        )
        
        async with self._lock:
            self.approval_requests[approval_id] = approval
            await self.update_task(task_id, status=TaskStatus.REQUIRES_APPROVAL)
            await self.post_message(
                agent_role=AgentRole.HUMAN_APPROVER,
                content={
                    "event": "approval_requested",
                    "approval_id": approval_id,
                    "description": description,
                },
                task_id=task_id,
            )
        
        logger.info("Created approval request %s for task %s", approval_id, task_id)
        return approval

    async def resolve_approval(
        self,
        approval_id: str,
        approved: bool,
        comment: Optional[str] = None,
    ) -> None:
        """Resolve an approval request."""
        async with self._lock:
            if approval_id not in self.approval_requests:
                raise ValueError(f"Approval request {approval_id} not found")
            
            approval = self.approval_requests[approval_id]
            
            if approval.status != ApprovalStatus.PENDING:
                raise ValueError(f"Approval {approval_id} already resolved")
            
            if datetime.utcnow() > approval.expires_at:
                approval.status = ApprovalStatus.TIMEOUT
                await self.update_task(approval.task_id, status=TaskStatus.FAILED, error="Approval timeout")
                logger.warning("Approval %s timed out", approval_id)
                return
            
            approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
            
            task = self.tasks.get(approval.task_id)
            if task:
                if approved:
                    task.status = TaskStatus.PENDING
                    task.approval_status = ApprovalStatus.APPROVED
                else:
                    task.status = TaskStatus.FAILED
                    task.approval_status = ApprovalStatus.REJECTED
                    task.error = f"Approval rejected: {comment}" if comment else "Approval rejected"
            
            await self.post_message(
                agent_role=AgentRole.HUMAN_APPROVER,
                content={
                    "event": "approval_resolved",
                    "approval_id": approval_id,
                    "approved": approved,
                    "comment": comment,
                },
                task_id=approval.task_id,
            )
        
        logger.info("Resolved approval %s: approved=%s", approval_id, approved)

    async def get_pending_approvals(self) -> list[ApprovalRequest]:
        """Get all pending approval requests."""
        now = datetime.utcnow()
        pending = []
        
        async with self._lock:
            for approval in self.approval_requests.values():
                if approval.status == ApprovalStatus.PENDING:
                    if now > approval.expires_at:
                        approval.status = ApprovalStatus.TIMEOUT
                        await self.update_task(
                            approval.task_id,
                            status=TaskStatus.FAILED,
                            error="Approval timeout",
                        )
                    else:
                        pending.append(approval)
        
        return pending

    async def cleanup_old_data(self, days: int = 7) -> None:
        """Clean up old completed tasks and messages."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        async with self._lock:
            # Remove old completed/failed tasks
            tasks_to_remove = [
                task_id
                for task_id, task in self.tasks.items()
                if task.completed_at and task.completed_at < cutoff
            ]
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
            
            # Remove old messages
            self.messages = [m for m in self.messages if m.timestamp >= cutoff]
            
            # Remove old resolved approvals
            approvals_to_remove = [
                approval_id
                for approval_id, approval in self.approval_requests.items()
                if approval.status != ApprovalStatus.PENDING
                and approval.created_at < cutoff
            ]
            for approval_id in approvals_to_remove:
                del self.approval_requests[approval_id]
        
        logger.info(
            "Cleaned up %d old tasks, %d approvals",
            len(tasks_to_remove),
            len(approvals_to_remove),
        )


# Global blackboard instance
blackboard = GitLabBlackboard()
