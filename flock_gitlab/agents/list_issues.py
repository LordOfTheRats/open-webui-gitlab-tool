from typing import Any, Dict, Optional, Literal
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class ListIssuesAgent(BaseAgent):
    """
    An agent that lists issues for a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_list_issues",
                "description": "Lists issues for a GitLab project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "state": {
                            "type": "string",
                            "enum": ["opened", "closed", "all"],
                            "description": "Filter issues by state.",
                            "default": "opened"
                        },
                        "labels": {
                            "type": "string",
                            "description": "Comma-separated list of label names to filter by."
                        },
                        "search": {
                            "type": "string",
                            "description": "Search issues against their title and description."
                        }
                    },
                    "required": ["project_id"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        state: Optional[Literal["opened", "closed", "all"]] = "opened",
        labels: Optional[str] = None,
        search: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches issues from the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/issues"
        
        params = {
            "state": state,
            "labels": labels,
            "search": search,
        }
        cleaned_params = {k: v for k, v in params.items() if v is not None}

        try:
            issues = await gitlab_api.request("GET", path, params=cleaned_params)
            return {"result": issues}
        except Exception as e:
            return {"error": str(e)}
