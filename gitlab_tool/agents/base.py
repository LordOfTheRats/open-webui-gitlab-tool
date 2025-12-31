"""Base agent infrastructure for GitLab tool."""

from typing import Generic, TypeVar

from flock import Agent as FlockAgent
from flock.core.artifacts import Artifact

from gitlab_tool.client import GitLabClient
from gitlab_tool.config import Settings
from gitlab_tool.utils.concurrency import get_limiter

InputT = TypeVar("InputT", bound=Artifact)
OutputT = TypeVar("OutputT", bound=Artifact)


class BaseGitLabAgent(Generic[InputT, OutputT]):
    """Base class for GitLab agents using flock-core."""

    def __init__(
        self,
        name: str,
        settings: Settings,
        gitlab_client: GitLabClient,
        model: str = None,
    ):
        """Initialize base agent."""
        self.name = name
        self.settings = settings
        self.gitlab_client = gitlab_client
        self.model = model or settings.ollama_model
        self.limiter = get_limiter()

    async def process(self, input_artifact: InputT) -> OutputT:
        """
        Process input artifact and return output artifact.
        
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement process()")

    async def invoke(self, input_artifact: InputT) -> OutputT:
        """
        Invoke agent with concurrency control.
        
        Wraps process() with semaphore to limit concurrent LLM requests.
        """
        async with self.limiter:
            return await self.process(input_artifact)

    def create_prompt(self, context: dict) -> str:
        """
        Create LLM prompt from context.
        
        Should be implemented by subclasses for agent-specific prompts.
        """
        raise NotImplementedError("Subclasses should implement create_prompt()")

    async def call_llm(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Call Ollama LLM with prompt.
        
        This is a placeholder - will be implemented with actual Ollama client.
        """
        # TODO: Implement actual Ollama API call
        # For now, return a placeholder
        return f"LLM response for: {prompt[:100]}..."
