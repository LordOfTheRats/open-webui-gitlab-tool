"""Project planner agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class ProjectPlannerAgent(BaseAgent):
    """Agent specialized in project planning and coordination."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize project planner agent."""
        super().__init__(AgentRole.PROJECT_PLANNER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is a project planning task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.ANALYSIS
            and "project" in task.input_data
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Analyze project and create planning insights."""
        project_ref = task.input_data["project"]
        
        # Get project info
        project = await self.gitlab.get_project(project_ref)
        
        # Get open issues
        open_issues = await self.gitlab.list_issues(
            project=project_ref,
            state="opened",
            per_page=20,
        )
        
        # Get open MRs
        open_mrs = await self.gitlab.list_merge_requests(
            project=project_ref,
            state="opened",
            per_page=20,
        )
        
        # Get recent pipelines
        pipelines = await self.gitlab.list_pipelines(
            project=project_ref,
            per_page=10,
        )
        
        # Collect labels from issues
        all_labels = set()
        for issue in open_issues:
            all_labels.update(issue.labels)
        
        prompt = f"""Analyze this GitLab project and create a comprehensive plan:

Project: {project.name} ({project.path_with_namespace})
Description: {project.description or 'No description'}
Visibility: {project.visibility}
Default Branch: {project.default_branch}

Current State:
- Open Issues: {len(open_issues)}
- Open Merge Requests: {len(open_mrs)}
- Recent Pipelines: {len(pipelines)}
- Active Labels: {', '.join(sorted(all_labels)) if all_labels else 'None'}

Top Issues:
{chr(10).join([f"- #{issue.iid}: {issue.title} [{issue.state}]" for issue in open_issues[:5]])}

Open Merge Requests:
{chr(10).join([f"- !{mr.iid}: {mr.title} [{mr.state}]" for mr in open_mrs[:5]])}

Provide:
1. Project health assessment
2. Current priorities based on issues and MRs
3. Workflow recommendations
4. Resource allocation suggestions
5. Risk areas and bottlenecks
6. Short-term action plan
"""
        
        plan = await self.generate_response(prompt, temperature=0.6)
        
        return {
            "project": {
                "name": project.name,
                "path": project.path_with_namespace,
                "visibility": project.visibility,
                "web_url": project.web_url,
            },
            "statistics": {
                "open_issues": len(open_issues),
                "open_merge_requests": len(open_mrs),
                "recent_pipelines": len(pipelines),
                "active_labels": len(all_labels),
            },
            "plan": plan,
        }
