import httpx
import os
from typing import Any, Dict, Optional

class GitLabAPI:
    """
    A simple wrapper for the GitLab API.
    """

    def __init__(self):
        self.base_url = os.getenv("GITLAB_BASE_URL", "").rstrip("/")
        self.token = os.getenv("GITLAB_PRIVATE_TOKEN", "")
        
        if not self.base_url:
            raise ValueError("GITLAB_BASE_URL environment variable not set.")
        if not self.token:
            raise ValueError("GITLAB_PRIVATE_TOKEN environment variable not set.")
            
        self.api_url = f"{self.base_url}/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json"
        }

    async def request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None) -> Any:
        """
        Makes an asynchronous request to the GitLab API.
        """
        async with httpx.AsyncClient(headers=self.headers) as client:
            try:
                response = await client.request(method, f"{self.api_url}{path}", params=params, json=json)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Pass the error details up
                raise Exception(f"GitLab API request failed: {e.response.status_code} - {e.response.text}") from e
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {str(e)}") from e

gitlab_api = GitLabAPI()
