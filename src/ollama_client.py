"""Ollama LLM client for agent interactions."""

import logging
from typing import Any, Optional

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for Ollama LLM operations."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """Initialize Ollama client."""
        self.base_url = (base_url or str(settings.ollama_url)).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.ollama_timeout

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text completion."""
        data: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        
        if system:
            data["system"] = system
        
        if max_tokens:
            data["options"]["num_predict"] = max_tokens
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=data,
                    timeout=float(self.timeout),
                )
                response.raise_for_status()
                result = response.json()
                
            return result.get("response", "")
            
        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %d seconds", self.timeout)
            raise
        except httpx.HTTPError as e:
            logger.error("Ollama HTTP error: %s", e)
            raise
        except Exception as e:
            logger.error("Ollama error: %s", e)
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat completion with message history."""
        data: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        
        if max_tokens:
            data["options"]["num_predict"] = max_tokens
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=data,
                    timeout=float(self.timeout),
                )
                response.raise_for_status()
                result = response.json()
                
            message = result.get("message", {})
            return message.get("content", "")
            
        except httpx.TimeoutException:
            logger.error("Ollama request timed out after %d seconds", self.timeout)
            raise
        except httpx.HTTPError as e:
            logger.error("Ollama HTTP error: %s", e)
            raise
        except Exception as e:
            logger.error("Ollama error: %s", e)
            raise

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings for text."""
        data = {
            "model": self.model,
            "prompt": text,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json=data,
                    timeout=float(self.timeout),
                )
                response.raise_for_status()
                result = response.json()
                
            return result.get("embedding", [])
            
        except httpx.HTTPError as e:
            logger.error("Ollama embedding error: %s", e)
            raise
