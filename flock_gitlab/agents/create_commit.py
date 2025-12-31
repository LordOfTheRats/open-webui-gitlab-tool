from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api

class CreateCommitAgent(BaseAgent):
    """
    An agent that creates a commit with multiple file actions.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_create_commit",
                "description": "Creates a commit with one or more file actions (create, update, delete).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "The ID or URL-encoded path of the project."
                        },
                        "branch": {
                            "type": "string",
                            "description": "The name of the branch to commit to."
                        },
                        "commit_message": {
                            "type": "string",
                            "description": "The commit message."
                        },
                        "actions": {
                            "type": "array",
                            "description": "A list of file action dictionaries.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {
                                        "type": "string",
                                        "enum": ["create", "update", "delete", "move"],
                                        "description": "The action to perform."
                                    },
                                    "file_path": {
                                        "type": "string",
                                        "description": "The path of the file."
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The new file content. Required for 'create' and 'update'."
                                    },
                                    "previous_path": {
                                        "type": "string",
                                        "description": "The previous path of the file. Required for 'move'."
                                    },
                                    "encoding": {
                                        "type": "string",
                                        "enum": ["text", "base64"],
                                        "default": "text"
                                    }
                                }
                            }
                        }
                    },
                    "required": ["project_id", "branch", "commit_message", "actions"]
                }
            }
        }

    async def execute(
        self,
        project_id: str,
        branch: str,
        commit_message: str,
        actions: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Creates a commit using the GitLab Commits API.
        """
        encoded_project_id = quote_plus(project_id, safe="")
        path = f"/projects/{encoded_project_id}/repository/commits"
        
        payload = {
            "branch": branch,
            "commit_message": commit_message,
            "actions": actions,
        }

        try:
            commit = await gitlab_api.request("POST", path, json=payload)
            return {"result": commit}
        except Exception as e:
            return {"error": str(e)}
