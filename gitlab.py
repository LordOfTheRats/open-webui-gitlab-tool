"""
title: GitLab (Self-hosted) Projects / Issues / Merge Requests / Repo Browsing + Writes + CI Control + Wiki
author: René Vögeli
author_url: https://github.com/LordOfTheRats
git_url: https://github.com/LordOfTheRats/open-webui-gitlab-tool
description: Access GitLab projects and work with issues, merge requests, repository files, diffs, CI pipelines, and wiki pages from Open WebUI. Includes optional repository write operations, CI pipeline controls, and wiki page CRUD operations. Supports compact output mode, helper lookup endpoints (labels/milestones/users/members), and basic retry/rate-limit handling.
required_open_webui_version: 0.4.0
requirements: httpx
version: 1.9.0
licence: MIT
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Optional, Union, Literal
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel, Field


Json = dict[str, Any]
ProjectRef = Union[int, str]  # int project_id OR "group/subgroup/project" path
GroupRef = Union[int, str]  # int group_id OR "group/subgroup" full path


# ----------------------------
# Module-level helper functions
# ----------------------------


def _encode_path(value: str) -> str:
    """
    Encode a path-like string so slashes become %2F (required by GitLab).
    """
    return quote_plus(value, safe="").replace("+", "%20")


def _project_id_or_path(project: ProjectRef) -> str:
    """
    GitLab endpoints use /projects/:id where :id can be numeric ID or URL-encoded path.
    """
    if isinstance(project, int):
        return str(project)
    return _encode_path(project)


def _group_id_or_path(group: GroupRef) -> str:
    """
    GitLab group endpoints use /groups/:id where :id can be numeric ID or URL-encoded full path.
    """
    if isinstance(group, int):
        return str(group)
    return _encode_path(group)


def _user_brief(u: Any) -> Optional[Json]:
    if not isinstance(u, dict):
        return None
    return {
        "id": u.get("id"),
        "username": u.get("username"),
        "name": u.get("name"),
        "web_url": u.get("web_url"),
    }


def _compact_one(kind: str, obj: Any) -> Any:
    if not isinstance(obj, dict):
        return obj

    if kind == "project":
        return {
            "id": obj.get("id"),
            "name": obj.get("name"),
            "path_with_namespace": obj.get("path_with_namespace"),
            "description": obj.get("description"),
            "visibility": obj.get("visibility"),
            "archived": obj.get("archived"),
            "default_branch": obj.get("default_branch"),
            "last_activity_at": obj.get("last_activity_at"),
            "web_url": obj.get("web_url"),
        }

    if kind == "issue":
        # NOTE: In compact mode we STILL include description (it's core context).
        return {
            "id": obj.get("id"),
            "iid": obj.get("iid"),
            "title": obj.get("title"),
            "description": obj.get("description"),
            "state": obj.get("state"),
            "labels": obj.get("labels"),
            "author": _user_brief(obj.get("author")),
            "assignee": (
                _user_brief(obj.get("assignee"))
                if isinstance(obj.get("assignee"), dict)
                else None
            ),
            "assignees": [
                _user_brief(a) for a in (obj.get("assignees") or [])
            ],
            "milestone": (
                (obj.get("milestone") or {}).get("title")
                if isinstance(obj.get("milestone"), dict)
                else None
            ),
            "time_stats": obj.get("time_stats"),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "due_date": obj.get("due_date"),
            "web_url": obj.get("web_url"),
        }

    if kind == "mr":
        # NOTE: In compact mode we STILL include description (it's core context).
        return {
            "id": obj.get("id"),
            "iid": obj.get("iid"),
            "title": obj.get("title"),
            "description": obj.get("description"),
            "state": obj.get("state"),
            "source_branch": obj.get("source_branch"),
            "target_branch": obj.get("target_branch"),
            "author": _user_brief(obj.get("author")),
            "assignees": [
                _user_brief(a) for a in (obj.get("assignees") or [])
            ],
            "reviewers": (
                [_user_brief(a) for a in (obj.get("reviewers") or [])]
                if isinstance(obj.get("reviewers"), list)
                else None
            ),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "merged_at": obj.get("merged_at"),
            "web_url": obj.get("web_url"),
        }

    if kind == "pipeline":
        return {
            "id": obj.get("id"),
            "iid": obj.get("iid"),
            "status": obj.get("status"),
            "ref": obj.get("ref"),
            "sha": obj.get("sha"),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "web_url": obj.get("web_url"),
        }

    if kind == "job":
        return {
            "id": obj.get("id"),
            "name": obj.get("name"),
            "stage": obj.get("stage"),
            "status": obj.get("status"),
            "ref": obj.get("ref"),
            "created_at": obj.get("created_at"),
            "started_at": obj.get("started_at"),
            "finished_at": obj.get("finished_at"),
            "web_url": obj.get("web_url"),
        }

    if kind == "label":
        return {
            "id": obj.get("id"),
            "name": obj.get("name"),
            "description": obj.get("description"),
            "color": obj.get("color"),
            "text_color": obj.get("text_color"),
        }

    if kind == "milestone":
        return {
            "id": obj.get("id"),
            "iid": obj.get("iid"),
            "title": obj.get("title"),
            "description": obj.get("description"),
            "state": obj.get("state"),
            "due_date": obj.get("due_date"),
            "start_date": obj.get("start_date"),
            "web_url": obj.get("web_url"),
        }

    if kind == "member":
        return {
            "id": obj.get("id"),
            "username": obj.get("username"),
            "name": obj.get("name"),
            "state": obj.get("state"),
            "access_level": obj.get("access_level"),
            "web_url": obj.get("web_url"),
        }

    if kind == "user":
        return {
            "id": obj.get("id"),
            "username": obj.get("username"),
            "name": obj.get("name"),
            "state": obj.get("state"),
            "web_url": obj.get("web_url"),
        }

    if kind == "note":
        # NOTE: In compact mode we STILL include body (it's the core of a comment).
        return {
            "id": obj.get("id"),
            "body": obj.get("body"),
            "author": _user_brief(obj.get("author")),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "system": obj.get("system"),
            "type": obj.get("type"),
        }

    if kind == "wiki":
        # NOTE: In compact mode we STILL include content (it's the core of a wiki page).
        return {
            "slug": obj.get("slug"),
            "title": obj.get("title"),
            "content": obj.get("content"),
            "format": obj.get("format"),
            "encoding": obj.get("encoding"),
        }

    return obj


class Tools:
    """
    Open WebUI Toolkit for GitLab.
    """

    def __init__(self):
        self.valves = self.Valves()

    class Valves(BaseModel):
        base_url: str = Field(
            "https://gitlab.example.com",
            description="Base URL for your GitLab instance, e.g. https://gitlab.example.com",
        )
        token: str = Field(
            "",
            description="GitLab Personal Access Token (PAT) with api scope",
        )
        verify_ssl: bool = Field(
            True,
            description="Verify TLS certificates (disable only for lab/self-signed setups)",
        )
        timeout_seconds: float = Field(
            30.0,
            description="HTTP request timeout in seconds",
        )
        per_page: int = Field(
            20,
            description="Default page size for list endpoints (GitLab pagination)",
        )
        allow_repo_writes: bool = Field(
            False,
            description="Safety valve: allow repository write operations (create/update/delete files) via the commits API.",
        )
        compact_results_default: bool = Field(
            True,
            description=(
                "Default compact mode for responses. "
                "When true, tool returns a reduced field set (but still includes descriptions and note bodies)."
            ),
        )

        # Retry / rate-limit handling
        max_retries: int = Field(
            3,
            description="Max retries for transient failures (429/502/503/504/timeouts). 0 disables retries.",
        )
        backoff_initial_seconds: float = Field(
            0.8,
            description="Initial backoff delay for retries (seconds).",
        )
        backoff_max_seconds: float = Field(
            10.0,
            description="Maximum backoff delay (seconds).",
        )
        retry_jitter: float = Field(
            0.2,
            description="Adds +/- jitter proportion of delay to spread retries (0.2 = +/-20%).",
        )

    # ----------------------------
    # Internal helpers (valves-dependent)
    # ----------------------------

    def _api_base(self) -> str:
        return self.valves.base_url.rstrip("/") + "/api/v4"

    def _headers(self) -> dict[str, str]:
        if not self.valves.token:
            raise ValueError(
                "GitLab token is not set. Configure the tool Valves: token=..."
            )

        return {"PRIVATE-TOKEN": self.valves.token, "Content-Type": "application/json"}

    def _ensure_writes_allowed(self) -> None:
        if not self.valves.allow_repo_writes:
            raise PermissionError(
                "Repository write operations are disabled. Set Valves.allow_repo_writes=true to enable."
            )

    def _want_compact(self, compact: Optional[bool]) -> bool:
        return self.valves.compact_results_default if compact is None else bool(compact)

    def _maybe_compact(self, kind: str, data: Any, compact: Optional[bool]) -> Any:
        if not self._want_compact(compact):
            return data
        if isinstance(data, list):
            return [_compact_one(kind, x) for x in data]
        return _compact_one(kind, data)

    def _compute_delay(
        self, attempt: int, retry_after: Optional[float] = None
    ) -> float:
        if retry_after is not None and retry_after > 0:
            base = float(retry_after)
        else:
            base = float(self.valves.backoff_initial_seconds) * (2 ** (attempt - 1))

        base = min(base, float(self.valves.backoff_max_seconds))

        jitter = float(self.valves.retry_jitter)
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
        url = self._api_base() + path
        headers = self._headers()
        if accept:
            headers = dict(headers)
            headers["Accept"] = accept

        max_retries = max(0, int(self.valves.max_retries))

        async with httpx.AsyncClient(
            verify=self.valves.verify_ssl,
            timeout=self.valves.timeout_seconds,
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
                        delay = self._compute_delay(
                            attempt=attempt + 1, retry_after=retry_after
                        )
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
                        delay = self._compute_delay(
                            attempt=attempt + 1, retry_after=None
                        )
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
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if page_count < 1:
            raise ValueError("page_count must be >= 1")

        params = dict(params or {})
        params.setdefault("per_page", self.valves.per_page)

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

    # ----------------------------
    # Projects
    # ----------------------------

    async def gitlab_list_projects(
        self,
        search: Optional[str] = None,
        membership: bool = True,
        owned: bool = False,
        starred: bool = False,
        simple: bool = True,
        visibility: Optional[Literal["private", "internal", "public"]] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List projects you can access.

        Args:
          search: Optional substring filter for project name/path.
          membership: If true, limit to projects you are a member of.
          owned: If true, limit to projects you own.
          starred: If true, limit to projects you starred.
          simple: If true, GitLab returns a reduced project payload (GitLab-side).
          visibility: One of: "private" | "internal" | "public" (or None to not filter).
          offset: Page offset (0-based). offset=0 -> page 1, offset=1 -> page 2, ...
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set (tool-side).
        """
        params: dict[str, Any] = {
            "membership": membership,
            "owned": owned,
            "starred": starred,
            "simple": simple,
            "order_by": "last_activity_at",
            "sort": "desc",
        }
        if search:
            params["search"] = search
        if visibility:
            params["visibility"] = visibility

        data = await self._paginate(
            "/projects", params=params, offset=offset, page_count=page_count
        )
        return self._maybe_compact("project", data, compact)

    async def gitlab_get_project(
        self, project: ProjectRef, compact: Optional[bool] = None
    ) -> Json:
        """
        Get a single project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        data = await self._request("GET", f"/projects/{pid}")
        return self._maybe_compact("project", data, compact)

    # ----------------------------
    # Helper lookups
    # ----------------------------

    async def gitlab_list_labels(
        self,
        project: ProjectRef,
        search: Optional[str] = None,
        include_ancestor_groups: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List labels for a project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          search: Optional substring filter for label name.
          include_ancestor_groups: If true, also includes labels inherited from ancestor groups.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {
            "with_counts": False,
            "include_ancestor_groups": include_ancestor_groups,
        }
        if search:
            params["search"] = search
        data = await self._paginate(
            f"/projects/{pid}/labels",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("label", data, compact)

    async def gitlab_list_milestones(
        self,
        project: ProjectRef,
        state: Optional[Literal["active", "closed", "all"]] = "active",
        search: Optional[str] = None,
        exclude_group_milestones: bool = False,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List milestones for a project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          state: One of: "active" | "closed" | "all". If unknown, pass None to omit the param.
          search: Optional substring filter for milestone title.
          exclude_group_milestones: If false (default), includes group/parent milestones when supported by GitLab.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {}
        if state is not None:
            params["state"] = state
        if search:
            params["search"] = search

        if not exclude_group_milestones:
            params["include_parent_milestones"] = True

        data = await self._paginate(
            f"/projects/{pid}/milestones",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("milestone", data, compact)

    async def gitlab_list_group_milestones(
        self,
        group: GroupRef,
        state: Optional[Literal["active", "closed", "all"]] = "active",
        search: Optional[str] = None,
        include_subgroups: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List milestones for a group.

        Args:
          group: Numeric group ID or "group/subgroup" full path.
          state: One of: "active" | "closed" | "all". If unknown, pass None to omit the param.
          search: Optional substring filter for milestone title.
          include_subgroups: If true, includes milestones from subgroups as well.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        gid = _group_id_or_path(group)
        params: dict[str, Any] = {"include_subgroups": include_subgroups}
        if state is not None:
            params["state"] = state
        if search:
            params["search"] = search
        data = await self._paginate(
            f"/groups/{gid}/milestones",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("milestone", data, compact)

    async def gitlab_search_users(
        self,
        search: str,
        active: Optional[bool] = None,
        external: Optional[bool] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        Search users by name/username.

        Args:
          search: Query string.
          active: If set, filter active users (True/False).
          external: If set, filter external users (True/False).
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        params: dict[str, Any] = {"search": search}
        if active is not None:
            params["active"] = active
        if external is not None:
            params["external"] = external
        data = await self._paginate(
            "/users", params=params, offset=offset, page_count=page_count
        )
        return self._maybe_compact("user", data, compact)

    async def gitlab_list_project_members(
        self,
        project: ProjectRef,
        query: Optional[str] = None,
        include_inherited: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List project members.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          query: Optional substring filter for username/name.
          include_inherited: If true, includes members inherited from groups.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {}
        if query:
            params["query"] = query
        endpoint = (
            f"/projects/{pid}/members/all"
            if include_inherited
            else f"/projects/{pid}/members"
        )
        data = await self._paginate(
            endpoint, params=params, offset=offset, page_count=page_count
        )
        return self._maybe_compact("member", data, compact)

    # ----------------------------
    # Issues (read / create)
    # ----------------------------

    async def gitlab_list_issues(
        self,
        project: ProjectRef,
        state: Optional[Literal["opened", "closed", "all"]] = "opened",
        labels: Optional[str] = None,
        assignee_username: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List issues.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          state: One of: "opened" | "closed" | "all".
          labels: Comma-separated label names (e.g. "bug,backend").
          assignee_username: Assignee username (not name). If you only have a display name/email,
            first resolve via gitlab_search_users(search="...") and use the returned "username".
          search: Full-text search query.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"state": state}
        if labels:
            params["labels"] = labels
        if assignee_username:
            params["assignee_username"] = assignee_username
        if search:
            params["search"] = search

        data = await self._paginate(
            f"/projects/{pid}/issues",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("issue", data, compact)

    async def gitlab_get_issue(
        self, project: ProjectRef, issue_iid: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Get a single issue by IID.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID (project-scoped integer).
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        data = await self._request("GET", f"/projects/{pid}/issues/{issue_iid}")
        return self._maybe_compact("issue", data, compact)

    async def gitlab_create_issue(
        self,
        project: ProjectRef,
        title: str,
        description: Optional[str] = None,
        labels: Optional[str] = None,
        assignee_id: Optional[int] = None,
        milestone_id: Optional[int] = None,
        due_date: Optional[str] = None,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Create an issue (single assignee).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          title: Issue title.
          description: Issue description (Markdown).
          labels: Comma-separated label names.
          assignee_id: Numeric GitLab user ID.
            If you only have a username or name, resolve it first via gitlab_search_users(search="...") and use "id".
          milestone_id: Milestone numeric id (not IID).
          due_date: "YYYY-MM-DD" (or None).
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {"title": title}
        if description is not None:
            payload["description"] = description
        if labels:
            payload["labels"] = labels
        if assignee_id is not None:
            payload["assignee_ids"] = [assignee_id]  # enforce single assignee
        if milestone_id is not None:
            payload["milestone_id"] = milestone_id
        if due_date is not None:
            payload["due_date"] = due_date

        data = await self._request("POST", f"/projects/{pid}/issues", json=payload)
        return self._maybe_compact("issue", data, compact)

    # ----------------------------
    # Issues (edit/update)
    # ----------------------------

    async def gitlab_update_issue(
        self,
        project: ProjectRef,
        issue_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[int] = None,
        unassign: bool = False,
        labels: Optional[str] = None,
        add_labels: Optional[str] = None,
        remove_labels: Optional[str] = None,
        due_date: Optional[str] = None,
        clear_due_date: bool = False,
        milestone_id: Optional[int] = None,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Update an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID (project-scoped integer).
          title: New title (or None to keep).
          description: New description (or None to keep).
          assignee_id: Numeric GitLab user ID to assign (ignored if unassign=True).
            If you only have a username or name, resolve it first via gitlab_search_users(search="...") and use "id".
          unassign: If true, removes assignee (sets assignee_ids=[]).
          labels: Replace ALL labels (comma-separated).
          add_labels: Add labels (comma-separated) without removing others.
          remove_labels: Remove labels (comma-separated) without adding others.
          due_date: Set due date "YYYY-MM-DD" (ignored if clear_due_date=True).
          clear_due_date: If true, removes due date.
          milestone_id: Set milestone numeric id (not IID).
          compact: If true, tool returns a reduced field set (still includes description).

        Notes:
          - Single assignee behavior: use assignee_id=<user_id> OR unassign=True.
          - Prefer add_labels/remove_labels for incremental label changes.
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {}

        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description

        if unassign:
            payload["assignee_ids"] = []
        elif assignee_id is not None:
            payload["assignee_ids"] = [assignee_id]

        if milestone_id is not None:
            payload["milestone_id"] = milestone_id

        if labels is not None:
            payload["labels"] = labels
        if add_labels is not None:
            payload["add_labels"] = add_labels
        if remove_labels is not None:
            payload["remove_labels"] = remove_labels

        if clear_due_date:
            payload["due_date"] = None
        elif due_date is not None:
            payload["due_date"] = due_date

        data = await self._request(
            "PUT",
            f"/projects/{pid}/issues/{issue_iid}",
            json=payload if payload else None,
        )
        return self._maybe_compact("issue", data, compact)

    async def gitlab_set_issue_description(
        self,
        project: ProjectRef,
        issue_iid: int,
        description: str,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Set issue description (replaces existing).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          description: New description (Markdown).
          compact: If true, tool returns a reduced field set (still includes description).
        """
        return await self.gitlab_update_issue(
            project, issue_iid, description=description, compact=compact
        )

    async def gitlab_set_issue_assignee(
        self,
        project: ProjectRef,
        issue_iid: int,
        assignee_id: Optional[int],
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Assign exactly one user, or unassign.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          assignee_id: Numeric GitLab user ID.
            If you only have a username or name, resolve it first via gitlab_search_users(search="...") and use "id".
            Pass None to unassign the issue.
          compact: If true, tool returns a reduced field set (still includes description).
        """
        if assignee_id is None:
            return await self.gitlab_update_issue(
                project, issue_iid, unassign=True, compact=compact
            )
        return await self.gitlab_update_issue(
            project, issue_iid, assignee_id=assignee_id, compact=compact
        )

    async def gitlab_add_issue_labels(
        self,
        project: ProjectRef,
        issue_iid: int,
        labels: str,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Add labels to an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          labels: Comma-separated label names to add.
          compact: If true, tool returns a reduced field set.
        """
        return await self.gitlab_update_issue(
            project, issue_iid, add_labels=labels, compact=compact
        )

    async def gitlab_remove_issue_labels(
        self,
        project: ProjectRef,
        issue_iid: int,
        labels: str,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Remove labels from an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          labels: Comma-separated label names to remove.
          compact: If true, tool returns a reduced field set.
        """
        return await self.gitlab_update_issue(
            project, issue_iid, remove_labels=labels, compact=compact
        )

    async def gitlab_set_issue_labels(
        self,
        project: ProjectRef,
        issue_iid: int,
        labels: str,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Replace ALL labels on an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          labels: Comma-separated label names to set (replaces all).
          compact: If true, tool returns a reduced field set.
        """
        return await self.gitlab_update_issue(
            project, issue_iid, labels=labels, compact=compact
        )

    async def gitlab_set_issue_due_date(
        self,
        project: ProjectRef,
        issue_iid: int,
        due_date: Optional[str],
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Set or clear issue due date.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          due_date: "YYYY-MM-DD" or None to clear.
          compact: If true, tool returns a reduced field set.
        """
        if due_date is None:
            return await self.gitlab_update_issue(
                project, issue_iid, clear_due_date=True, compact=compact
            )
        return await self.gitlab_update_issue(
            project, issue_iid, due_date=due_date, compact=compact
        )

    async def gitlab_set_issue_time_estimate(
        self,
        project: ProjectRef,
        issue_iid: int,
        duration: str,
    ) -> Json:
        """
        Set time estimate.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          duration: GitLab duration string, e.g. "1h", "30m", "2d 3h".
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST",
            f"/projects/{pid}/issues/{issue_iid}/time_estimate",
            json={"duration": duration},
        )

    async def gitlab_reset_issue_time_estimate(
        self, project: ProjectRef, issue_iid: int
    ) -> Json:
        """
        Reset/clear time estimate.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST", f"/projects/{pid}/issues/{issue_iid}/reset_time_estimate"
        )

    async def gitlab_add_issue_spent_time(
        self,
        project: ProjectRef,
        issue_iid: int,
        duration: str,
    ) -> Json:
        """
        Add spent time.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          duration: GitLab duration string, e.g. "15m", "1h".
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST",
            f"/projects/{pid}/issues/{issue_iid}/add_spent_time",
            json={"duration": duration},
        )

    async def gitlab_reset_issue_spent_time(
        self, project: ProjectRef, issue_iid: int
    ) -> Json:
        """
        Reset spent time to 0.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST", f"/projects/{pid}/issues/{issue_iid}/reset_spent_time"
        )

    async def gitlab_add_issue_note(
        self, project: ProjectRef, issue_iid: int, body: str
    ) -> Json:
        """
        Add a note/comment to an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          body: Comment text (Markdown).
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST", f"/projects/{pid}/issues/{issue_iid}/notes", json={"body": body}
        )

    async def gitlab_list_issue_notes(
        self,
        project: ProjectRef,
        issue_iid: int,
        sort: Optional[Literal["asc", "desc"]] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List issue notes/comments.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          sort: "asc" | "desc" (chronological order).
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set (still includes note body).
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"sort": sort}
        data = await self._paginate(
            f"/projects/{pid}/issues/{issue_iid}/notes",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("note", data, compact)

    async def gitlab_close_issue(
        self, project: ProjectRef, issue_iid: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Close an issue.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          issue_iid: Issue IID.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        data = await self._request(
            "PUT", f"/projects/{pid}/issues/{issue_iid}", json={"state_event": "close"}
        )
        return self._maybe_compact("issue", data, compact)

    # ----------------------------
    # Merge Requests
    # ----------------------------

    async def gitlab_list_merge_requests(
        self,
        project: ProjectRef,
        state: Optional[
            Literal["opened", "closed", "locked", "merged", "all"]
        ] = "opened",
        source_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List merge requests.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          state: One of: "opened" | "closed" | "locked" | "merged" | "all".
          source_branch: Filter by source branch.
          target_branch: Filter by target branch.
          search: Full-text search query.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"state": state}
        if source_branch:
            params["source_branch"] = source_branch
        if target_branch:
            params["target_branch"] = target_branch
        if search:
            params["search"] = search

        data = await self._paginate(
            f"/projects/{pid}/merge_requests",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("mr", data, compact)

    async def gitlab_get_merge_request(
        self, project: ProjectRef, mr_iid: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Get a single merge request by IID.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          mr_iid: Merge request IID (project-scoped integer).
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        data = await self._request("GET", f"/projects/{pid}/merge_requests/{mr_iid}")
        return self._maybe_compact("mr", data, compact)

    async def gitlab_create_merge_request(
        self,
        project: ProjectRef,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        remove_source_branch: bool = False,
        squash: Optional[bool] = None,
        draft: bool = False,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Create a merge request.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          source_branch: Source branch name.
          target_branch: Target branch name.
          title: MR title (if draft=True, tool will prefix "Draft: ").
          description: MR description (Markdown).
          remove_source_branch: If true, removes source branch after merge.
          squash: If set, overrides project squash behavior for this MR.
          draft: If true, prefixes title with "Draft: " (if not already).
          compact: If true, tool returns a reduced field set (still includes description).
        """
        pid = _project_id_or_path(project)
        final_title = (
            f"Draft: {title}"
            if draft and not title.lower().startswith("draft:")
            else title
        )

        payload: dict[str, Any] = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": final_title,
            "remove_source_branch": remove_source_branch,
        }
        if description is not None:
            payload["description"] = description
        if squash is not None:
            payload["squash"] = squash

        data = await self._request(
            "POST", f"/projects/{pid}/merge_requests", json=payload
        )
        return self._maybe_compact("mr", data, compact)

    async def gitlab_add_mr_note(
        self, project: ProjectRef, mr_iid: int, body: str
    ) -> Json:
        """
        Add a note/comment to an MR.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          mr_iid: MR IID.
          body: Comment text (Markdown).
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "POST",
            f"/projects/{pid}/merge_requests/{mr_iid}/notes",
            json={"body": body},
        )

    async def gitlab_list_mr_notes(
        self,
        project: ProjectRef,
        mr_iid: int,
        sort: Optional[Literal["asc", "desc"]] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List MR notes/comments.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          mr_iid: MR IID.
          sort: "asc" | "desc".
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set (still includes note body).
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"sort": sort}
        data = await self._paginate(
            f"/projects/{pid}/merge_requests/{mr_iid}/notes",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("note", data, compact)

    async def gitlab_approve_merge_request(
        self, project: ProjectRef, mr_iid: int, sha: Optional[str] = None
    ) -> Json:
        """
        Approve a merge request.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          mr_iid: MR IID.
          sha: Optional commit SHA to approve (useful to avoid approving outdated changes).
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {}
        if sha:
            payload["sha"] = sha
        return await self._request(
            "POST",
            f"/projects/{pid}/merge_requests/{mr_iid}/approve",
            json=payload if payload else None,
        )

    async def gitlab_merge_merge_request(
        self,
        project: ProjectRef,
        mr_iid: int,
        merge_commit_message: Optional[str] = None,
        squash_commit_message: Optional[str] = None,
        should_remove_source_branch: Optional[bool] = None,
        squash: Optional[bool] = None,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Merge a merge request.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          mr_iid: MR IID.
          merge_commit_message: Optional merge commit message.
          squash_commit_message: Optional squash commit message.
          should_remove_source_branch: If set, overrides MR setting.
          squash: If set, overrides MR setting.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {}
        if merge_commit_message is not None:
            payload["merge_commit_message"] = merge_commit_message
        if squash_commit_message is not None:
            payload["squash_commit_message"] = squash_commit_message
        if should_remove_source_branch is not None:
            payload["should_remove_source_branch"] = should_remove_source_branch
        if squash is not None:
            payload["squash"] = squash

        data = await self._request(
            "PUT",
            f"/projects/{pid}/merge_requests/{mr_iid}/merge",
            json=payload if payload else None,
        )
        return self._maybe_compact("mr", data, compact)

    # ----------------------------
    # Repository browsing
    # ----------------------------

    async def gitlab_list_repository_tree(
        self,
        project: ProjectRef,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = False,
        offset: int = 0,
        page_count: int = 1,
    ) -> list[Json]:
        """
        List repository tree (files/folders) for a project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          path: Folder path inside the repository ("" for root).
          ref: Branch/tag/commit (e.g. "main"); if None, GitLab uses default branch.
          recursive: If true, lists recursively.
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"path": path, "recursive": recursive}
        if ref:
            params["ref"] = ref
        return await self._paginate(
            f"/projects/{pid}/repository/tree",
            params=params,
            offset=offset,
            page_count=page_count,
        )

    async def gitlab_get_file(
        self, project: ProjectRef, file_path: str, ref: str = "HEAD"
    ) -> Json:
        """
        Get file metadata/content (base64) from repository.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          file_path: Path to file in repo.
          ref: Branch/tag/commit (default "HEAD").
        """
        pid = _project_id_or_path(project)
        encoded_file_path = _encode_path(file_path)
        return await self._request(
            "GET",
            f"/projects/{pid}/repository/files/{encoded_file_path}",
            params={"ref": ref},
        )

    async def gitlab_get_raw_file(
        self, project: ProjectRef, file_path: str, ref: str = "HEAD"
    ) -> str:
        """
        Get raw file content as text.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          file_path: Path to file in repo.
          ref: Branch/tag/commit (default "HEAD").
        """
        pid = _project_id_or_path(project)
        encoded_file_path = _encode_path(file_path)
        return await self._request(
            "GET",
            f"/projects/{pid}/repository/files/{encoded_file_path}/raw",
            params={"ref": ref},
            accept="text/plain",
            want_text=True,
        )

    async def gitlab_compare(
        self, project: ProjectRef, from_ref: str, to_ref: str, straight: bool = False
    ) -> Json:
        """
        Compare two refs (commits/branches/tags).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          from_ref: Source ref.
          to_ref: Target ref.
          straight: If true, uses straight comparison.
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "GET",
            f"/projects/{pid}/repository/compare",
            params={"from": from_ref, "to": to_ref, "straight": straight},
        )

    # ----------------------------
    # Repository writes (Commits API)
    # ----------------------------

    async def gitlab_create_commit(
        self,
        project: ProjectRef,
        branch: str,
        commit_message: str,
        actions: list[Json],
        start_branch: Optional[str] = None,
        author_email: Optional[str] = None,
        author_name: Optional[str] = None,
    ) -> Json:
        """
        Create a commit with multiple actions (advanced).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          branch: Branch name to commit to.
          commit_message: Commit message.
          actions: GitLab commit actions list (create/update/delete/move/chmod).
          start_branch: If set, creates branch from this ref before committing (when branch doesn't exist).
          author_email: Optional author email.
          author_name: Optional author name.

        Note:
          - Requires Valves.allow_repo_writes=true.
        """
        self._ensure_writes_allowed()
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": actions,
        }
        if start_branch is not None:
            payload["start_branch"] = start_branch
        if author_email is not None:
            payload["author_email"] = author_email
        if author_name is not None:
            payload["author_name"] = author_name
        return await self._request(
            "POST", f"/projects/{pid}/repository/commits", json=payload
        )

    async def gitlab_create_or_update_file(
        self,
        project: ProjectRef,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str,
        encoding: Literal["text", "base64"] = "text",
        start_branch: Optional[str] = None,
        execute_filemode: Optional[bool] = None,
    ) -> Json:
        """
        Create or update a file (single-action commit).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          branch: Branch name to commit to.
          file_path: Path to file in repo.
          content: New file content.
          commit_message: Commit message.
          encoding: "text" or "base64".
          start_branch: If set, creates branch from this ref before committing (when branch doesn't exist).
          execute_filemode: If set, toggles executable bit.

        Note:
          - Requires Valves.allow_repo_writes=true.
        """
        self._ensure_writes_allowed()
        pid = _project_id_or_path(project)

        exists = True
        try:
            encoded_file_path = _encode_path(file_path)
            await self._request(
                "GET",
                f"/projects/{pid}/repository/files/{encoded_file_path}",
                params={"ref": branch},
            )
        except RuntimeError:
            exists = False

        action: dict[str, Any] = {
            "action": "update" if exists else "create",
            "file_path": file_path,
            "content": content,
            "encoding": encoding,
        }
        if execute_filemode is not None:
            action["execute_filemode"] = execute_filemode

        payload: dict[str, Any] = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [action],
        }
        if start_branch is not None:
            payload["start_branch"] = start_branch

        return await self._request(
            "POST", f"/projects/{pid}/repository/commits", json=payload
        )

    async def gitlab_delete_file(
        self,
        project: ProjectRef,
        branch: str,
        file_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> Json:
        """
        Delete a file (single-action commit).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          branch: Branch name.
          file_path: Path to file in repo.
          commit_message: Commit message.
          start_branch: If set, creates branch from this ref before committing (when branch doesn't exist).

        Note:
          - Requires Valves.allow_repo_writes=true.
        """
        self._ensure_writes_allowed()
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [{"action": "delete", "file_path": file_path}],
        }
        if start_branch is not None:
            payload["start_branch"] = start_branch
        return await self._request(
            "POST", f"/projects/{pid}/repository/commits", json=payload
        )

    async def gitlab_move_file(
        self,
        project: ProjectRef,
        branch: str,
        file_path: str,
        previous_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> Json:
        """
        Move/rename a file (single-action commit).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          branch: Branch name.
          file_path: New path.
          previous_path: Old path.
          commit_message: Commit message.
          start_branch: If set, creates branch from this ref before committing (when branch doesn't exist).

        Note:
          - Requires Valves.allow_repo_writes=true.
        """
        self._ensure_writes_allowed()
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [
                {
                    "action": "move",
                    "file_path": file_path,
                    "previous_path": previous_path,
                }
            ],
        }
        if start_branch is not None:
            payload["start_branch"] = start_branch
        return await self._request(
            "POST", f"/projects/{pid}/repository/commits", json=payload
        )

    async def gitlab_chmod_file(
        self,
        project: ProjectRef,
        branch: str,
        file_path: str,
        execute_filemode: bool,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> Json:
        """
        Change executable bit on a file (single-action commit).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          branch: Branch name.
          file_path: Path to file.
          execute_filemode: True to set executable bit, False to unset.
          commit_message: Commit message.
          start_branch: If set, creates branch from this ref before committing (when branch doesn't exist).

        Note:
          - Requires Valves.allow_repo_writes=true.
        """
        self._ensure_writes_allowed()
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": [
                {
                    "action": "chmod",
                    "file_path": file_path,
                    "execute_filemode": execute_filemode,
                }
            ],
        }
        if start_branch is not None:
            payload["start_branch"] = start_branch
        return await self._request(
            "POST", f"/projects/{pid}/repository/commits", json=payload
        )

    # ----------------------------
    # CI / Pipelines
    # ----------------------------

    async def gitlab_list_pipelines(
        self,
        project: ProjectRef,
        ref: Optional[str] = None,
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
        ] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List pipelines for a project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          ref: Filter by ref/branch (e.g. "main").
          status: One of:
            "created" | "waiting_for_resource" | "preparing" | "pending" | "running" |
            "success" | "failed" | "canceled" | "skipped" | "manual" | "scheduled"
            (or None to not filter).
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {}
        if ref:
            params["ref"] = ref
        if status:
            params["status"] = status
        data = await self._paginate(
            f"/projects/{pid}/pipelines",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("pipeline", data, compact)

    async def gitlab_get_pipeline(
        self, project: ProjectRef, pipeline_id: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Get a pipeline.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          pipeline_id: Pipeline numeric id.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        data = await self._request("GET", f"/projects/{pid}/pipelines/{pipeline_id}")
        return self._maybe_compact("pipeline", data, compact)

    async def gitlab_list_pipeline_jobs(
        self,
        project: ProjectRef,
        pipeline_id: int,
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
        ] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List jobs belonging to a pipeline.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          pipeline_id: Pipeline numeric id.
          scope: One of:
            "created" | "pending" | "running" | "failed" | "success" | "canceled" | "skipped" | "manual"
            (or None to not filter).
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {}
        if scope:
            params["scope"] = scope
        data = await self._paginate(
            f"/projects/{pid}/pipelines/{pipeline_id}/jobs",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("job", data, compact)

    async def gitlab_get_job_trace(self, project: ProjectRef, job_id: int) -> str:
        """
        Get CI job log/trace (plain text).

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          job_id: Job numeric id.
        """
        pid = _project_id_or_path(project)
        return await self._request(
            "GET",
            f"/projects/{pid}/jobs/{job_id}/trace",
            accept="text/plain",
            want_text=True,
        )

    async def gitlab_run_pipeline(
        self,
        project: ProjectRef,
        ref: str,
        variables: Optional[dict[str, str]] = None,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Trigger a pipeline.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          ref: Branch/tag name to run pipeline on.
          variables: Optional dict of CI variables (key -> value).
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {"ref": ref}
        if variables:
            payload["variables"] = [
                {"key": k, "value": v} for k, v in variables.items()
            ]
        data = await self._request("POST", f"/projects/{pid}/pipeline", json=payload)
        return self._maybe_compact("pipeline", data, compact)

    async def gitlab_retry_job(
        self, project: ProjectRef, job_id: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Retry a CI job.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          job_id: Job numeric id.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        data = await self._request("POST", f"/projects/{pid}/jobs/{job_id}/retry")
        return self._maybe_compact("job", data, compact)

    async def gitlab_cancel_job(
        self, project: ProjectRef, job_id: int, compact: Optional[bool] = None
    ) -> Json:
        """
        Cancel a CI job.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          job_id: Job numeric id.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        data = await self._request("POST", f"/projects/{pid}/jobs/{job_id}/cancel")
        return self._maybe_compact("job", data, compact)

    # ----------------------------
    # Wiki Operations
    # ----------------------------

    async def gitlab_list_wiki_pages(
        self,
        project: ProjectRef,
        with_content: bool = False,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> list[Json]:
        """
        List wiki pages for a project.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          with_content: If true, returns full page content (may be large for many pages).
          offset: Page offset (0-based).
          page_count: Number of pages to fetch starting from offset.
          compact: If true, tool returns a reduced field set.
        """
        pid = _project_id_or_path(project)
        params: dict[str, Any] = {"with_content": with_content}
        data = await self._paginate(
            f"/projects/{pid}/wikis",
            params=params,
            offset=offset,
            page_count=page_count,
        )
        return self._maybe_compact("wiki", data, compact)

    async def gitlab_get_wiki_page(
        self,
        project: ProjectRef,
        slug: str,
        version: Optional[str] = None,
        render_html: bool = False,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Get a single wiki page by slug.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          slug: Wiki page slug (URL-friendly identifier).
          version: Optional version ID to retrieve a specific version.
          render_html: If true, returns content rendered as HTML (GitLab API feature).
          compact: If true, tool returns a reduced field set (still includes content).
        """
        pid = _project_id_or_path(project)
        encoded_slug = _encode_path(slug)
        params: dict[str, Any] = {"render_html": render_html}
        if version is not None:
            params["version"] = version
        data = await self._request(
            "GET", f"/projects/{pid}/wikis/{encoded_slug}", params=params
        )
        return self._maybe_compact("wiki", data, compact)

    async def gitlab_create_wiki_page(
        self,
        project: ProjectRef,
        title: str,
        content: str,
        format: Literal["markdown", "rdoc", "asciidoc", "org"] = "markdown",
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Create a new wiki page.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          title: Wiki page title (will be converted to slug automatically by GitLab).
          content: Wiki page content.
          format: Content format: "markdown" | "rdoc" | "asciidoc" | "org" (default: "markdown").
          compact: If true, tool returns a reduced field set (still includes content).
        """
        pid = _project_id_or_path(project)
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "format": format,
        }
        data = await self._request("POST", f"/projects/{pid}/wikis", json=payload)
        return self._maybe_compact("wiki", data, compact)

    async def gitlab_update_wiki_page(
        self,
        project: ProjectRef,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        format: Optional[Literal["markdown", "rdoc", "asciidoc", "org"]] = None,
        compact: Optional[bool] = None,
    ) -> Json:
        """
        Update an existing wiki page.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          slug: Wiki page slug (URL-friendly identifier).
          title: New title (or None to keep existing).
          content: New content (or None to keep existing).
          format: Content format: "markdown" | "rdoc" | "asciidoc" | "org" (or None to keep existing).
          compact: If true, tool returns a reduced field set (still includes content).
        """
        pid = _project_id_or_path(project)
        encoded_slug = _encode_path(slug)
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if format is not None:
            payload["format"] = format

        data = await self._request(
            "PUT",
            f"/projects/{pid}/wikis/{encoded_slug}",
            json=payload if payload else None,
        )
        return self._maybe_compact("wiki", data, compact)

    async def gitlab_delete_wiki_page(
        self, project: ProjectRef, slug: str
    ) -> Json:
        """
        Delete a wiki page.

        Args:
          project: Numeric project ID or "group/subgroup/project" path.
          slug: Wiki page slug (URL-friendly identifier).
        """
        pid = _project_id_or_path(project)
        encoded_slug = _encode_path(slug)
        return await self._request("DELETE", f"/projects/{pid}/wikis/{encoded_slug}")
