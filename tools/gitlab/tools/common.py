"""Common utilities for GitLab LangChain tools."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional, TypeVar
from urllib.parse import quote_plus

import gitlab

T = TypeVar("T")


def _encode_path(value: str) -> str:
    """Encode a path-like string so slashes become %2F (required by GitLab)."""
    return quote_plus(value, safe="").replace("+", "%20")


def _project_id_or_path(project: int | str) -> str:
    """Convert project reference to API format.
    
    GitLab endpoints use /projects/:id where :id can be numeric ID or URL-encoded path.
    """
    if isinstance(project, int):
        return str(project)
    return _encode_path(project)


def _group_id_or_path(group: int | str) -> str:
    """Convert group reference to API format.
    
    GitLab group endpoints use /groups/:id where :id can be numeric ID or URL-encoded full path.
    """
    if isinstance(group, int):
        return str(group)
    return _encode_path(group)


def _user_brief(u: Any) -> Optional[dict[str, Any]]:
    """Extract brief user info."""
    if not isinstance(u, dict):
        return None
    return {
        "id": u.get("id"),
        "username": u.get("username"),
        "name": u.get("name"),
        "web_url": u.get("web_url"),
    }


def _compact_one(kind: str, obj: Any) -> Any:
    """Apply compact transformation to a single object."""
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
        return {
            "slug": obj.get("slug"),
            "title": obj.get("title"),
            "content": obj.get("content"),
            "format": obj.get("format"),
            "encoding": obj.get("encoding"),
        }

    return obj


def _maybe_compact(kind: str, data: Any, compact: Optional[bool]) -> Any:
    """Apply compact transformation to data if compact mode is enabled."""
    if not compact:
        return data
    if isinstance(data, list):
        return [_compact_one(kind, x) for x in data]
    return _compact_one(kind, data)


def _gitlab_error_to_message(error: Exception) -> str:
    """Convert GitLab error to readable message."""
    if isinstance(error, gitlab.exceptions.GitlabGetError):
        return f"GitLab resource not found: {str(error)}"
    elif isinstance(error, gitlab.exceptions.GitlabCreateError):
        return f"GitLab creation failed: {str(error)}"
    elif isinstance(error, gitlab.exceptions.GitlabUpdateError):
        return f"GitLab update failed: {str(error)}"
    elif isinstance(error, gitlab.exceptions.GitlabDeleteError):
        return f"GitLab deletion failed: {str(error)}"
    elif isinstance(error, gitlab.exceptions.GitlabAuthError):
        return f"GitLab authentication failed: {str(error)}"
    elif isinstance(error, gitlab.exceptions.GitlabError):
        return f"GitLab API error: {str(error)}"
    else:
        return f"Error: {str(error)}"


async def _run_async(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a synchronous function asynchronously using ThreadPoolExecutor."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
