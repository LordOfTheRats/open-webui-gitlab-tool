"""GitLab API client."""

import asyncio
import random
from typing import Any, Literal, Optional, Union
from urllib.parse import quote_plus

import httpx

from gitlab_tool.config import Settings

Json = dict[str, Any]
ProjectRef = Union[int, str]


class GitLabClient:
    """Async GitLab API client with retry logic."""

    def __init__(self, settings: Settings):
        """Initialize GitLab client."""
        self.settings = settings
        self.base_url = settings.gitlab_url.rstrip("/") + "/api/v4"

    def _encode_path(self, value: str) -> str:
        """Encode a path-like string so slashes become %2F."""
        return quote_plus(value, safe="").replace("+", "%20")

    def _project_id_or_path(self, project: ProjectRef) -> str:
        """Convert project reference to API path segment."""
        if isinstance(project, int):
            return str(project)
        return self._encode_path(project)

    def _headers(self) -> dict[str, str]:
        """Build request headers including authentication token."""
        if not self.settings.gitlab_token:
            raise ValueError("GitLab token is not set")

        return {
            "PRIVATE-TOKEN": self.settings.gitlab_token,
            "Content-Type": "application/json",
        }

    def _compute_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        if retry_after is not None and retry_after > 0:
            base = float(retry_after)
        else:
            base = 0.8 * (2 ** (attempt - 1))

        base = min(base, 10.0)

        jitter = 0.2
        if jitter > 0:
            delta = base * jitter
            base = base + random.uniform(-delta, delta)

        return max(0.0, base)

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        accept: Optional[str] = None,
        want_text: bool = False,
    ) -> Any:
        """Execute HTTP request with retry logic."""
        url = self.base_url + path
        headers = self._headers()
        if accept:
            headers = dict(headers)
            headers["Accept"] = accept

        max_retries = 3

        async with httpx.AsyncClient(
            verify=self.settings.gitlab_verify_ssl,
            timeout=self.settings.gitlab_timeout,
            headers=headers,
        ) as client:
            for attempt in range(0, max_retries + 1):
                try:
                    r = await client.request(method, url, params=params, json=json)

                    if r.status_code in (429, 502, 503, 504) and attempt < max_retries:
                        retry_after_hdr = r.headers.get("Retry-After")
                        retry_after: Optional[float] = None
                        if retry_after_hdr:
                            try:
                                retry_after = float(retry_after_hdr)
                            except Exception:
                                retry_after = None
                        delay = self._compute_delay(attempt=attempt + 1, retry_after=retry_after)
                        await asyncio.sleep(delay)
                        continue

                    if r.status_code >= 400:
                        try:
                            detail = r.json()
                        except Exception:
                            detail = r.text
                        raise RuntimeError(
                            f"GitLab API error {r.status_code} for {method} {path}: {detail}"
                        )

                    if r.status_code == 204:
                        return {"ok": True}

                    if want_text:
                        return r.text

                    if not r.text:
                        return {"ok": True}

                    return r.json()

                except (
                    httpx.ConnectTimeout,
                    httpx.ReadTimeout,
                    httpx.PoolTimeout,
                    httpx.ConnectError,
                ) as e:
                    if attempt < max_retries:
                        delay = self._compute_delay(attempt=attempt + 1, retry_after=None)
                        await asyncio.sleep(delay)
                        continue
                    raise e

    async def _paginate(
        self,
        path: str,
        params: Optional[dict[str, Any]] = None,
        offset: int = 0,
        page_count: int = 1,
    ) -> list[Any]:
        """Fetch paginated results."""
        params = dict(params or {})
        params.setdefault("per_page", 20)

        start_page = offset + 1
        end_page = start_page + page_count - 1

        out: list[Any] = []
        for page in range(start_page, end_page + 1):
            params["page"] = page
            chunk = await self._request("GET", path, params=params)

            if not isinstance(chunk, list):
                return [chunk]

            out.extend(chunk)

            if len(chunk) < int(params["per_page"]):
                break

        return out

    # Project operations
    async def list_projects(
        self,
        search: Optional[str] = None,
        membership: bool = True,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Json]:
        """List projects."""
        params: dict[str, Any] = {
            "membership": membership,
            "simple": True,
            "order_by": "last_activity_at",
            "sort": "desc",
            "page": page,
            "per_page": per_page,
        }
        if search:
            params["search"] = search

        return await self._request("GET", "/projects", params=params)

    async def get_project(self, project: ProjectRef) -> Json:
        """Get a single project."""
        pid = self._project_id_or_path(project)
        return await self._request("GET", f"/projects/{pid}")

    # Issue operations
    async def list_issues(
        self,
        project: ProjectRef,
        state: Optional[Literal["opened", "closed", "all"]] = "opened",
        labels: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Json]:
        """List issues."""
        pid = self._project_id_or_path(project)
        params: dict[str, Any] = {"state": state, "page": page, "per_page": per_page}
        if labels:
            params["labels"] = labels

        return await self._request("GET", f"/projects/{pid}/issues", params=params)

    async def get_issue(self, project: ProjectRef, issue_iid: int) -> Json:
        """Get a single issue by IID."""
        pid = self._project_id_or_path(project)
        return await self._request("GET", f"/projects/{pid}/issues/{issue_iid}")

    async def create_issue(
        self,
        project: ProjectRef,
        title: str,
        description: Optional[str] = None,
        labels: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> Json:
        """Create an issue."""
        pid = self._project_id_or_path(project)
        payload: dict[str, Any] = {"title": title}
        if description is not None:
            payload["description"] = description
        if labels:
            payload["labels"] = labels
        if assignee_id is not None:
            payload["assignee_ids"] = [assignee_id]

        return await self._request("POST", f"/projects/{pid}/issues", json=payload)

    async def list_issue_notes(
        self, project: ProjectRef, issue_iid: int, page: int = 1, per_page: int = 20
    ) -> list[Json]:
        """List issue notes/comments."""
        pid = self._project_id_or_path(project)
        params = {"sort": "asc", "page": page, "per_page": per_page}
        return await self._request(
            "GET", f"/projects/{pid}/issues/{issue_iid}/notes", params=params
        )

    # Merge request operations
    async def list_merge_requests(
        self,
        project: ProjectRef,
        state: Optional[Literal["opened", "closed", "merged", "all"]] = "opened",
        page: int = 1,
        per_page: int = 20,
    ) -> list[Json]:
        """List merge requests."""
        pid = self._project_id_or_path(project)
        params: dict[str, Any] = {"state": state, "page": page, "per_page": per_page}
        return await self._request("GET", f"/projects/{pid}/merge_requests", params=params)

    async def get_merge_request(self, project: ProjectRef, mr_iid: int) -> Json:
        """Get a single merge request by IID."""
        pid = self._project_id_or_path(project)
        return await self._request("GET", f"/projects/{pid}/merge_requests/{mr_iid}")

    async def create_merge_request(
        self,
        project: ProjectRef,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        remove_source_branch: bool = False,
    ) -> Json:
        """Create a merge request."""
        pid = self._project_id_or_path(project)
        payload: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "remove_source_branch": remove_source_branch,
        }
        if description is not None:
            payload["description"] = description

        return await self._request("POST", f"/projects/{pid}/merge_requests", json=payload)

    async def get_merge_request_changes(self, project: ProjectRef, mr_iid: int) -> Json:
        """Get merge request changes/diff."""
        pid = self._project_id_or_path(project)
        return await self._request("GET", f"/projects/{pid}/merge_requests/{mr_iid}/changes")

    async def list_mr_notes(
        self, project: ProjectRef, mr_iid: int, page: int = 1, per_page: int = 20
    ) -> list[Json]:
        """List MR notes/comments."""
        pid = self._project_id_or_path(project)
        params = {"sort": "asc", "page": page, "per_page": per_page}
        return await self._request(
            "GET", f"/projects/{pid}/merge_requests/{mr_iid}/notes", params=params
        )

    # Pipeline operations
    async def list_pipelines(
        self,
        project: ProjectRef,
        ref: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Json]:
        """List pipelines."""
        pid = self._project_id_or_path(project)
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status

        return await self._request("GET", f"/projects/{pid}/pipelines", params=params)

    async def get_pipeline(self, project: ProjectRef, pipeline_id: int) -> Json:
        """Get a pipeline."""
        pid = self._project_id_or_path(project)
        return await self._request("GET", f"/projects/{pid}/pipelines/{pipeline_id}")

    async def list_pipeline_jobs(
        self, project: ProjectRef, pipeline_id: int, page: int = 1, per_page: int = 20
    ) -> list[Json]:
        """List jobs belonging to a pipeline."""
        pid = self._project_id_or_path(project)
        params = {"page": page, "per_page": per_page}
        return await self._request(
            "GET", f"/projects/{pid}/pipelines/{pipeline_id}/jobs", params=params
        )

    async def get_job_trace(self, project: ProjectRef, job_id: int) -> str:
        """Get CI job log/trace."""
        pid = self._project_id_or_path(project)
        return await self._request(
            "GET",
            f"/projects/{pid}/jobs/{job_id}/trace",
            accept="text/plain",
            want_text=True,
        )

    async def run_pipeline(
        self,
        project: ProjectRef,
        ref: str,
        variables: Optional[dict[str, str]] = None,
    ) -> Json:
        """Trigger a pipeline."""
        pid = self._project_id_or_path(project)
        payload: dict[str, Any] = {"ref": ref}
        if variables:
            payload["variables"] = [{"key": k, "value": v} for k, v in variables.items()]
        return await self._request("POST", f"/projects/{pid}/pipeline", json=payload)

    # Repository operations
    async def list_repository_tree(
        self,
        project: ProjectRef,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> list[Json]:
        """List repository tree."""
        pid = self._project_id_or_path(project)
        params: dict[str, Any] = {
            "path": path,
            "recursive": recursive,
            "page": page,
            "per_page": per_page,
        }
        if ref:
            params["ref"] = ref
        return await self._request("GET", f"/projects/{pid}/repository/tree", params=params)

    async def get_raw_file(
        self, project: ProjectRef, file_path: str, ref: str = "HEAD"
    ) -> str:
        """Get raw file content."""
        pid = self._project_id_or_path(project)
        encoded_file_path = self._encode_path(file_path)
        return await self._request(
            "GET",
            f"/projects/{pid}/repository/files/{encoded_file_path}/raw",
            params={"ref": ref},
            accept="text/plain",
            want_text=True,
        )
