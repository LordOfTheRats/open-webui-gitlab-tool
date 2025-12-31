"""Pipeline reviewer agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class PipelineReviewerAgent(BaseAgent):
    """Agent specialized in CI/CD pipeline analysis."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize pipeline reviewer agent."""
        super().__init__(AgentRole.PIPELINE_REVIEWER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is a pipeline review task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.ANALYSIS
            and "project" in task.input_data
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Analyze CI/CD pipelines."""
        project = task.input_data["project"]
        ref = task.input_data.get("ref")
        
        pipelines = await self.gitlab.list_pipelines(
            project=project,
            ref=ref,
            per_page=20,
        )
        
        if not pipelines:
            return {
                "total_pipelines": 0,
                "analysis": "No pipelines found for the specified criteria.",
            }
        
        # Analyze pipeline status distribution
        status_counts: dict[str, int] = {}
        for pipeline in pipelines:
            status_counts[pipeline.status] = status_counts.get(pipeline.status, 0) + 1
        
        pipelines_text = "\n\n".join([
            f"Pipeline #{pipeline.id}\n"
            f"Status: {pipeline.status}\n"
            f"Ref: {pipeline.ref}\n"
            f"SHA: {pipeline.sha[:8]}\n"
            f"Created: {pipeline.created_at}\n"
            f"Updated: {pipeline.updated_at}"
            for pipeline in pipelines[:10]  # Limit to 10 for analysis
        ])
        
        prompt = f"""Analyze these CI/CD pipeline executions:

Status Distribution:
{', '.join(f'{status}: {count}' for status, count in status_counts.items())}

Recent Pipelines:
{pipelines_text}

Provide:
1. Overall pipeline health assessment
2. Failure patterns and recurring issues
3. Performance trends
4. Recommendations for improvement
5. Action items for failed pipelines
"""
        
        analysis = await self.generate_response(prompt, temperature=0.5)
        
        return {
            "total_pipelines": len(pipelines),
            "status_distribution": status_counts,
            "recent_pipelines": [
                {
                    "id": p.id,
                    "status": p.status,
                    "ref": p.ref,
                    "sha": p.sha[:8],
                    "web_url": p.web_url,
                }
                for p in pipelines[:10]
            ],
            "analysis": analysis,
        }
