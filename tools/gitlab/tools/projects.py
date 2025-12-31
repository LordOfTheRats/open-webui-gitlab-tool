"""Project tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import GetProjectInput, ListProjectsInput
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _project_id_or_path,
    _run_async,
)


class ListProjectsTool(BaseTool):
    """List projects you can access."""

    name: str = "gitlab_list_projects"
    description: str = (
        "List projects you can access. Can filter by search, membership status, "
        "visibility, and other criteria. Returns a list of projects."
    )
    args_schema: type[BaseModel] = ListProjectsInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        search: Optional[str] = None,
        membership: bool = True,
        owned: bool = False,
        starred: bool = False,
        visibility: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List projects (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    search=search,
                    membership=membership,
                    owned=owned,
                    starred=starred,
                    visibility=visibility,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        search: Optional[str] = None,
        membership: bool = True,
        owned: bool = False,
        starred: bool = False,
        visibility: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List projects (async)."""
        try:
            def _list_projects():
                projects = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "membership": membership,
                        "owned": owned,
                        "starred": starred,
                        "order_by": "last_activity_at",
                        "sort": "desc",
                        "page": page,
                        "per_page": 20,
                    }
                    if search:
                        params["search"] = search
                    if visibility:
                        params["visibility"] = visibility

                    page_projects = self.gitlab.projects.list(
                        as_list=False, **params
                    )
                    for p in page_projects:
                        projects.append(p.asdict())

                return projects

            projects = await _run_async(_list_projects)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("project", projects, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing projects: {str(e)}")


class GetProjectTool(BaseTool):
    """Get a single project by ID or path."""

    name: str = "gitlab_get_project"
    description: str = (
        "Get details of a single project by ID (int) or path (str like 'group/project'). "
        "Returns full project information."
    )
    args_schema: type[BaseModel] = GetProjectInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        compact: Optional[bool] = None,
    ) -> str:
        """Get project (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(project=project, compact=compact))
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        compact: Optional[bool] = None,
    ) -> str:
        """Get project (async)."""
        try:
            pid = _project_id_or_path(project)

            def _get_project():
                proj = self.gitlab.projects.get(pid)
                return proj.asdict()

            proj_data = await _run_async(_get_project)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("project", proj_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting project: {str(e)}")
