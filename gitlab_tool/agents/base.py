"""Base agent infrastructure for GitLab tool."""

from typing import Generic, TypeVar

from gitlab_tool.client import GitLabClient, get_ollama_client
from gitlab_tool.config import Settings
from gitlab_tool.utils.concurrency import get_limiter

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


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
        self.ollama_client = get_ollama_client()

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
        
        Uses the Ollama client to generate completions.
        """
        return await self.ollama_client.generate(
            prompt=prompt,
            model=self.model,
            temperature=temperature,
        )

    async def call_llm_json(self, prompt: str, temperature: float = 0.7) -> dict:
        """
        Call Ollama LLM and parse JSON response.
        
        Ensures the response is valid JSON.
        """
        return await self.ollama_client.generate_json(
            prompt=prompt,
            model=self.model,
            temperature=temperature,
        )
