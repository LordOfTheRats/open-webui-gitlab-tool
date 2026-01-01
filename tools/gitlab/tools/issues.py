"""Issue tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    AddIssueNoteInput,
    CloseIssueInput,
    CreateIssueInput,
    GetIssueInput,
    ListIssueNotesInput,
    ListIssuesInput,
    UpdateIssueInput,
)
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _run_async,
)


class ListIssuesTool(BaseTool):
    """List issues in a project."""

    name: str = "gitlab_list_issues"
    description: str = (
        "List issues in a project with optional filters by state, labels, assignee, and search terms. "
        "Returns a list of issues."
    )
    args_schema: type[BaseModel] = ListIssuesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        state: Optional[str] = "opened",
        labels: Optional[str] = None,
        assignee_username: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List issues (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    state=state,
                    labels=labels,
                    assignee_username=assignee_username,
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
        labels: Optional[str] = None,
        assignee_username: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List issues (async)."""
        try:
            def _list_issues():
                issues = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                    }
                    if state:
                        params["state"] = state
                    if labels:
                        params["labels"] = labels
                    if assignee_username:
                        params["assignee_username"] = assignee_username
                    if search:
                        params["search"] = search

                    page_issues = self.gitlab.projects.get(
                        project
                    ).issues.list(as_list=False, **params)
                    for issue in page_issues:
                        issues.append(issue.asdict())

                return issues

            issues = await _run_async(_list_issues)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("issue", issues, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing issues: {str(e)}")


class GetIssueTool(BaseTool):
    """Get a single issue."""

    name: str = "gitlab_get_issue"
    description: str = (
        "Get details of a single issue by its IID (internal ID within the project). "
        "Returns full issue information."
    )
    args_schema: type[BaseModel] = GetIssueInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        issue_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get issue (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, issue_iid=issue_iid, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        issue_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Get issue (async)."""
        try:
            def _get_issue():
                issue = self.gitlab.projects.get(project).issues.get(issue_iid)
                return issue.asdict()

            issue_data = await _run_async(_get_issue)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("issue", issue_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting issue: {str(e)}")


class CreateIssueTool(BaseTool):
    """Create a new issue."""

    name: str = "gitlab_create_issue"
    description: str = (
        "Create a new issue in a project with title, description, labels, assignee, and due date. "
        "Returns the created issue."
    )
    args_schema: type[BaseModel] = CreateIssueInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        title: str,
        description: Optional[str] = None,
        labels: Optional[str] = None,
        assignee_id: Optional[int] = None,
        milestone_id: Optional[int] = None,
        due_date: Optional[str] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Create issue (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    title=title,
                    description=description,
                    labels=labels,
                    assignee_id=assignee_id,
                    milestone_id=milestone_id,
                    due_date=due_date,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        title: str,
        description: Optional[str] = None,
        labels: Optional[str] = None,
        assignee_id: Optional[int] = None,
        milestone_id: Optional[int] = None,
        due_date: Optional[str] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Create issue (async)."""
        try:
            def _create_issue():
                data = {"title": title}
                if description:
                    data["description"] = description
                if labels:
                    data["labels"] = labels
                if assignee_id:
                    data["assignee_id"] = assignee_id
                if milestone_id:
                    data["milestone_id"] = milestone_id
                if due_date:
                    data["due_date"] = due_date

                issue = self.gitlab.projects.get(project).issues.create(data)
                return issue.asdict()

            issue_data = await _run_async(_create_issue)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("issue", issue_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error creating issue: {str(e)}")


class UpdateIssueTool(BaseTool):
    """Update an issue."""

    name: str = "gitlab_update_issue"
    description: str = (
        "Update an issue with new title, description, labels, assignee, milestone, or due date. "
        "Returns the updated issue."
    )
    args_schema: type[BaseModel] = UpdateIssueInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        issue_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[int] = None,
        labels: Optional[str] = None,
        add_labels: Optional[str] = None,
        remove_labels: Optional[str] = None,
        due_date: Optional[str] = None,
        milestone_id: Optional[int] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Update issue (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    issue_iid=issue_iid,
                    title=title,
                    description=description,
                    assignee_id=assignee_id,
                    labels=labels,
                    add_labels=add_labels,
                    remove_labels=remove_labels,
                    due_date=due_date,
                    milestone_id=milestone_id,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        issue_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee_id: Optional[int] = None,
        labels: Optional[str] = None,
        add_labels: Optional[str] = None,
        remove_labels: Optional[str] = None,
        due_date: Optional[str] = None,
        milestone_id: Optional[int] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Update issue (async)."""
        try:
            def _update_issue():
                issue = self.gitlab.projects.get(project).issues.get(issue_iid)
                if title is not None:
                    issue.title = title
                if description is not None:
                    issue.description = description
                if assignee_id is not None:
                    issue.assignee_id = assignee_id
                if labels is not None:
                    issue.labels = labels.split(",") if isinstance(labels, str) else labels
                if add_labels:
                    current = issue.labels or []
                    new_labels = [l.strip() for l in add_labels.split(",")]
                    issue.labels = list(set(current + new_labels))
                if remove_labels:
                    current = issue.labels or []
                    remove = set(l.strip() for l in remove_labels.split(","))
                    issue.labels = [l for l in current if l not in remove]
                if due_date is not None:
                    issue.due_date = due_date
                if milestone_id is not None:
                    issue.milestone_id = milestone_id
                issue.save()
                return issue.asdict()

            issue_data = await _run_async(_update_issue)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("issue", issue_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error updating issue: {str(e)}")


class CloseIssueTool(BaseTool):
    """Close an issue."""

    name: str = "gitlab_close_issue"
    description: str = "Close an open issue. Returns the closed issue."
    args_schema: type[BaseModel] = CloseIssueInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        issue_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Close issue (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, issue_iid=issue_iid, compact=compact)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        issue_iid: int,
        compact: Optional[bool] = None,
    ) -> str:
        """Close issue (async)."""
        try:
            def _close_issue():
                issue = self.gitlab.projects.get(project).issues.get(issue_iid)
                issue.state_event = "close"
                issue.save()
                return issue.asdict()

            issue_data = await _run_async(_close_issue)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("issue", issue_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error closing issue: {str(e)}")


class AddIssueNoteTool(BaseTool):
    """Add a comment to an issue."""

    name: str = "gitlab_add_issue_note"
    description: str = "Add a comment/note to an issue. Returns the created note."
    args_schema: type[BaseModel] = AddIssueNoteInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        issue_iid: int,
        body: str,
    ) -> str:
        """Add issue note (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, issue_iid=issue_iid, body=body)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        issue_iid: int,
        body: str,
    ) -> str:
        """Add issue note (async)."""
        try:
            def _add_note():
                issue = self.gitlab.projects.get(project).issues.get(issue_iid)
                note = issue.notes.create({"body": body})
                return note.asdict()

            note_data = await _run_async(_add_note)
            return str(note_data)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error adding issue note: {str(e)}")


class ListIssueNotesTool(BaseTool):
    """List comments on an issue."""

    name: str = "gitlab_list_issue_notes"
    description: str = "List all comments/notes on an issue, with optional sorting."
    args_schema: type[BaseModel] = ListIssueNotesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        issue_iid: int,
        sort: Optional[str] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List issue notes (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    issue_iid=issue_iid,
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
        issue_iid: int,
        sort: Optional[str] = "asc",
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List issue notes (async)."""
        try:
            def _list_notes():
                notes = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "sort": sort,
                        "page": page,
                        "per_page": 20,
                    }
                    issue = self.gitlab.projects.get(project).issues.get(issue_iid)
                    page_notes = issue.notes.list(as_list=False, **params)
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
            raise Exception(f"Error listing issue notes: {str(e)}")
