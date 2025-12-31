from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
import base64

class GetFileAgent(BaseAgent):
    """
    An agent that gets a file from a repository.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_get_file",
                "description": "Gets a file from a repository.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file in the repository."
                        },
                        "ref": {
                            "type": "string",
                            "description": "The name of a branch, tag, or commit.",
                            "default": "main"
                        }
                    },
                    "required": ["project_id", "file_path"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        file_path: str,
        ref: str = "main",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fetches a file from the GitLab API. The content is base64 decoded.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        encoded_file_path = quote_plus(file_path, safe="")
        path = f"/projects/{encoded_project_id}/repository/files/{encoded_file_path}"
        
        params = {"ref": ref}

        try:
            file_data = await gitlab_api.request("GET", path, params=params)
            # Decode the content from base64
            if file_data.get("encoding") == "base64":
                file_data["content"] = base64.b64decode(file_data["content"]).decode("utf-8")
            return {"result": file_data}
        except Exception as e:
            return {"error": str(e)}
