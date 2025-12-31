"""Tests for blackboard."""

import pytest
from datetime import datetime

from src.blackboard import GitLabBlackboard
from src.models import AgentRole, ApprovalStatus, OperationType, TaskStatus


@pytest.fixture
def blackboard() -> GitLabBlackboard:
    """Create blackboard for testing."""
    return GitLabBlackboard()


@pytest.mark.asyncio
async def test_create_task(blackboard: GitLabBlackboard) -> None:
    """Test task creation."""
    task = await blackboard.create_task(
        operation_type=OperationType.ANALYSIS,
        agent_role=AgentRole.ISSUE_SUMMARIZER,
        input_data={"project": "test", "issue_iid": 1},
    )
    
    assert task.status == TaskStatus.PENDING
    assert task.agent_role == AgentRole.ISSUE_SUMMARIZER
    assert task.input_data["project"] == "test"


@pytest.mark.asyncio
async def test_update_task(blackboard: GitLabBlackboard) -> None:
    """Test task update."""
    task = await blackboard.create_task(
        operation_type=OperationType.ANALYSIS,
        agent_role=AgentRole.ISSUE_SUMMARIZER,
        input_data={"project": "test"},
    )
    
    await blackboard.update_task(
        task.id,
        status=TaskStatus.COMPLETED,
        output_data={"result": "success"},
    )
    
    updated_task = await blackboard.get_task(task.id)
    assert updated_task is not None
    assert updated_task.status == TaskStatus.COMPLETED
    assert updated_task.output_data == {"result": "success"}


@pytest.mark.asyncio
async def test_approval_request(blackboard: GitLabBlackboard) -> None:
    """Test approval request creation."""
    task = await blackboard.create_task(
        operation_type=OperationType.WRITE,
        agent_role=AgentRole.ISSUE_SUMMARIZER,
        input_data={"project": "test"},
        requires_approval=True,
    )
    
    approval = await blackboard.request_approval(
        task_id=task.id,
        operation_type=OperationType.WRITE,
        description="Test approval",
        details={"action": "create"},
    )
    
    assert approval.status == ApprovalStatus.PENDING
    assert approval.task_id == task.id
    
    # Approve
    await blackboard.resolve_approval(approval.id, approved=True)
    
    resolved_approval = blackboard.approval_requests.get(approval.id)
    assert resolved_approval is not None
    assert resolved_approval.status == ApprovalStatus.APPROVED
