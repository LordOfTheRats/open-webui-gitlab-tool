"""Artifacts package initialization."""

from gitlab_tool.artifacts.gitlab import (
    CodeReview,
    Issue,
    IssueSummary,
    Job,
    MergeRequest,
    MergeRequestSummary,
    Pipeline,
    PipelineAnalysis,
)
from gitlab_tool.artifacts.requests import (
    ApprovalResponse,
    CreateIssueRequest,
    CreateMergeRequestRequest,
    GetFileRequest,
    ListProjectsRequest,
    ReviewMergeRequestRequest,
    SummarizeIssueRequest,
    SummarizeMergeRequestRequest,
    TriagePipelineRequest,
)

__all__ = [
    # GitLab entities
    "Issue",
    "MergeRequest",
    "Pipeline",
    "Job",
    # Agent outputs
    "IssueSummary",
    "MergeRequestSummary",
    "CodeReview",
    "PipelineAnalysis",
    # Requests
    "SummarizeIssueRequest",
    "SummarizeMergeRequestRequest",
    "ReviewMergeRequestRequest",
    "TriagePipelineRequest",
    "CreateIssueRequest",
    "CreateMergeRequestRequest",
    "GetFileRequest",
    "ListProjectsRequest",
    "ApprovalResponse",
]
