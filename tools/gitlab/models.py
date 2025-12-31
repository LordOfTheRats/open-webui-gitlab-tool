"""Pydantic models for GitLab tool inputs."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProjectRef(BaseModel):
    """Base model with project reference."""

    project: int | str = Field(
        ...,
        description="Project ID (int) or path (str) in format 'group/subgroup/project'",
    )


# ----------------------------
# Project tools
# ----------------------------


class ListProjectsInput(BaseModel):
    """Input for listing projects."""

    search: Optional[str] = Field(
        None, description="Optional substring filter for project name/path"
    )
    membership: bool = Field(True, description="Limit to projects you are a member of")
    owned: bool = Field(False, description="Limit to projects you own")
    starred: bool = Field(False, description="Limit to projects you starred")
    visibility: Optional[Literal["private", "internal", "public"]] = Field(
        None, description="Filter by visibility level"
    )
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetProjectInput(ProjectRef):
    """Input for getting a single project."""

    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


# ----------------------------
# Issue tools
# ----------------------------


class ListIssuesInput(ProjectRef):
    """Input for listing issues."""

    state: Optional[Literal["opened", "closed", "all"]] = Field(
        "opened", description="Filter by state"
    )
    labels: Optional[str] = Field(
        None, description="Comma-separated list of label names"
    )
    assignee_username: Optional[str] = Field(None, description="Filter by assignee username")
    search: Optional[str] = Field(None, description="Search in title and description")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetIssueInput(ProjectRef):
    """Input for getting a single issue."""

    issue_iid: int = Field(..., description="Issue IID (internal ID within project)")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class CreateIssueInput(ProjectRef):
    """Input for creating an issue."""

    title: str = Field(..., description="Issue title")
    description: Optional[str] = Field(None, description="Issue description")
    labels: Optional[str] = Field(
        None, description="Comma-separated list of label names"
    )
    assignee_id: Optional[int] = Field(None, description="ID of assignee user")
    milestone_id: Optional[int] = Field(None, description="ID of milestone")
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class UpdateIssueInput(ProjectRef):
    """Input for updating an issue."""

    issue_iid: int = Field(..., description="Issue IID")
    title: Optional[str] = Field(None, description="New issue title")
    description: Optional[str] = Field(None, description="New issue description")
    assignee_id: Optional[int] = Field(None, description="ID of assignee user")
    labels: Optional[str] = Field(
        None, description="Comma-separated list of label names (replaces existing)"
    )
    add_labels: Optional[str] = Field(
        None, description="Comma-separated list of labels to add"
    )
    remove_labels: Optional[str] = Field(
        None, description="Comma-separated list of labels to remove"
    )
    due_date: Optional[str] = Field(None, description="Due date (YYYY-MM-DD)")
    milestone_id: Optional[int] = Field(None, description="ID of milestone")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class CloseIssueInput(ProjectRef):
    """Input for closing an issue."""

    issue_iid: int = Field(..., description="Issue IID")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class AddIssueNoteInput(ProjectRef):
    """Input for adding a comment to an issue."""

    issue_iid: int = Field(..., description="Issue IID")
    body: str = Field(..., description="Comment text")


class ListIssueNotesInput(ProjectRef):
    """Input for listing issue comments."""

    issue_iid: int = Field(..., description="Issue IID")
    sort: Optional[Literal["asc", "desc"]] = Field(
        "asc", description="Sort order by creation date"
    )
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


# ----------------------------
# Merge Request tools
# ----------------------------


class ListMergeRequestsInput(ProjectRef):
    """Input for listing merge requests."""

    state: Optional[
        Literal["opened", "closed", "locked", "merged", "all"]
    ] = Field("opened", description="Filter by state")
    source_branch: Optional[str] = Field(None, description="Filter by source branch")
    target_branch: Optional[str] = Field(None, description="Filter by target branch")
    search: Optional[str] = Field(None, description="Search in title and description")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetMergeRequestInput(ProjectRef):
    """Input for getting a merge request."""

    mr_iid: int = Field(..., description="Merge Request IID")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class CreateMergeRequestInput(ProjectRef):
    """Input for creating a merge request."""

    source_branch: str = Field(..., description="Source branch name")
    target_branch: str = Field(..., description="Target branch name")
    title: str = Field(..., description="MR title")
    description: Optional[str] = Field(None, description="MR description")
    remove_source_branch: bool = Field(
        False, description="Delete source branch after merge"
    )
    squash: Optional[bool] = Field(None, description="Squash commits on merge")
    draft: bool = Field(False, description="Create as draft MR")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class ApproveMergeRequestInput(ProjectRef):
    """Input for approving a merge request."""

    mr_iid: int = Field(..., description="Merge Request IID")


class MergeMergeRequestInput(ProjectRef):
    """Input for merging a merge request."""

    mr_iid: int = Field(..., description="Merge Request IID")
    merge_commit_message: Optional[str] = Field(None, description="Custom commit message")
    squash_commit_message: Optional[str] = Field(
        None, description="Custom squash commit message"
    )
    should_remove_source_branch: Optional[bool] = Field(
        None, description="Delete source branch after merge"
    )
    squash: Optional[bool] = Field(None, description="Squash commits on merge")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class AddMergeRequestNoteInput(ProjectRef):
    """Input for adding a comment to a merge request."""

    mr_iid: int = Field(..., description="Merge Request IID")
    body: str = Field(..., description="Comment text")


class ListMergeRequestNotesInput(ProjectRef):
    """Input for listing merge request comments."""

    mr_iid: int = Field(..., description="Merge Request IID")
    sort: Optional[Literal["asc", "desc"]] = Field(
        "asc", description="Sort order by creation date"
    )
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


# ----------------------------
# Repository tools
# ----------------------------


class ListRepositoryTreeInput(ProjectRef):
    """Input for listing repository tree."""

    path: str = Field("", description="Path within repository")
    ref: Optional[str] = Field(None, description="Branch/tag/commit reference")
    recursive: bool = Field(False, description="Recursively fetch all files")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")


class GetFileInput(ProjectRef):
    """Input for getting a file."""

    file_path: str = Field(..., description="Path to file")
    ref: str = Field("HEAD", description="Branch/tag/commit reference")


class GetRawFileInput(ProjectRef):
    """Input for getting raw file content."""

    file_path: str = Field(..., description="Path to file")
    ref: str = Field("HEAD", description="Branch/tag/commit reference")


class CompareInput(ProjectRef):
    """Input for comparing refs."""

    from_ref: str = Field(..., description="From commit/branch/tag")
    to_ref: str = Field(..., description="To commit/branch/tag")
    straight: bool = Field(False, description="Use straight diff (no merge base)")


class CreateOrUpdateFileInput(ProjectRef):
    """Input for creating or updating a file."""

    branch: str = Field(..., description="Branch name")
    file_path: str = Field(..., description="Path to file")
    content: str = Field(..., description="File content")
    commit_message: str = Field(..., description="Commit message")
    encoding: Literal["text", "base64"] = Field("text", description="Content encoding")
    start_branch: Optional[str] = Field(
        None, description="Branch to start from (for new branches)"
    )
    execute_filemode: Optional[bool] = Field(None, description="Make file executable")


class DeleteFileInput(ProjectRef):
    """Input for deleting a file."""

    branch: str = Field(..., description="Branch name")
    file_path: str = Field(..., description="Path to file")
    commit_message: str = Field(..., description="Commit message")
    start_branch: Optional[str] = Field(
        None, description="Branch to start from (for new branches)"
    )


class MoveFileInput(ProjectRef):
    """Input for moving/renaming a file."""

    branch: str = Field(..., description="Branch name")
    file_path: str = Field(..., description="Current file path")
    previous_path: str = Field(..., description="Previous file path")
    commit_message: str = Field(..., description="Commit message")
    start_branch: Optional[str] = Field(
        None, description="Branch to start from (for new branches)"
    )


class ChmodFileInput(ProjectRef):
    """Input for changing file permissions."""

    branch: str = Field(..., description="Branch name")
    file_path: str = Field(..., description="Path to file")
    execute_filemode: bool = Field(..., description="Make file executable")
    commit_message: str = Field(..., description="Commit message")
    start_branch: Optional[str] = Field(
        None, description="Branch to start from (for new branches)"
    )


# ----------------------------
# Pipeline tools
# ----------------------------


class ListPipelinesInput(ProjectRef):
    """Input for listing pipelines."""

    ref: Optional[str] = Field(None, description="Filter by ref/branch")
    status: Optional[
        Literal[
            "created",
            "waiting_for_resource",
            "preparing",
            "pending",
            "running",
            "success",
            "failed",
            "canceled",
            "skipped",
            "manual",
            "scheduled",
        ]
    ] = Field(None, description="Filter by pipeline status")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetPipelineInput(ProjectRef):
    """Input for getting a pipeline."""

    pipeline_id: int = Field(..., description="Pipeline ID")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class ListPipelineJobsInput(ProjectRef):
    """Input for listing jobs in a pipeline."""

    pipeline_id: int = Field(..., description="Pipeline ID")
    scope: Optional[
        Literal[
            "created",
            "pending",
            "running",
            "failed",
            "success",
            "canceled",
            "skipped",
            "manual",
        ]
    ] = Field(None, description="Filter by job status")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetJobTraceInput(ProjectRef):
    """Input for getting job trace/log."""

    job_id: int = Field(..., description="Job ID")


class RunPipelineInput(ProjectRef):
    """Input for triggering a pipeline."""

    ref: str = Field(..., description="Ref/branch/tag to trigger pipeline on")
    variables: Optional[dict[str, str]] = Field(
        None, description="Pipeline variables as key-value pairs"
    )
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class RetryJobInput(ProjectRef):
    """Input for retrying a job."""

    job_id: int = Field(..., description="Job ID")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class CancelJobInput(ProjectRef):
    """Input for canceling a job."""

    job_id: int = Field(..., description="Job ID")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


# ----------------------------
# Wiki tools
# ----------------------------


class ListWikiPagesInput(ProjectRef):
    """Input for listing wiki pages."""

    with_content: bool = Field(False, description="Include page content")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class GetWikiPageInput(ProjectRef):
    """Input for getting a wiki page."""

    slug: str = Field(..., description="Wiki page slug/title")
    version: Optional[str] = Field(None, description="Commit/version to retrieve")
    render_html: bool = Field(False, description="Return rendered HTML")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class CreateWikiPageInput(ProjectRef):
    """Input for creating a wiki page."""

    title: str = Field(..., description="Wiki page title")
    content: str = Field(..., description="Wiki page content")
    format: Literal["markdown", "rdoc", "asciidoc", "org"] = Field(
        "markdown", description="Content format"
    )
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class UpdateWikiPageInput(ProjectRef):
    """Input for updating a wiki page."""

    slug: str = Field(..., description="Wiki page slug/title")
    title: Optional[str] = Field(None, description="New page title")
    content: Optional[str] = Field(None, description="New page content")
    format: Optional[Literal["markdown", "rdoc", "asciidoc", "org"]] = Field(
        None, description="Content format"
    )
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class DeleteWikiPageInput(ProjectRef):
    """Input for deleting a wiki page."""

    slug: str = Field(..., description="Wiki page slug/title")


# ----------------------------
# Helper/Lookup tools
# ----------------------------


class SearchUsersInput(BaseModel):
    """Input for searching users."""

    search: str = Field(..., description="Search query (username or name)")
    active: Optional[bool] = Field(None, description="Filter by active status")
    external: Optional[bool] = Field(None, description="Filter by external status")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class ListLabelsInput(ProjectRef):
    """Input for listing project labels."""

    search: Optional[str] = Field(None, description="Search filter for label name")
    include_ancestor_groups: bool = Field(
        True, description="Include labels from ancestor groups"
    )
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class ListMilestonesInput(ProjectRef):
    """Input for listing project milestones."""

    state: Optional[Literal["active", "closed", "all"]] = Field(
        "active", description="Filter by state"
    )
    search: Optional[str] = Field(None, description="Search filter for milestone title")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )


class ListProjectMembersInput(ProjectRef):
    """Input for listing project members."""

    query: Optional[str] = Field(None, description="Search filter for username/name")
    include_inherited: bool = Field(True, description="Include inherited members")
    offset: int = Field(0, description="Page offset (0-based)")
    page_count: int = Field(1, description="Number of pages to fetch")
    compact: Optional[bool] = Field(
        None, description="Return compact results (uses toolkit default if not specified)"
    )
