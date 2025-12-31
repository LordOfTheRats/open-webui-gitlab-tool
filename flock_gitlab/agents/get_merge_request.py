from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class GetMergeRequestAgent(BaseAgent):
    """
    An agent that fetches a single merge request for a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_get_merge_request",
                "description": "Fetches a single merge request for a GitLab project.",
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
        Fetches a single merge request from the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/merge_requests/{mr_iid}"
        
        try:
            mr = await gitlab_api.request("GET", path)
            return {"result": mr}
        except Exception as e:
            return {"error": str(e)}
