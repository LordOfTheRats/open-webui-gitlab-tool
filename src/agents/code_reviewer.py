"""Code reviewer agent."""

import logging
from typing import Any

from ..models import AgentRole, OperationType, Task
from .base import BaseAgent

logger = logging.getLogger(__name__)


class CodeReviewerAgent(BaseAgent):
    """Agent specialized in code review."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize code reviewer agent."""
        super().__init__(AgentRole.CODE_REVIEWER, *args, **kwargs)

    async def can_handle(self, task: Task) -> bool:
        """Check if this is a code review task."""
        return (
            task.agent_role == self.role
            and task.operation_type == OperationType.ANALYSIS
            and "project" in task.input_data
            and "file_path" in task.input_data
        )

    async def execute(self, task: Task) -> dict[str, Any]:
        """Perform code review with AI analysis."""
        project = task.input_data["project"]
        file_path = task.input_data["file_path"]
        ref = task.input_data.get("ref", "main")
        
        # Get file content
        content = await self.gitlab.get_file_content(project, file_path, ref)
        
        # Determine file type for context
        file_ext = file_path.split(".")[-1] if "." in file_path else "txt"
        
        prompt = f"""Review this code file and provide detailed feedback:

File: {file_path}
Type: {file_ext}
Branch: {ref}

Code:
```{file_ext}
{content}
```

Provide a comprehensive code review covering:
1. Code quality and style
2. Potential bugs or issues
3. Security considerations
4. Performance implications
5. Best practices and improvements
6. Documentation completeness
"""
        
        review = await self.generate_response(prompt, temperature=0.3)
        
        return {
            "file": {
                "path": file_path,
                "ref": ref,
                "size": len(content),
            },
            "review": review,
        }
