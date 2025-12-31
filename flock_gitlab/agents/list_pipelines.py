from typing import Any, Dict, Optional, Literal
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class ListPipelinesAgent(BaseAgent):
    """
    An agent that lists pipelines for a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_list_pipelines",
                "description": "Lists pipelines for a GitLab project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "status": {
                            "type": "string",
                            "enum": ["running", "pending", "success", "failed", "canceled", "skipped"],
                            "description": "Filter pipelines by status."
                        },
                        "ref": {
                            "type": "string",
                            "description": "Filter pipelines by branch or tag name."
                        }
                    },
                    "required": ["project_id"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        status: Optional[str] = None,
        ref: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches pipelines from the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/pipelines"
        
        params = {
            "status": status,
            "ref": ref,
        }
        cleaned_params = {k: v for k, v in params.items() if v is not None}

        try:
            pipelines = await gitlab_api.request("GET", path, params=cleaned_params)
            return {"result": pipelines}
        except Exception as e:
            return {"error": str(e)}
