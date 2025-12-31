from typing import Any, Dict
from urllib.parse import quote_plus
from flock_gitlab.agents.base import BaseAgent
from flock_gitlab.utils.gitlab_api import gitlab_api
from flock_gitlab.utils.ollama_api import ollama_api

class SummarizeMergeRequestAgent(BaseAgent):
    """
    An agent that summarizes a GitLab merge request using an LLM.
    """

    def get_tool_def(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "gitlab_summarize_merge_request",
                "description": "Summarizes a GitLab merge request using an LLM.",
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
        Fetches a merge request and its changes, then generates a summary.
        """
        try:
            encoded_project_id = quote_plus(project_id, safe="")
            
            # 1. Fetch the merge request details
            mr_path = f"/projects/{encoded_project_id}/merge_requests/{mr_iid}"
            mr = await gitlab_api.request("GET", mr_path)

            # 2. Fetch the merge request changes
            changes_path = f"/projects/{encoded_project_id}/merge_requests/{mr_iid}/changes"
            changes = await gitlab_api.request("GET", changes_path)

            # 3. Create a prompt for the LLM
            prompt = f"""Please summarize the following GitLab merge request.
            Focus on the purpose of the changes and provide a high-level overview of the modifications.

            Title: {mr.get('title')}
            Description: {mr.get('description')}
            State: {mr.get('state')}
            Source Branch: {mr.get('source_branch')}
            Target Branch: {mr.get('target_branch')}
            
            Changes:
            """
            
            for change in changes.get("changes", []):
                prompt += f"\n--- File: {change.get('new_path')} ---\n"
                prompt += f"{change.get('diff')}\n"

            # 4. Generate the summary with Ollama
            summary_response = await ollama_api.generate(prompt)
            
            return {"result": {"summary": summary_response.get("response")}}

        except Exception as e:
            return {"error": str(e)}
