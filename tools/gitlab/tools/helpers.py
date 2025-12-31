"""Helper/Lookup tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    ListLabelsInput,
    ListMilestonesInput,
    ListProjectMembersInput,
    SearchUsersInput,
)
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _project_id_or_path,
    _run_async,
)


class SearchUsersTool(BaseTool):
    """Search for users."""

    name: str = "gitlab_search_users"
    description: str = (
        "Search for GitLab users by username or name. Useful for finding user IDs to assign issues/MRs. "
        "Returns matching users."
    )
    args_schema: type[BaseModel] = SearchUsersInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        search: str,
        active: Optional[bool] = None,
        external: Optional[bool] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """Search users (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    search=search,
                    active=active,
                    external=external,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        search: str,
        active: Optional[bool] = None,
        external: Optional[bool] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """Search users (async)."""
        try:
            def _search_users():
                users = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "search": search,
                        "page": page,
                        "per_page": 20,
                    }
                    if active is not None:
                        params["active"] = active
                    if external is not None:
                        params["external"] = external

                    page_users = self.gitlab.users.list(as_list=False, **params)
                    for user in page_users:
                        users.append(user.asdict())

                return users

            users = await _run_async(_search_users)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("user", users, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error searching users: {str(e)}")


class ListLabelsTool(BaseTool):
    """List project labels."""

    name: str = "gitlab_list_labels"
    description: str = (
        "List all labels available in a project, with optional search filter. "
        "Useful for finding label names/IDs. Returns available labels."
    )
    args_schema: type[BaseModel] = ListLabelsInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        search: Optional[str] = None,
        include_ancestor_groups: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List labels (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    search=search,
                    include_ancestor_groups=include_ancestor_groups,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        search: Optional[str] = None,
        include_ancestor_groups: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List labels (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_labels():
                labels = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "with_counts": False,
                        "include_ancestor_groups": include_ancestor_groups,
                        "page": page,
                        "per_page": 20,
                    }
                    if search:
                        params["search"] = search

                    page_labels = self.gitlab.projects.get(pid).labels.list(
                        as_list=False, **params
                    )
                    for label in page_labels:
                        labels.append(label.asdict())

                return labels

            labels = await _run_async(_list_labels)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("label", labels, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing labels: {str(e)}")


class ListMilestonesTool(BaseTool):
    """List project milestones."""

    name: str = "gitlab_list_milestones"
    description: str = (
        "List all milestones in a project with optional state filter and search. "
        "Useful for finding milestone IDs. Returns available milestones."
    )
    args_schema: type[BaseModel] = ListMilestonesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        state: Optional[str] = "active",
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List milestones (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    state=state,
                    search=search,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        state: Optional[str] = "active",
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List milestones (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_milestones():
                milestones = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if state is not None:
                        params["state"] = state
                    if search:
                        params["search"] = search

                    page_milestones = self.gitlab.projects.get(
                        pid
                    ).milestones.list(as_list=False, **params)
                    for milestone in page_milestones:
                        milestones.append(milestone.asdict())

                return milestones

            milestones = await _run_async(_list_milestones)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("milestone", milestones, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing milestones: {str(e)}")


class ListProjectMembersTool(BaseTool):
    """List project members."""

    name: str = "gitlab_list_project_members"
    description: str = (
        "List all members of a project with optional search and inheritance settings. "
        "Returns member information including access levels."
    )
    args_schema: type[BaseModel] = ListProjectMembersInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        query: Optional[str] = None,
        include_inherited: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List project members (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    query=query,
                    include_inherited=include_inherited,
                    offset=offset,
                    page_count=page_count,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        query: Optional[str] = None,
        include_inherited: bool = True,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List project members (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_members():
                members = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if query:
                        params["query"] = query

                    endpoint = (
                        "all"
                        if include_inherited
                        else ""
                    )

                    if endpoint == "all":
                        page_members = (
                            self.gitlab.projects.get(pid)
                            .members_all.list(as_list=False, **params)
                        )
                    else:
                        page_members = (
                            self.gitlab.projects.get(pid)
                            .members.list(as_list=False, **params)
                        )

                    for member in page_members:
                        members.append(member.asdict())

                return members

            members = await _run_async(_list_members)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("member", members, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing project members: {str(e)}")
