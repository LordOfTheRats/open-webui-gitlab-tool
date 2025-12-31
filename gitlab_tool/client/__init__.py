"""Client package initialization."""

from gitlab_tool.client.gitlab import GitLabClient
from gitlab_tool.client.ollama import OllamaClient, get_ollama_client

__all__ = ["GitLabClient", "OllamaClient", "get_ollama_client"]
