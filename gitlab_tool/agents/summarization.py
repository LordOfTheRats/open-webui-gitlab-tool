"""Issue summarization agent."""

from gitlab_tool.agents.base import BaseGitLabAgent
from gitlab_tool.artifacts.gitlab import Issue, IssueSummary
from gitlab_tool.artifacts.requests import SummarizeIssueRequest


class IssueSummarizationAgent(BaseGitLabAgent[SummarizeIssueRequest, IssueSummary]):
    """Agent that summarizes GitLab issues."""

    def __init__(self, *args, **kwargs):
        """Initialize issue summarization agent."""
        super().__init__(name="issue_summarization", *args, **kwargs)

    def create_prompt(self, context: dict) -> str:
        """Create prompt for issue summarization."""
        issue = context["issue"]
        comments = context.get("comments", [])

        prompt = f"""Analyze this GitLab issue and provide a concise summary.

**Issue Details:**
Title: {issue.get('title')}
State: {issue.get('state')}
Labels: {', '.join(issue.get('labels', []))}
Author: {issue.get('author', {}).get('name')}
Created: {issue.get('created_at')}
Updated: {issue.get('updated_at')}

**Description:**
{issue.get('description') or 'No description'}
"""

        if comments:
            prompt += f"\n\n**Comments ({len(comments)}):**\n"
            for i, comment in enumerate(comments[:5], 1):  # Limit to first 5 comments
                if not comment.get("system"):  # Skip system notes
                    author = comment.get("author", {}).get("name", "Unknown")
                    body = comment.get("body", "")
                    prompt += f"\n{i}. {author}: {body[:200]}...\n"

        prompt += """

Provide:
1. A 2-3 sentence summary of the issue
2. 3-5 key points or action items
3. Priority assessment (low/medium/high)
4. Complexity assessment (simple/moderate/complex)

Format your response as JSON with keys: summary, key_points (array), priority, complexity
"""
        return prompt

    async def process(self, request: SummarizeIssueRequest) -> IssueSummary:
        """Process issue summarization request."""
        # Fetch issue details
        issue = await self.gitlab_client.get_issue(request.project, request.issue_iid)

        # Optionally fetch comments
        comments = []
        if request.include_comments:
            comments = await self.gitlab_client.list_issue_notes(
                request.project, request.issue_iid, per_page=10
            )

        # Create prompt and call LLM
        prompt = self.create_prompt({"issue": issue, "comments": comments})
        response = await self.call_llm(prompt, temperature=0.3)

        # Parse LLM response (simplified - in production, parse JSON properly)
        # For now, create a basic summary
        return IssueSummary(
            issue_iid=request.issue_iid,
            project=request.project,
            title=issue.get("title", ""),
            summary=f"Issue summary: {response[:200]}",
            key_points=["Point 1", "Point 2", "Point 3"],
            status=issue.get("state", "unknown"),
            priority="medium",
            complexity="moderate",
        )
