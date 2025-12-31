from typing import Any, Dict, Optional
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class CreateMergeRequestAgent(BaseAgent):
    """
    An agent that creates a new merge request in a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_create_merge_request",
                "description": "Creates a new merge request in a GitLab project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "source_branch": {
                            "type": "string",
                            "description": "The source branch for the merge request."
                        },
                        "target_branch": {
                            "type": "string",
                            "description": "The target branch for the merge request."
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the merge request."
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the merge request."
                        },
                        "remove_source_branch": {
                            "type": "boolean",
                            "description": "Flag indicating if the source branch should be removed after merging.",
                            "default": False
                        }
                    },
                    "required": ["project_id", "source_branch", "target_branch", "title"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        remove_source_branch: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Creates a new merge request using the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/merge_requests"
        
        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
            "description": description,
            "remove_source_branch": remove_source_branch,
        }
        cleaned_payload = {k: v for k, v in payload.items() if v is not None}

        try:
            mr = await gitlab_api.request("POST", path, json=cleaned_payload)
            return {"result": mr}
        except Exception as e:
            return {"error": str(e)}
