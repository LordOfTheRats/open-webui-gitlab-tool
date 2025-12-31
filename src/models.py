"""Common types and models used across the application."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class OperationType(str, Enum):
    """Types of operations that can be performed."""

    READ = "read"
    WRITE = "write"
    PIPELINE_ACTION = "pipeline_action"
    ANALYSIS = "analysis"


class ApprovalStatus(str, Enum):
    """Status of human approval requests."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class AgentRole(str, Enum):
    """Roles for specialist agents."""

    PROJECT_PLANNER = "project_planner"
    ISSUE_SUMMARIZER = "issue_summarizer"
    MR_ANALYZER = "mr_analyzer"
    CODE_REVIEWER = "code_reviewer"
    PIPELINE_REVIEWER = "pipeline_reviewer"
    REPO_BROWSER = "repo_browser"
    WIKI_MANAGER = "wiki_manager"
    HUMAN_APPROVER = "human_approver"


class TaskStatus(str, Enum):
    """Status of blackboard tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"


class BlackboardMessage(BaseModel):
    """Message posted to the blackboard."""

    id: str
    agent_role: AgentRole
    timestamp: datetime
    content: dict[str, Any]
    task_id: Optional[str] = None


class Task(BaseModel):
    """Task to be executed by agents."""

    id: str
    operation_type: OperationType
    agent_role: AgentRole
    status: TaskStatus = TaskStatus.PENDING
    input_data: dict[str, Any]
    output_data: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    requires_approval: bool = False
    approval_status: Optional[ApprovalStatus] = None


class ApprovalRequest(BaseModel):
    """Request for human approval."""

    id: str
    task_id: str
    operation_type: OperationType
    description: str
    details: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING


class GitLabResource(BaseModel):
    """Base model for GitLab resources."""

    id: int
    web_url: str


class ProjectInfo(GitLabResource):
    """GitLab project information."""

    name: str
    path_with_namespace: str
    description: Optional[str] = None
    default_branch: Optional[str] = None
    visibility: str


class IssueInfo(GitLabResource):
    """GitLab issue information."""

    iid: int
    title: str
    description: Optional[str] = None
    state: str
    labels: list[str] = Field(default_factory=list)
    author: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class MergeRequestInfo(GitLabResource):
    """GitLab merge request information."""

    iid: int
    title: str
    description: Optional[str] = None
    state: str
    source_branch: str
    target_branch: str
    author: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime] = None


class PipelineInfo(GitLabResource):
    """GitLab pipeline information."""

    iid: Optional[int] = None
    status: str
    ref: str
    sha: str
    created_at: datetime
    updated_at: datetime
