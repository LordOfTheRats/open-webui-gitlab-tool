"""Repository operations agent."""

from typing import Any

from gitlab_tool.agents.base import BaseGitLabAgent
from gitlab_tool.artifacts.requests import GetFileRequest


class RepositoryOperationsAgent(BaseGitLabAgent[GetFileRequest, dict[str, Any]]):
    """Agent that handles repository file operations."""

    def __init__(self, *args, **kwargs):
        """Initialize repository operations agent."""
        super().__init__(name="repository_operations", *args, **kwargs)

    async def process(self, request: GetFileRequest) -> dict[str, Any]:
        """Process repository file request."""
        # For file operations, we don't need LLM - just fetch from GitLab
        try:
            content = await self.gitlab_client.get_raw_file(
                request.project,
                request.file_path,
                request.ref,
            )
            
            return {
                "project": request.project,
                "file_path": request.file_path,
                "ref": request.ref,
                "content": content,
                "size": len(content),
            }
        except Exception as e:
            return {
                "project": request.project,
                "file_path": request.file_path,
                "ref": request.ref,
                "error": str(e),
            }
