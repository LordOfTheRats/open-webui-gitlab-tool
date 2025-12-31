"""Ollama LLM client integration."""

import json
from typing import Optional

import httpx

from gitlab_tool.config import Settings


class OllamaClient:
    """Client for Ollama LLM API."""

    def __init__(self, settings: Settings):
        """Initialize Ollama client."""
        self.settings = settings
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate completion from Ollama.
        
        Args:
            prompt: User prompt to send to LLM
            model: Model name (defaults to configured model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            system: System prompt/instructions
            
        Returns:
            Generated text response
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens
            
        if system is not None:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return data.get("response", "")
                
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s. "
                "Consider increasing OLLAMA_TIMEOUT."
            )
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to call Ollama: {e}")

    async def generate_json(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system: Optional[str] = None,
    ) -> dict:
        """
        Generate JSON response from Ollama.
        
        Adds JSON format instruction and parses response.
        """
        json_system = (system or "") + "\n\nYou must respond with valid JSON only. No other text."
        json_prompt = prompt + "\n\nRespond with valid JSON:"
        
        response = await self.generate(
            prompt=json_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            system=json_system,
        )
        
        # Try to extract JSON from response
        try:
            # First try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON in code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            else:
                # Try to find JSON object in response
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
                    
                raise ValueError(f"Could not extract valid JSON from response: {response[:200]}")

    async def health_check(self) -> bool:
        """Check if Ollama is accessible and model is available."""
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                
                # Check if configured model is available
                model_available = any(
                    self.model in m or m.startswith(self.model.split(":")[0])
                    for m in models
                )
                
                if not model_available:
                    raise RuntimeError(
                        f"Model '{self.model}' not found. Available models: {models}"
                    )
                
                return True
                
        except Exception as e:
            raise RuntimeError(f"Ollama health check failed: {e}")


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        from gitlab_tool.config import get_settings

        settings = get_settings()
        _ollama_client = OllamaClient(settings)
    return _ollama_client


def set_ollama_client(client: OllamaClient) -> None:
    """Set global Ollama client instance."""
    global _ollama_client
    _ollama_client = client
