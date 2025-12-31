"""Repository browser agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class RepoBrowserAgent(BaseAgent):
    """Agent specialized in browsing repository contents."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize repository browser agent."""
        super().__init__(AgentRole.REPO_BROWSER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is a repository browsing task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.READ
            and "project" in task.input_data
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Browse repository and provide insights."""
        project = task.input_data["project"]
        
        # Get project info
        project_info = await self.gitlab.get_project(project)
        
        action = task.input_data.get("action", "overview")
        
        if action == "overview":
            return await self._project_overview(project, project_info)
        elif action == "file":
            return await self._browse_file(task.input_data, project_info)
        else:
            raise ValueError(f"Unknown action: {action}")
    
    async def _project_overview(self, project: str, project_info: Any) -> dict[str, Any]:
        """Provide project overview."""
        # Get README if exists
        try:
            readme_content = await self.gitlab.get_file_content(
                project=project,
                file_path="README.md",
                ref=project_info.default_branch or "main",
            )
            has_readme = True
        except Exception:
            readme_content = ""
            has_readme = False
        
        prompt = f"""Analyze this GitLab project repository:

Project: {project_info.name}
Path: {project_info.path_with_namespace}
Description: {project_info.description or 'No description'}
Default Branch: {project_info.default_branch or 'main'}
Visibility: {project_info.visibility}

README Found: {has_readme}
{f"README Content:{chr(10)}{readme_content[:1000]}" if has_readme else "No README found"}

Provide:
1. Project purpose and structure assessment
2. Documentation quality
3. Suggested areas to explore
4. Quick start guidance for contributors
"""
        
        analysis = await self.generate_response(prompt, temperature=0.5)
        
        return {
            "project": {
                "name": project_info.name,
                "path": project_info.path_with_namespace,
                "web_url": project_info.web_url,
                "default_branch": project_info.default_branch,
            },
            "has_readme": has_readme,
            "analysis": analysis,
        }
    
    async def _browse_file(self, input_data: dict[str, Any], project_info: Any) -> dict[str, Any]:
        """Browse specific file."""
        file_path = input_data["file_path"]
        ref = input_data.get("ref", project_info.default_branch or "main")
        
        content = await self.gitlab.get_file_content(
            project=input_data["project"],
            file_path=file_path,
            ref=ref,
        )
        
        return {
            "file": {
                "path": file_path,
                "ref": ref,
                "size": len(content),
            },
            "content": content,
            "project": {
                "name": project_info.name,
                "web_url": project_info.web_url,
            },
        }
