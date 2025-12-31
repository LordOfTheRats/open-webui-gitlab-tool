"""Request models for API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class SummarizeIssueRequest(BaseModel):
    """Request to summarize an issue."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    issue_iid: int = Field(..., description="Issue IID")
    include_comments: bool = Field(default=False, description="Include comments in summary")


class SummarizeMergeRequestRequest(BaseModel):
    """Request to summarize a merge request."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    mr_iid: int = Field(..., description="Merge request IID")
    include_diff: bool = Field(default=True, description="Include diff analysis")


class ReviewMergeRequestRequest(BaseModel):
    """Request to review a merge request."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    mr_iid: int = Field(..., description="Merge request IID")
    review_depth: str = Field(
        default="standard",
        description="Review depth: 'quick', 'standard', or 'thorough'",
    )


class TriagePipelineRequest(BaseModel):
    """Request to triage a failed pipeline."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    pipeline_id: int = Field(..., description="Pipeline ID")
    include_logs: bool = Field(default=True, description="Include job logs in analysis")


class CreateIssueRequest(BaseModel):
    """Request to create an issue."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    title: str = Field(..., description="Issue title")
    description: Optional[str] = Field(None, description="Issue description")
    labels: Optional[list[str]] = Field(None, description="Issue labels")
    assignee_id: Optional[int] = Field(None, description="Assignee user ID")


class CreateMergeRequestRequest(BaseModel):
    """Request to create a merge request."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    source_branch: str = Field(..., description="Source branch name")
    target_branch: str = Field(..., description="Target branch name")
    title: str = Field(..., description="Merge request title")
    description: Optional[str] = Field(None, description="Merge request description")
    remove_source_branch: bool = Field(
        default=False, description="Remove source branch after merge"
    )


class GetFileRequest(BaseModel):
    """Request to get a file from repository."""

    project: str = Field(..., description="Project path (e.g., 'group/project')")
    file_path: str = Field(..., description="File path in repository")
    ref: str = Field(default="HEAD", description="Branch, tag, or commit SHA")


class ListProjectsRequest(BaseModel):
    """Request to list projects."""

    search: Optional[str] = Field(None, description="Search query")
    membership: bool = Field(default=True, description="Only projects user is member of")
    page: int = Field(default=1, description="Page number")
    per_page: int = Field(default=20, description="Results per page")


class ApprovalResponse(BaseModel):
    """Response for approval request."""

    request_id: str
    approved: bool
    message: Optional[str] = None
    timestamp: str
