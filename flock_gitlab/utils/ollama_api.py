import httpx
import os
from typing import Any, Dict

class OllamaAPI:
    """
    A simple wrapper for the Ollama API.
    """

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")
        
        if not self.base_url:
            raise ValueError("OLLAMA_BASE_URL environment variable not set.")

    async def generate(self, prompt: str, format: str = "") -> Dict[str, Any]:
        """
        Makes an asynchronous request to the Ollama generate endpoint.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if format:
            payload["format"] = format

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Ollama API request failed: {e.response.status_code} - {e.response.text}") from e
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {str(e)}") from e

ollama_api = OllamaAPI()
