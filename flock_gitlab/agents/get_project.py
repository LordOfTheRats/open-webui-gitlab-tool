from typing import Any, Dict
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
from urllib.parse import quote_plus

class GetProjectAgent(BaseAgent):
    """
    An agent that fetches details for a single GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_get_project",
                "description": "Fetches details for a single GitLab project by its ID or URL-encoded path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project (e.g., 'group/project')."
                        }
                    },
                    "required": ["project_id"]
                }
            }
        }

    async def execute(self, project_id: str, **kwargs) -> Dict[str, Any]:
        """
        Fetches a single project from the GitLab API.
        """
        # The project ID needs to be URL-encoded if it's a path.
        encoded_project_id = quote_plus(project_id, safe="")
        
        try:
            project = await gitlab_api.request("GET", f"/projects/{encoded_project_id}")
            return {"result": project}
        except Exception as e:
            return {"error": str(e)}
