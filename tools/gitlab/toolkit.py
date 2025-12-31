"""GitLab LangChain Toolkit."""

from __future__ import annotations

from typing import Optional

import gitlab
from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import BaseModel, Field

from .tools.projects import (
    GetProjectTool,
    ListProjectsTool,
)
from .tools.issues import (
    AddIssueNoteTool,
    CloseIssueTool,
    CreateIssueTool,
    GetIssueTool,
    ListIssueNotesTool,
    ListIssuesTool,
    UpdateIssueTool,
)
from .tools.merge_requests import (
    AddMergeRequestNoteTool,
    ApproveMergeRequestTool,
    CreateMergeRequestTool,
    GetMergeRequestTool,
    ListMergeRequestNotesTool,
    ListMergeRequestsTool,
    MergeMergeRequestTool,
)
from .tools.repository import (
    ChmodFileTool,
    CompareRefsTool,
    CreateOrUpdateFileTool,
    DeleteFileTool,
    GetFileTool,
    GetRawFileTool,
    ListRepositoryTreeTool,
    MoveFileTool,
)
from .tools.pipelines import (
    CancelJobTool,
    GetJobTraceTool,
    GetPipelineTool,
    ListPipelineJobsTool,
    ListPipelinesTool,
    RetryJobTool,
    RunPipelineTool,
)
from .tools.wiki import (
    CreateWikiPageTool,
    DeleteWikiPageTool,
    GetWikiPageTool,
    ListWikiPagesTool,
    UpdateWikiPageTool,
)
from .tools.helpers import (
    ListLabelsTool,
    ListMilestonesTool,
    ListProjectMembersTool,
    SearchUsersTool,
)


class GitLabToolkit(BaseToolkit):
    """Toolkit for GitLab operations with LangChain.
    
    Provides comprehensive tools for interacting with GitLab projects,
    issues, merge requests, repositories, CI/CD pipelines, and wiki pages.
    """

    gitlab_url: str = Field(
        "https://gitlab.example.com",
        description="Base URL for your GitLab instance",
    )
    token: str = Field("", description="GitLab Personal Access Token (PAT) with api scope")
    verify_ssl: bool = Field(
        True,
        description="Verify TLS certificates (disable only for lab/self-signed setups)",
    )
    compact_results_default: bool = Field(
        True,
        description="Default compact mode for responses (reduced field set but includes core data)",
    )
    allow_repo_writes: bool = Field(
        False,
        description="Enable repository write operations (create/update/delete files)",
    )

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True

    def _initialize_gitlab(self) -> gitlab.Gitlab:
        """Initialize and return GitLab client."""
        return gitlab.Gitlab(
            self.gitlab_url,
            private_token=self.token,
            ssl_verify=self.verify_ssl,
        )

    def get_tools(self) -> list[BaseTool]:
        """Return all tools in the toolkit."""
        gl = self._initialize_gitlab()

        return [
            # Project tools
            ListProjectsTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetProjectTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            # Issue tools
            ListIssuesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetIssueTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            CreateIssueTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            UpdateIssueTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            CloseIssueTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            AddIssueNoteTool(
                gitlab=gl,
            ),
            ListIssueNotesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            # Merge Request tools
            ListMergeRequestsTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetMergeRequestTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            CreateMergeRequestTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            ApproveMergeRequestTool(
                gitlab=gl,
            ),
            MergeMergeRequestTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            AddMergeRequestNoteTool(
                gitlab=gl,
            ),
            ListMergeRequestNotesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            # Repository tools
            ListRepositoryTreeTool(
                gitlab=gl,
            ),
            GetFileTool(
                gitlab=gl,
            ),
            GetRawFileTool(
                gitlab=gl,
            ),
            CompareRefsTool(
                gitlab=gl,
            ),
            CreateOrUpdateFileTool(
                gitlab=gl,
                allow_writes=self.allow_repo_writes,
            ),
            DeleteFileTool(
                gitlab=gl,
                allow_writes=self.allow_repo_writes,
            ),
            MoveFileTool(
                gitlab=gl,
                allow_writes=self.allow_repo_writes,
            ),
            ChmodFileTool(
                gitlab=gl,
                allow_writes=self.allow_repo_writes,
            ),
            # Pipeline tools
            ListPipelinesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetPipelineTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            ListPipelineJobsTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetJobTraceTool(
                gitlab=gl,
            ),
            RunPipelineTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            RetryJobTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            CancelJobTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            # Wiki tools
            ListWikiPagesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            GetWikiPageTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            CreateWikiPageTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            UpdateWikiPageTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            DeleteWikiPageTool(
                gitlab=gl,
            ),
            # Helper/Lookup tools
            SearchUsersTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            ListLabelsTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            ListMilestonesTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
            ListProjectMembersTool(
                gitlab=gl,
                compact_default=self.compact_results_default,
            ),
        ]
