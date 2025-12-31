"""Issue summarizer agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class IssueSummarizerAgent(BaseAgent):
    """Agent specialized in summarizing GitLab issues."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize issue summarizer agent."""
        super().__init__(AgentRole.ISSUE_SUMMARIZER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is an issue summarization task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.ANALYSIS
            and "project" in task.input_data
            and ("issue_iid" in task.input_data or "issues" in task.input_data)
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Summarize issue(s) with AI analysis."""
        project = task.input_data["project"]
        
        # Handle single issue
        if "issue_iid" in task.input_data:
            issue = await self.gitlab.get_issue(project, task.input_data["issue_iid"])
            
            prompt = f"""Analyze this GitLab issue and provide a comprehensive summary:

Title: {issue.title}
State: {issue.state}
Labels: {', '.join(issue.labels) if issue.labels else 'None'}
Author: {issue.author.get('name', 'Unknown')}
Created: {issue.created_at}

Description:
{issue.description or 'No description provided'}

Provide:
1. Brief summary (2-3 sentences)
2. Key points and requirements
3. Technical considerations
4. Suggested next steps
"""
            
            summary = await self.generate_response(prompt, temperature=0.5)
            
            return {
                "issue": {
                    "iid": issue.iid,
                    "title": issue.title,
                    "state": issue.state,
                    "web_url": issue.web_url,
                },
                "summary": summary,
            }
        
        # Handle multiple issues
        if "issues" in task.input_data:
            state = task.input_data.get("state")
            labels = task.input_data.get("labels")
            
            issues = await self.gitlab.list_issues(
                project=project,
                state=state,
                labels=labels,
                per_page=20,
            )
            
            issues_text = "\n\n".join([
                f"#{issue.iid}: {issue.title}\n"
                f"State: {issue.state}, Labels: {', '.join(issue.labels) if issue.labels else 'None'}\n"
                f"Created: {issue.created_at}"
                for issue in issues
            ])
            
            prompt = f"""Analyze these GitLab issues and provide insights:

{issues_text}

Provide:
1. Overview of issue states and distribution
2. Common themes and patterns
3. Priority recommendations
4. Areas needing attention
"""
            
            analysis = await self.generate_response(prompt, temperature=0.5)
            
            return {
                "total_issues": len(issues),
                "issues": [
                    {
                        "iid": issue.iid,
                        "title": issue.title,
                        "state": issue.state,
                        "labels": issue.labels,
                        "web_url": issue.web_url,
                    }
                    for issue in issues
                ],
                "analysis": analysis,
            }
        
        raise ValueError("Invalid task data for issue summarization")
