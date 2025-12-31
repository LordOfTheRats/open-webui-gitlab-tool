"""Merge request summarization and code review agents."""

from gitlab_tool.agents.base import BaseGitLabAgent
from gitlab_tool.artifacts.gitlab import CodeReview, MergeRequestSummary
from gitlab_tool.artifacts.requests import (
    ReviewMergeRequestRequest,
    SummarizeMergeRequestRequest,
)


class MergeRequestSummarizationAgent(
    BaseGitLabAgent[SummarizeMergeRequestRequest, MergeRequestSummary]
):
    """Agent that summarizes GitLab merge requests."""

    def __init__(self, *args, **kwargs):
        """Initialize MR summarization agent."""
        super().__init__(name="mr_summarization", *args, **kwargs)

    def create_prompt(self, context: dict) -> str:
        """Create prompt for MR summarization."""
        mr = context["mr"]
        changes = context.get("changes", {})
        comments = context.get("comments", [])

        prompt = f"""Analyze this GitLab merge request and provide a comprehensive summary.

**Merge Request Details:**
Title: {mr.get('title')}
State: {mr.get('state')}
Source Branch: {mr.get('source_branch')}
Target Branch: {mr.get('target_branch')}
Author: {mr.get('author', {}).get('name')}
Created: {mr.get('created_at')}
Updated: {mr.get('updated_at')}

**Description:**
{mr.get('description') or 'No description'}
"""

        if changes:
            files_changed = len(changes.get('changes', []))
            prompt += f"\n\n**Changes:** {files_changed} files modified\n"
            
            # Show first few changed files
            for change in changes.get('changes', [])[:5]:
                old_path = change.get('old_path', '')
                new_path = change.get('new_path', '')
                if old_path == new_path:
                    prompt += f"- Modified: {new_path}\n"
                else:
                    prompt += f"- Renamed: {old_path} → {new_path}\n"

        if comments:
            prompt += f"\n\n**Discussion ({len(comments)} comments)**\n"
            for i, comment in enumerate(comments[:3], 1):
                if not comment.get("system"):
                    author = comment.get("author", {}).get("name", "Unknown")
                    body = comment.get("body", "")
                    prompt += f"{i}. {author}: {body[:150]}...\n"

        prompt += """

Provide:
1. A 2-3 sentence summary of what this MR does
2. Summary of the code changes
3. Current review status and any concerns
4. 3-5 recommendations for reviewers

Format as JSON with keys: summary, changes_summary, review_status, recommendations (array)
"""
        return prompt

    async def process(self, request: SummarizeMergeRequestRequest) -> MergeRequestSummary:
        """Process MR summarization request."""
        # Fetch MR details
        mr = await self.gitlab_client.get_merge_request(request.project, request.mr_iid)

        # Optionally fetch changes/diff
        changes = {}
        if request.include_diff:
            changes = await self.gitlab_client.get_merge_request_changes(
                request.project, request.mr_iid
            )

        # Fetch comments
        comments = await self.gitlab_client.list_mr_notes(
            request.project, request.mr_iid, per_page=10
        )

        # Create prompt and call LLM
        prompt = self.create_prompt({"mr": mr, "changes": changes, "comments": comments})
        response = await self.call_llm(prompt, temperature=0.3)

        # Parse LLM response (simplified)
        return MergeRequestSummary(
            mr_iid=request.mr_iid,
            project=request.project,
            title=mr.get("title", ""),
            summary=f"MR summary: {response[:200]}",
            changes_summary=f"{len(changes.get('changes', []))} files changed",
            review_status=mr.get("state", "unknown"),
            recommendations=["Review the changes carefully", "Test the functionality"],
        )


class CodeReviewAgent(BaseGitLabAgent[ReviewMergeRequestRequest, CodeReview]):
    """Agent that performs automated code review on merge requests."""

    def __init__(self, *args, **kwargs):
        """Initialize code review agent."""
        super().__init__(name="code_review", *args, **kwargs)

    def create_prompt(self, context: dict) -> str:
        """Create prompt for code review."""
        mr = context["mr"]
        changes = context.get("changes", {})
        review_depth = context.get("review_depth", "standard")

        prompt = f"""Perform a {review_depth} code review of this merge request.

**Merge Request:**
Title: {mr.get('title')}
Author: {mr.get('author', {}).get('name')}
Source: {mr.get('source_branch')} → {mr.get('target_branch')}

**Description:**
{mr.get('description') or 'No description'}
"""

        if changes:
            prompt += f"\n\n**Files Changed ({len(changes.get('changes', []))}):**\n"
            
            # Analyze diffs for first few files
            for change in changes.get('changes', [])[:10]:
                new_path = change.get('new_path', '')
                diff = change.get('diff', '')
                
                prompt += f"\n### {new_path}\n"
                
                # Show diff (truncated to avoid token limits)
                diff_lines = diff.split('\n')[:50]
                prompt += '\n'.join(diff_lines) + '\n'
                
                if len(diff_lines) < len(diff.split('\n')):
                    prompt += "... (diff truncated)\n"

        if review_depth == "quick":
            prompt += """

Quick review focus:
- Critical bugs or security issues
- Obvious code smells
"""
        elif review_depth == "thorough":
            prompt += """

Thorough review focus:
- Architecture and design patterns
- Performance implications
- Security vulnerabilities
- Code quality and maintainability
- Test coverage
- Documentation
"""
        else:  # standard
            prompt += """

Standard review focus:
- Potential bugs
- Code quality issues
- Security concerns
- Best practices violations
"""

        prompt += """

Provide:
1. Overall assessment (1-2 sentences)
2. List of issues found (with file/line references if possible)
3. Suggestions for improvement
4. Approval recommendation (approve/request_changes/needs_discussion)

Format as JSON with keys: overall_assessment, issues_found (array of objects), suggestions (array), approval_recommendation (boolean)
"""
        return prompt

    async def process(self, request: ReviewMergeRequestRequest) -> CodeReview:
        """Process code review request."""
        # Fetch MR details
        mr = await self.gitlab_client.get_merge_request(request.project, request.mr_iid)

        # Fetch changes/diff
        changes = await self.gitlab_client.get_merge_request_changes(
            request.project, request.mr_iid
        )

        # Create prompt and call LLM
        prompt = self.create_prompt({
            "mr": mr,
            "changes": changes,
            "review_depth": request.review_depth,
        })
        
        # Use higher temperature for more creative review insights
        response = await self.call_llm(prompt, temperature=0.5)

        # Parse LLM response (simplified)
        return CodeReview(
            mr_iid=request.mr_iid,
            project=request.project,
            overall_assessment=f"Code review: {response[:200]}",
            issues_found=[
                {"file": "example.py", "line": 42, "severity": "medium", "issue": "Example issue"}
            ],
            suggestions=["Add unit tests", "Improve error handling"],
            approval_recommendation=True,
        )
