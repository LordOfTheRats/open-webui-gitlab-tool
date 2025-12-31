from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
from flock_gitlab.utils.ollama_api import ollama_api

class SummarizeIssueAgent(BaseAgent):
    """
    An agent that summarizes a GitLab issue using an LLM.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_summarize_issue",
                "description": "Summarizes a GitLab issue using an LLM.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "issue_iid": {
                            "type": "integer",
                            "description": "The internal ID (IID) of the issue."
                        }
                    },
                    "required": ["project_id", "issue_iid"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        issue_iid: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches an issue and generates a summary.
        """
        try:
            # 1. Fetch the issue
            encoded_project_id = quote_plus(project_id, safe="")
            path = f"/projects/{encoded_project_id}/issues/{issue_iid}"
            issue = await gitlab_api.request("GET", path)

            # 2. Create a prompt for the LLM
            prompt = f"""Please summarize the following GitLab issue.
            Focus on the main problem, the proposed solution, and the current status.

            Title: {issue.get('title')}
            Description: {issue.get('description')}
            State: {issue.get('state')}
            Labels: {issue.get('labels')}
            Author: {issue.get('author', {}).get('name')}
            
            Provide a concise summary.
            """

            # 3. Generate the summary with Ollama
            summary_response = await ollama_api.generate(prompt)
            
            return {"result": {"summary": summary_response.get("response")}}

        except Exception as e:
            return {"error": str(e)}
