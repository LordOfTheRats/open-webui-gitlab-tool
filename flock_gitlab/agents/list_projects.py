from typing import Any, Dict, Optional, Literal
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class ListProjectsAgent(BaseAgent):
    """
    An agent that lists projects in GitLab.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_list_projects",
                "description": "Lists GitLab projects based on specified criteria.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search": {
                            "type": "string",
                            "description": "A string to search for in project names and paths."
                        },
                        "membership": {
                            "type": "boolean",
                            "description": "Limit by projects that the current user is a member of.",
                            "default": True
                        },
                        "starred": {
                            "type": "boolean",
                            "description": "Limit by projects starred by the current user.",
                            "default": False
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "internal", "private"],
                            "description": "Limit by project visibility."
                        }
                    },
                    "required": []
                }
            }
        }

    async def execute(
        self,
        search: Optional[str] = None,
        membership: bool = True,
        starred: bool = False,
        visibility: Optional[Literal["public", "internal", "private"]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches projects from the GitLab API.
        """
        params = {
            "search": search,
            "membership": membership,
            "starred": starred,
            "visibility": visibility,
            "simple": True, # Use simple view for performance
        }
        # Filter out None values so they don't get sent as query params
        cleaned_params = {k: v for k, v in params.items() if v is not None}

        try:
            projects = await gitlab_api.request("GET", "/projects", params=cleaned_params)
            return {"result": projects}
        except Exception as e:
            return {"error": str(e)}
