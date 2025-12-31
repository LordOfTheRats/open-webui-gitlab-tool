from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
from flock_gitlab.utils.ollama_api import ollama_api

class CodeReviewAgent(BaseAgent):
    """
    An agent that performs a code review on a GitLab merge request using an LLM.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_code_review",
                "description": "Performs a code review on a GitLab merge request using an LLM.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "mr_iid": {
                            "type": "integer",
                            "description": "The internal ID (IID) of the merge request."
                        }
                    },
                    "required": ["project_id", "mr_iid"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        mr_iid: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches the changes for a merge request and generates a code review.
        """
        try:
            encoded_project_id = quote_plus(project_id, safe="")
            
            # 1. Fetch the merge request changes
            changes_path = f"/projects/{encoded_project_id}/merge_requests/{mr_iid}/changes"
            changes = await gitlab_api.request("GET", changes_path)

            # 2. Create a prompt for the LLM
            prompt = """Please act as a senior software engineer and perform a code review
            on the following changes from a GitLab merge request.
            Look for potential bugs, performance issues, style inconsistencies, and areas for improvement.
            Provide constructive feedback.

            Changes:
            """
            
            for change in changes.get("changes", []):
                prompt += f"\n--- File: {change.get('new_path')} ---\n"
                prompt += f"{change.get('diff')}\n"

            # 3. Generate the review with Ollama
            review_response = await ollama_api.generate(prompt)
            
            return {"result": {"review": review_response.get("response")}}

        except Exception as e:
            return {"error": str(e)}
