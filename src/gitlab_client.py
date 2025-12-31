"""GitLab API client for interacting with GitLab instances."""

import logging
from typing import Any, Optional
from urllib.parse import quote

import httpx

from .config import settings
from .models import IssueInfo, MergeRequestInfo, PipelineInfo, ProjectInfo

logger = logging.getLogger(__name__)


class GitLabClient:
    """Client for GitLab API operations."""

    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None) -> None:
        """Initialize GitLab client."""
        self.base_url = (base_url or str(settings.gitlab_url)).rstrip("/")
        self.token = token or settings.gitlab_token
        self.api_url = f"{self.base_url}/api/v4"
        
        if not self.token:
            raise ValueError("GitLab token is required")
        
        self.headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
        }

    def _encode_project_path(self, project: str | int) -> str:
        """Encode project path for URL."""
        if isinstance(project, int):
            return str(project)
        return quote(project, safe="")

    async def get_project(self, project: str | int) -> ProjectInfo:
        """Get project information."""
        project_id = self._encode_project_path(project)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            
        return ProjectInfo(
            id=data["id"],
            name=data["name"],
            path_with_namespace=data["path_with_namespace"],
            description=data.get("description"),
            default_branch=data.get("default_branch"),
            visibility=data["visibility"],
            web_url=data["web_url"],
        )

    async def list_projects(
        self,
        membership: bool = True,
        archived: bool = False,
        per_page: int = 20,
    ) -> list[ProjectInfo]:
        """List accessible projects."""
        params: dict[str, Any] = {
            "per_page": per_page,
            "archived": archived,
        }
        if membership:
            params["membership"] = "true"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            ProjectInfo(
                id=p["id"],
                name=p["name"],
                path_with_namespace=p["path_with_namespace"],
                description=p.get("description"),
                default_branch=p.get("default_branch"),
                visibility=p["visibility"],
                web_url=p["web_url"],
            )
            for p in data
        ]

    async def list_issues(
        self,
        project: str | int,
        state: Optional[str] = None,
        labels: Optional[list[str]] = None,
        per_page: int = 20,
    ) -> list[IssueInfo]:
        """List project issues."""
        project_id = self._encode_project_path(project)
        params: dict[str, Any] = {"per_page": per_page}
        
        if state:
            params["state"] = state
        if labels:
            params["labels"] = ",".join(labels)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/issues",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            IssueInfo(
                id=issue["id"],
                iid=issue["iid"],
                title=issue["title"],
                description=issue.get("description"),
                state=issue["state"],
                labels=issue.get("labels", []),
                author=issue["author"],
                created_at=issue["created_at"],
                updated_at=issue["updated_at"],
                web_url=issue["web_url"],
            )
            for issue in data
        ]

    async def get_issue(self, project: str | int, issue_iid: int) -> IssueInfo:
        """Get specific issue."""
        project_id = self._encode_project_path(project)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/issues/{issue_iid}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            issue = response.json()
        
        return IssueInfo(
            id=issue["id"],
            iid=issue["iid"],
            title=issue["title"],
            description=issue.get("description"),
            state=issue["state"],
            labels=issue.get("labels", []),
            author=issue["author"],
            created_at=issue["created_at"],
            updated_at=issue["updated_at"],
            web_url=issue["web_url"],
        )

    async def list_merge_requests(
        self,
        project: str | int,
        state: Optional[str] = None,
        per_page: int = 20,
    ) -> list[MergeRequestInfo]:
        """List project merge requests."""
        project_id = self._encode_project_path(project)
        params: dict[str, Any] = {"per_page": per_page}
        
        if state:
            params["state"] = state
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/merge_requests",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            MergeRequestInfo(
                id=mr["id"],
                iid=mr["iid"],
                title=mr["title"],
                description=mr.get("description"),
                state=mr["state"],
                source_branch=mr["source_branch"],
                target_branch=mr["target_branch"],
                author=mr["author"],
                created_at=mr["created_at"],
                updated_at=mr["updated_at"],
                merged_at=mr.get("merged_at"),
                web_url=mr["web_url"],
            )
            for mr in data
        ]

    async def get_merge_request(
        self,
        project: str | int,
        mr_iid: int,
    ) -> MergeRequestInfo:
        """Get specific merge request."""
        project_id = self._encode_project_path(project)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/merge_requests/{mr_iid}",
                headers=self.headers,
                timeout=30.0,
            )
            response.raise_for_status()
            mr = response.json()
        
        return MergeRequestInfo(
            id=mr["id"],
            iid=mr["iid"],
            title=mr["title"],
            description=mr.get("description"),
            state=mr["state"],
            source_branch=mr["source_branch"],
            target_branch=mr["target_branch"],
            author=mr["author"],
            created_at=mr["created_at"],
            updated_at=mr["updated_at"],
            merged_at=mr.get("merged_at"),
            web_url=mr["web_url"],
        )

    async def list_pipelines(
        self,
        project: str | int,
        ref: Optional[str] = None,
        per_page: int = 20,
    ) -> list[PipelineInfo]:
        """List project pipelines."""
        project_id = self._encode_project_path(project)
        params: dict[str, Any] = {"per_page": per_page}
        
        if ref:
            params["ref"] = ref
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/pipelines",
                headers=self.headers,
                params=params,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        
        return [
            PipelineInfo(
                id=p["id"],
                iid=p.get("iid"),
                status=p["status"],
                ref=p["ref"],
                sha=p["sha"],
                created_at=p["created_at"],
                updated_at=p["updated_at"],
                web_url=p["web_url"],
            )
            for p in data
        ]

    async def get_file_content(
        self,
        project: str | int,
        file_path: str,
        ref: str = "main",
    ) -> str:
        """Get file content from repository."""
        project_id = self._encode_project_path(project)
        file_path_encoded = quote(file_path, safe="")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/projects/{project_id}/repository/files/{file_path_encoded}/raw",
                headers=self.headers,
                params={"ref": ref},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.text

    async def create_issue(
        self,
        project: str | int,
        title: str,
        description: Optional[str] = None,
        labels: Optional[list[str]] = None,
    ) -> IssueInfo:
        """Create a new issue."""
        project_id = self._encode_project_path(project)
        data: dict[str, Any] = {"title": title}
        
        if description:
            data["description"] = description
        if labels:
            data["labels"] = ",".join(labels)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/projects/{project_id}/issues",
                headers=self.headers,
                json=data,
                timeout=30.0,
            )
            response.raise_for_status()
            issue = response.json()
        
        return IssueInfo(
            id=issue["id"],
            iid=issue["iid"],
            title=issue["title"],
            description=issue.get("description"),
            state=issue["state"],
            labels=issue.get("labels", []),
            author=issue["author"],
            created_at=issue["created_at"],
            updated_at=issue["updated_at"],
            web_url=issue["web_url"],
        )
