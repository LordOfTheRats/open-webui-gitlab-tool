from typing import Any, Dict, Optional
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class CreateIssueAgent(BaseAgent):
    """
    An agent that creates a new issue in a GitLab project.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_create_issue",
                "description": "Creates a new issue in a GitLab project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "title": {
                            "type": "string",
                            "description": "The title of the issue."
                        },
                        "description": {
                            "type": "string",
                            "description": "The description of the issue."
                        },
                        "labels": {
                            "type": "string",
                            "description": "Comma-separated list of label names for the issue."
                        }
                    },
                    "required": ["project_id", "title"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        labels: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Creates a new issue using the GitLab API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/issues"
        
        payload = {
            "title": title,
            "description": description,
            "labels": labels,
        }
        cleaned_payload = {k: v for k, v in payload.items() if v is not None}

        try:
            issue = await gitlab_api.request("POST", path, json=cleaned_payload)
            return {"result": issue}
        except Exception as e:
            return {"error": str(e)}
