"""Merge Request tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    AddMergeRequestNoteInput,
    ApproveMergeRequestInput,
    CreateMergeRequestInput,
    GetMergeRequestInput,
    ListMergeRequestNotesInput,
    ListMergeRequestsInput,
    MergeMergeRequestInput,
)
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _project_id_or_path,
    _run_async,
)


class ListMergeRequestsTool(BaseTool):
    """List merge requests in a project."""

    name: str = "gitlab_list_merge_requests"
    description: str = (
        "List merge requests in a project with optional filters by state, branch, and search. "
        "Returns a list of merge requests."
    )
    args_schema: type[BaseModel] = ListMergeRequestsInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        state: Optional[str] = "opened",
        source_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List merge requests (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    state=state,
                    source_branch=source_branch,
                    target_branch=target_branch,
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
        state: Optional[str] = "opened",
        source_branch: Optional[str] = None,
        target_branch: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List merge requests (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_mrs():
                mrs = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if state:
                        params["state"] = state
                    if source_branch:
                        params["source_branch"] = source_branch
                    if target_branch:
                        params["target_branch"] = target_branch
                    if search:
                        params["search"] = search

                    page_mrs = self.gitlab.projects.get(pid).mergerequests.list(
                        as_list=False, **params
                    )
                    for mr in page_mrs:
                        mrs.append(mr.asdict())

                return mrs

            mrs = await _run_async(_list_mrs)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("mr", mrs, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing merge requests: {str(e)}")


class GetMergeRequestTool(BaseTool):
    """Get a single merge request."""

    name: str = "gitlab_get_merge_request"
    description: str = (
        "Get details of a single merge request by its IID. "
        "Returns full merge request information."
    )
    args_schema: type[BaseModel] = GetMergeRequestInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        mr_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get merge request (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, mr_iid=mr_iid, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        mr_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get merge request (async)."""
        try:
            pid = _project_id_or_path(project)

            def _get_mr():
                mr = self.gitlab.projects.get(pid).mergerequests.get(mr_iid)
                return mr.asdict()

            mr_data = await _run_async(_get_mr)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("mr", mr_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting merge request: {str(e)}")


class CreateMergeRequestTool(BaseTool):
    """Create a new merge request."""

    name: str = "gitlab_create_merge_request"
    description: str = (
        "Create a new merge request with source/target branches, title, and description. "
        "Returns the created merge request."
    )
    args_schema: type[BaseModel] = CreateMergeRequestInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        remove_source_branch: bool = False,
        squash: Optional[bool] = None,
        draft: bool = False,
        compact: Optional[bool] = None,
    ) -> str:
        """Create merge request (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    title=title,
                    description=description,
                    remove_source_branch=remove_source_branch,
                    squash=squash,
                    draft=draft,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        remove_source_branch: bool = False,
        squash: Optional[bool] = None,
        draft: bool = False,
        compact: Optional[bool] = None,
    ) -> str:
        """Create merge request (async)."""
        try:
            pid = _project_id_or_path(project)

            def _create_mr():
                data = {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "title": title,
                }
                if description:
                    data["description"] = description
                if remove_source_branch:
                    data["remove_source_branch"] = remove_source_branch
                if squash is not None:
                    data["squash"] = squash
                if draft:
                    data["draft"] = draft

                mr = self.gitlab.projects.get(pid).mergerequests.create(data)
                return mr.asdict()

            mr_data = await _run_async(_create_mr)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("mr", mr_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error creating merge request: {str(e)}")


class ApproveMergeRequestTool(BaseTool):
    """Approve a merge request."""

    name: str = "gitlab_approve_merge_request"
    description: str = (
        "Approve a merge request. Only works if you have permission and the MR is not already approved by you. "
        "Returns the approval status."
    )
    args_schema: type[BaseModel] = ApproveMergeRequestInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        mr_iid: int,
    ) -> str:
        """Approve merge request (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, mr_iid=mr_iid)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        mr_iid: int,
    ) -> str:
        """Approve merge request (async)."""
        try:
            pid = _project_id_or_path(project)

            def _approve():
                mr = self.gitlab.projects.get(pid).mergerequests.get(mr_iid)
                mr.approve()
                return mr.asdict()

            mr_data = await _run_async(_approve)
            return str(mr_data)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error approving merge request: {str(e)}")


class MergeMergeRequestTool(BaseTool):
    """Merge a merge request."""

    name: str = "gitlab_merge_merge_request"
    description: str = (
        "Merge a merge request. Only works if MR is approved and all checks pass. "
        "Returns the merged MR details."
    )
    args_schema: type[BaseModel] = MergeMergeRequestInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        mr_iid: int,
        merge_commit_message: Optional[str] = None,
        squash_commit_message: Optional[str] = None,
        should_remove_source_branch: Optional[bool] = None,
        squash: Optional[bool] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Merge merge request (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    mr_iid=mr_iid,
                    merge_commit_message=merge_commit_message,
                    squash_commit_message=squash_commit_message,
                    should_remove_source_branch=should_remove_source_branch,
                    squash=squash,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        mr_iid: int,
        merge_commit_message: Optional[str] = None,
        squash_commit_message: Optional[str] = None,
        should_remove_source_branch: Optional[bool] = None,
        squash: Optional[bool] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Merge merge request (async)."""
        try:
            pid = _project_id_or_path(project)

            def _merge():
                mr = self.gitlab.projects.get(pid).mergerequests.get(mr_iid)
                opts = {}
                if merge_commit_message:
                    opts["merge_commit_message"] = merge_commit_message
                if squash_commit_message:
                    opts["squash_commit_message"] = squash_commit_message
                if should_remove_source_branch is not None:
                    opts["should_remove_source_branch"] = should_remove_source_branch
                if squash is not None:
                    opts["squash"] = squash
                mr.merge(**opts)
                return mr.asdict()

            mr_data = await _run_async(_merge)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("mr", mr_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error merging merge request: {str(e)}")


class AddMergeRequestNoteTool(BaseTool):
    """Add a comment to a merge request."""

    name: str = "gitlab_add_merge_request_note"
    description: str = (
        "Add a comment/note to a merge request. Returns the created note."
    )
    args_schema: type[BaseModel] = AddMergeRequestNoteInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        mr_iid: int,
        body: str,
    ) -> str:
        """Add MR note (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, mr_iid=mr_iid, body=body)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        mr_iid: int,
        body: str,
    ) -> str:
        """Add MR note (async)."""
        try:
            pid = _project_id_or_path(project)

            def _add_note():
                mr = self.gitlab.projects.get(pid).mergerequests.get(mr_iid)
                note = mr.notes.create({"body": body})
                return note.asdict()

            note_data = await _run_async(_add_note)
            return str(note_data)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error adding merge request note: {str(e)}")


class ListMergeRequestNotesTool(BaseTool):
    """List comments on a merge request."""

    name: str = "gitlab_list_merge_request_notes"
    description: str = "List all comments/notes on a merge request with optional sorting."
    args_schema: type[BaseModel] = ListMergeRequestNotesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        mr_iid: int,
        sort: Optional[str] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List MR notes (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    mr_iid=mr_iid,
                    sort=sort,
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
        mr_iid: int,
        sort: Optional[str] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List MR notes (async)."""
        try:
            pid = _project_id_or_path(project)

            def _list_notes():
                notes = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "sort": sort,
                        "page": page,
                        "per_page": 20,
                    }
                    mr = self.gitlab.projects.get(pid).mergerequests.get(mr_iid)
                    page_notes = mr.notes.list(as_list=False, **params)
                    for note in page_notes:
                        notes.append(note.asdict())

                return notes

            notes = await _run_async(_list_notes)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("note", notes, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing merge request notes: {str(e)}")
