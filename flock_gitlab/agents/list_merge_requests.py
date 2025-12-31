from typing import Any, Dict, Optional, Literal
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class ListMergeRequestsAgent(BaseAgent):
    """
    An agent that lists merge requests for a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_list_merge_requests",
                "description": "Lists merge requests for a GitLab project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "state": {
                            "type": "string",
                            "enum": ["opened", "closed", "locked", "merged", "all"],
                            "description": "Filter merge requests by state.",
                            "default": "opened"
                        },
                        "search": {
                            "type": "string",
                            "description": "Search merge requests against their title and description."
                        }
                    },
                    "required": ["project_id"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        state: Optional[Literal["opened", "closed", "locked", "merged", "all"]] = "opened",
        search: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches merge requests from the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/merge_requests"
        
        params = {
            "state": state,
            "search": search,
        }
        cleaned_params = {k: v for k, v in params.items() if v is not None}

        try:
            mrs = await gitlab_api.request("GET", path, params=cleaned_params)
            return {"result": mrs}
        except Exception as e:
            return {"error": str(e)}
