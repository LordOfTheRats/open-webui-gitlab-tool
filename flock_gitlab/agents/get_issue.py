from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class GetIssueAgent(BaseAgent):
    """
    An agent that fetches a single issue for a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_get_issue",
                "description": "Fetches a single issue for a GitLab project.",
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
        Fetches a single issue from the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/issues/{issue_iid}"
        
        try:
            issue = await gitlab_api.request("GET", path)
            return {"result": issue}
        except Exception as e:
            return {"error": str(e)}
