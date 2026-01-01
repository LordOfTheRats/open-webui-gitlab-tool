"""Repository tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    ChmodFileInput,
    CompareInput,
    CreateOrUpdateFileInput,
    DeleteFileInput,
    GetFileInput,
    GetRawFileInput,
    ListRepositoryTreeInput,
    MoveFileInput,
)
from .common import (
    _gitlab_error_to_message,
    _run_async,
)


class ListRepositoryTreeTool(BaseTool):
    """List repository tree contents."""

    name: str = "gitlab_list_repository_tree"
    description: str = (
        "List files and directories in a repository at a given path and ref. "
        "Supports recursive listing."
    )
    args_schema: type[BaseModel] = ListRepositoryTreeInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = False,
        offset: int = 0,
        page_count: int = 1,
    ) -> str:
        """List repository tree (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    path=path,
                    ref=ref,
                    recursive=recursive,
                    offset=offset,
                    page_count=page_count,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        path: str = "",
        ref: Optional[str] = None,
        recursive: bool = False,
        offset: int = 0,
        page_count: int = 1,
    ) -> str:
        """List repository tree (async)."""
        try:
            

            def _list_tree():
                items = []
                for page in range(offset + 1, offset + page_count + 1):
                    params = {
                        "page": page,
                        "per_page": 20,
                        "recursive": recursive,
                    }
                    if ref:
                        params["ref"] = ref

                    tree = self.gitlab.projects.get(project).repository_tree(
                        path=path, **params
                    )
                    for item in tree:
                        items.append(item)

                return items

            items = await _run_async(_list_tree)
            return str(items)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing repository tree: {str(e)}")


class GetFileTool(BaseTool):
    """Get file content and metadata."""

    name: str = "gitlab_get_file"
    description: str = (
        "Get file content and metadata from a repository. "
        "Returns file object with content (base64 encoded by GitLab)."
    )
    args_schema: type[BaseModel] = GetFileInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        file_path: str,
        ref: str = "HEAD",
    ) -> str:
        """Get file (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, file_path=file_path, ref=ref)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        file_path: str,
        ref: str = "HEAD",
    ) -> str:
        """Get file (async)."""
        try:
            

            def _get_file():
                f = self.gitlab.projects.get(project).files.get(
                    file_path, ref=ref
                )
                result = {
                    "file_path": f.file_path,
                    "ref": f.ref,
                    "blob_id": f.blob_id,
                    "commit_id": f.commit_id,
                    "encoding": f.encoding,
                }
                # Content is base64 encoded
                if f.content:
                    try:
                        decoded = base64.b64decode(f.content).decode("utf-8")
                        result["content"] = decoded
                    except Exception:
                        result["content"] = f.content
                else:
                    result["content"] = f.content
                return result

            file_data = await _run_async(_get_file)
            return str(file_data)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting file: {str(e)}")


class GetRawFileTool(BaseTool):
    """Get raw file content."""

    name: str = "gitlab_get_raw_file"
    description: str = (
        "Get raw file content from a repository as plain text. "
        "Returns the file content directly (not base64 encoded)."
    )
    args_schema: type[BaseModel] = GetRawFileInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        file_path: str,
        ref: str = "HEAD",
    ) -> str:
        """Get raw file (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(project=project, file_path=file_path, ref=ref)
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        file_path: str,
        ref: str = "HEAD",
    ) -> str:
        """Get raw file (async)."""
        try:
            

            def _get_raw_file():
                content = self.gitlab.projects.get(project).files.raw(
                    file_path, ref=ref
                )
                # Content is already bytes, decode to string
                if isinstance(content, bytes):
                    return content.decode("utf-8")
                return str(content)

            content = await _run_async(_get_raw_file)
            return content
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting raw file: {str(e)}")


class CompareRefsTool(BaseTool):
    """Compare two refs (branches/tags/commits)."""

    name: str = "gitlab_compare_refs"
    description: str = (
        "Compare two refs (branches, tags, or commits) to see diffs. "
        "Returns diff information between the refs."
    )
    args_schema: type[BaseModel] = CompareInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        from_ref: str,
        to_ref: str,
        straight: bool = False,
    ) -> str:
        """Compare refs (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    from_ref=from_ref,
                    to_ref=to_ref,
                    straight=straight,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        from_ref: str,
        to_ref: str,
        straight: bool = False,
    ) -> str:
        """Compare refs (async)."""
        try:
            

            def _compare():
                comparison = self.gitlab.projects.get(project).repository_compare(
                    from_ref, to_ref, straight=straight
                )
                return comparison
            
            result = await _run_async(_compare)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error comparing refs: {str(e)}")


class CreateOrUpdateFileTool(BaseTool):
    """Create or update a file in a repository."""

    name: str = "gitlab_create_or_update_file"
    description: str = (
        "Create a new file or update an existing file in a repository. "
        "Returns the commit information."
    )
    args_schema: type[BaseModel] = CreateOrUpdateFileInput

    gitlab: gitlab.Gitlab
    allow_writes: bool = False

    def _run(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str,
        encoding: str = "text",
        start_branch: Optional[str] = None,
        execute_filemode: Optional[bool] = None,
    ) -> str:
        """Create or update file (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    branch=branch,
                    file_path=file_path,
                    content=content,
                    commit_message=commit_message,
                    encoding=encoding,
                    start_branch=start_branch,
                    execute_filemode=execute_filemode,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str,
        encoding: str = "text",
        start_branch: Optional[str] = None,
        execute_filemode: Optional[bool] = None,
    ) -> str:
        """Create or update file (async)."""
        if not self.allow_writes:
            raise Exception(
                "Repository write operations are disabled. "
                "Enable allow_repo_writes in toolkit configuration."
            )

        try:
            

            def _create_or_update():
                data = {
                    "branch": branch,
                    "content": content,
                    "commit_message": commit_message,
                }
                if encoding:
                    data["encoding"] = encoding
                if start_branch:
                    data["start_branch"] = start_branch
                if execute_filemode is not None:
                    data["execute_filemode"] = execute_filemode

                try:
                    # Try to get existing file first
                    f = self.gitlab.projects.get(project).files.get(file_path, ref=branch)
                    f.content = content
                    f.commit_message = commit_message
                    if encoding:
                        f.encoding = encoding
                    if execute_filemode is not None:
                        f.execute_filemode = execute_filemode
                    f.save(branch=branch)
                    return f.asdict()
                except gitlab.exceptions.GitlabGetError:
                    # File doesn't exist, create it
                    f = self.gitlab.projects.get(project).files.create(
                        file_path, data
                    )
                    return f.asdict()

            result = await _run_async(_create_or_update)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error creating/updating file: {str(e)}")


class DeleteFileTool(BaseTool):
    """Delete a file from a repository."""

    name: str = "gitlab_delete_file"
    description: str = (
        "Delete a file from a repository. Returns commit information."
    )
    args_schema: type[BaseModel] = DeleteFileInput

    gitlab: gitlab.Gitlab
    allow_writes: bool = False

    def _run(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Delete file (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    branch=branch,
                    file_path=file_path,
                    commit_message=commit_message,
                    start_branch=start_branch,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Delete file (async)."""
        if not self.allow_writes:
            raise Exception(
                "Repository write operations are disabled. "
                "Enable allow_repo_writes in toolkit configuration."
            )

        try:
            

            def _delete():
                f = self.gitlab.projects.get(project).files.get(file_path, ref=branch)
                f.delete(branch=branch, commit_message=commit_message)
                return f"File {file_path} deleted from {branch}"

            result = await _run_async(_delete)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")


class MoveFileTool(BaseTool):
    """Move/rename a file in a repository."""

    name: str = "gitlab_move_file"
    description: str = (
        "Move or rename a file in a repository. Returns commit information."
    )
    args_schema: type[BaseModel] = MoveFileInput

    gitlab: gitlab.Gitlab
    allow_writes: bool = False

    def _run(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        previous_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Move file (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    branch=branch,
                    file_path=file_path,
                    previous_path=previous_path,
                    commit_message=commit_message,
                    start_branch=start_branch,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        previous_path: str,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Move file (async)."""
        if not self.allow_writes:
            raise Exception(
                "Repository write operations are disabled. "
                "Enable allow_repo_writes in toolkit configuration."
            )

        try:
            

            def _move():
                f = self.gitlab.projects.get(project).files.get(previous_path, ref=branch)
                f.file_path = file_path
                f.save(branch=branch, commit_message=commit_message)
                return f.asdict()

            result = await _run_async(_move)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error moving file: {str(e)}")


class ChmodFileTool(BaseTool):
    """Change file permissions (executable mode)."""

    name: str = "gitlab_chmod_file"
    description: str = (
        "Change file permissions (make executable or non-executable). "
        "Returns commit information."
    )
    args_schema: type[BaseModel] = ChmodFileInput

    gitlab: gitlab.Gitlab
    allow_writes: bool = False

    def _run(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        execute_filemode: bool,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Change file mode (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    branch=branch,
                    file_path=file_path,
                    execute_filemode=execute_filemode,
                    commit_message=commit_message,
                    start_branch=start_branch,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        branch: str,
        file_path: str,
        execute_filemode: bool,
        commit_message: str,
        start_branch: Optional[str] = None,
    ) -> str:
        """Change file mode (async)."""
        if not self.allow_writes:
            raise Exception(
                "Repository write operations are disabled. "
                "Enable allow_repo_writes in toolkit configuration."
            )

        try:
            

            def _chmod():
                f = self.gitlab.projects.get(project).files.get(file_path, ref=branch)
                f.execute_filemode = execute_filemode
                f.save(branch=branch, commit_message=commit_message)
                return f.asdict()

            result = await _run_async(_chmod)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error changing file mode: {str(e)}")
