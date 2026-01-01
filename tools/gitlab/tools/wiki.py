"""Wiki tools for GitLab LangChain toolkit."""

from __future__ import annotations

import asyncio
from typing import Any, Literal, Optional

import gitlab
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from ..models import (
    CreateWikiPageInput,
    DeleteWikiPageInput,
    GetWikiPageInput,
    ListWikiPagesInput,
    UpdateWikiPageInput,
)
from .common import (
    _gitlab_error_to_message,
    _maybe_compact,
    _run_async,
)


class ListWikiPagesTool(BaseTool):
    """List wiki pages in a project."""

    name: str = "gitlab_list_wiki_pages"
    description: str = (
        "List all wiki pages in a project. Optionally include page content. "
        "Returns a list of wiki pages."
    )
    args_schema: type[BaseModel] = ListWikiPagesInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        with_content: bool = False,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List wiki pages (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    with_content=with_content,
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
        with_content: bool = False,
        offset: int = 0,
        page_count: int = 1,
        compact: Optional[bool] = None,
    ) -> str:
        """List wiki pages (async)."""
        try:
            

            def _list_pages():
                pages = []
                for page_num in range(offset + 1, offset + page_count + 1):
                    params = {
                        "with_content": with_content,
                        "page": page_num,
                        "per_page": 20,
                    }
                    page_list = self.gitlab.projects.get(project).wikis.list(
                        as_list=False, **params
                    )
                    for wiki_page in page_list:
                        pages.append(wiki_page.asdict())

                return pages

            pages = await _run_async(_list_pages)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("wiki", pages, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error listing wiki pages: {str(e)}")


class GetWikiPageTool(BaseTool):
    """Get a single wiki page."""

    name: str = "gitlab_get_wiki_page"
    description: str = (
        "Get details of a single wiki page by its slug/title. "
        "Can retrieve a specific version. Returns page content and metadata."
    )
    args_schema: type[BaseModel] = GetWikiPageInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        slug: str,
        version: Optional[str] = None,
        render_html: bool = False,
        compact: Optional[bool] = None,
    ) -> str:
        """Get wiki page (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    slug=slug,
                    version=version,
                    render_html=render_html,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        slug: str,
        version: Optional[str] = None,
        render_html: bool = False,
        compact: Optional[bool] = None,
    ) -> str:
        """Get wiki page (async)."""
        try:
            

            def _get_page():
                params = {}
                if version:
                    params["version"] = version
                if render_html:
                    params["render_html"] = render_html

                page = self.gitlab.projects.get(project).wikis.get(slug, **params)
                return page.asdict()

            page_data = await _run_async(_get_page)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("wiki", page_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error getting wiki page: {str(e)}")


class CreateWikiPageTool(BaseTool):
    """Create a new wiki page."""

    name: str = "gitlab_create_wiki_page"
    description: str = (
        "Create a new wiki page with title, content, and format. "
        "Returns the created page."
    )
    args_schema: type[BaseModel] = CreateWikiPageInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        title: str,
        content: str,
        format: Literal["markdown", "rdoc", "asciidoc", "org"] = "markdown",
        compact: Optional[bool] = None,
    ) -> str:
        """Create wiki page (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    title=title,
                    content=content,
                    format=format,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        title: str,
        content: str,
        format: Literal["markdown", "rdoc", "asciidoc", "org"] = "markdown",
        compact: Optional[bool] = None,
    ) -> str:
        """Create wiki page (async)."""
        try:
            

            def _create_page():
                data = {
                    "title": title,
                    "content": content,
                }
                if format:
                    data["format"] = format

                page = self.gitlab.projects.get(project).wikis.create(data)
                return page.asdict()

            page_data = await _run_async(_create_page)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("wiki", page_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error creating wiki page: {str(e)}")


class UpdateWikiPageTool(BaseTool):
    """Update an existing wiki page."""

    name: str = "gitlab_update_wiki_page"
    description: str = (
        "Update a wiki page with new title, content, and/or format. "
        "Returns the updated page."
    )
    args_schema: type[BaseModel] = UpdateWikiPageInput

    gitlab: gitlab.Gitlab
    compact_default: bool = True

    def _run(
        self,
        project: int | str,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        format: Optional[Literal["markdown", "rdoc", "asciidoc", "org"]] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Update wiki page (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._arun(
                    project=project,
                    slug=slug,
                    title=title,
                    content=content,
                    format=format,
                    compact=compact,
                )
            )
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        slug: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        format: Optional[Literal["markdown", "rdoc", "asciidoc", "org"]] = None,
        compact: Optional[bool] = None,
    ) -> str:
        """Update wiki page (async)."""
        try:
            

            def _update_page():
                page = self.gitlab.projects.get(project).wikis.get(slug)
                if title is not None:
                    page.title = title
                if content is not None:
                    page.content = content
                if format is not None:
                    page.format = format
                page.save()
                return page.asdict()

            page_data = await _run_async(_update_page)
            use_compact = self.compact_default if compact is None else compact
            result = _maybe_compact("wiki", page_data, use_compact)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error updating wiki page: {str(e)}")


class DeleteWikiPageTool(BaseTool):
    """Delete a wiki page."""

    name: str = "gitlab_delete_wiki_page"
    description: str = "Delete a wiki page by its slug/title."
    args_schema: type[BaseModel] = DeleteWikiPageInput

    gitlab: gitlab.Gitlab

    def _run(
        self,
        project: int | str,
        slug: str,
    ) -> str:
        """Delete wiki page (sync wrapper)."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._arun(project=project, slug=slug))
        finally:
            loop.close()

    async def _arun(
        self,
        project: int | str,
        slug: str,
    ) -> str:
        """Delete wiki page (async)."""
        try:
            

            def _delete_page():
                page = self.gitlab.projects.get(project).wikis.get(slug)
                page.delete()
                return f"Wiki page '{slug}' deleted successfully"

            result = await _run_async(_delete_page)
            return str(result)
        except gitlab.exceptions.GitlabError as e:
            raise Exception(_gitlab_error_to_message(e))
        except Exception as e:
            raise Exception(f"Error deleting wiki page: {str(e)}")
