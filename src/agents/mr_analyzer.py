"""Merge request analyzer agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class MRAnalyzerAgent(BaseAgent):
    """Agent specialized in analyzing merge requests."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize MR analyzer agent."""
        super().__init__(AgentRole.MR_ANALYZER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is an MR analysis task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.ANALYSIS
            and "project" in task.input_data
            and ("mr_iid" in task.input_data or "merge_requests" in task.input_data)
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Analyze merge request(s) with AI insights."""
        project = task.input_data["project"]
        
        # Handle single MR
        if "mr_iid" in task.input_data:
            mr = await self.gitlab.get_merge_request(project, task.input_data["mr_iid"])
            
            prompt = f"""Analyze this GitLab merge request:

Title: {mr.title}
State: {mr.state}
Source: {mr.source_branch} → Target: {mr.target_branch}
Author: {mr.author.get('name', 'Unknown')}
Created: {mr.created_at}
{f"Merged: {mr.merged_at}" if mr.merged_at else ""}

Description:
{mr.description or 'No description provided'}

Provide:
1. Purpose and scope of changes
2. Potential impact assessment
3. Code review considerations
4. Merge readiness evaluation
"""
            
            analysis = await self.generate_response(prompt, temperature=0.5)
            
            return {
                "merge_request": {
                    "iid": mr.iid,
                    "title": mr.title,
                    "state": mr.state,
                    "source_branch": mr.source_branch,
                    "target_branch": mr.target_branch,
                    "web_url": mr.web_url,
                },
                "analysis": analysis,
            }
        
        # Handle multiple MRs
        if "merge_requests" in task.input_data:
            state = task.input_data.get("state")
            
            mrs = await self.gitlab.list_merge_requests(
                project=project,
                state=state,
                per_page=20,
            )
            
            mrs_text = "\n\n".join([
                f"!{mr.iid}: {mr.title}\n"
                f"State: {mr.state}\n"
                f"{mr.source_branch} → {mr.target_branch}\n"
                f"Author: {mr.author.get('name', 'Unknown')}\n"
                f"Created: {mr.created_at}"
                for mr in mrs
            ])
            
            prompt = f"""Analyze these GitLab merge requests:

{mrs_text}

Provide:
1. Overview of MR states and activity
2. Bottlenecks or blocked MRs
3. Priority review recommendations
4. Overall development velocity insights
"""
            
            analysis = await self.generate_response(prompt, temperature=0.5)
            
            return {
                "total_merge_requests": len(mrs),
                "merge_requests": [
                    {
                        "iid": mr.iid,
                        "title": mr.title,
                        "state": mr.state,
                        "source_branch": mr.source_branch,
                        "target_branch": mr.target_branch,
                        "web_url": mr.web_url,
                    }
                    for mr in mrs
                ],
                "analysis": analysis,
            }
        
        raise ValueError("Invalid task data for MR analysis")
