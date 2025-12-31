"""Configuration management using Pydantic settings."""

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # GitLab Configuration
    gitlab_url: HttpUrl = Field(
        default="https://gitlab.example.com",
        description="GitLab instance URL",
    )
    gitlab_token: str = Field(
        default="",
        description="GitLab private access token",
    )

    # Ollama Configuration
    ollama_url: HttpUrl = Field(
        default="http://localhost:11434",
        description="Ollama API URL",
    )
    ollama_model: str = Field(
        default="llama3.2",
        description="Default Ollama model to use",
    )
    ollama_max_concurrent: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Maximum concurrent Ollama requests",
    )
    ollama_timeout: int = Field(
        default=300,
        ge=30,
        description="Ollama request timeout in seconds",
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    log_level: str = Field(default="INFO", description="Logging level")

    # Agent Configuration
    agent_timeout: int = Field(
        default=600,
        ge=60,
        description="Agent execution timeout in seconds",
    )
    max_agent_iterations: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum iterations for agent execution",
    )

    # Human Approval Configuration
    require_approval_for_writes: bool = Field(
        default=True,
        description="Require human approval for write operations",
    )
    require_approval_for_pipeline_actions: bool = Field(
        default=True,
        description="Require human approval for pipeline actions",
    )
    approval_timeout: int = Field(
        default=300,
        ge=30,
        description="Human approval timeout in seconds",
    )

    def validate_gitlab_config(self) -> None:
        """Validate GitLab configuration is complete."""
        if not self.gitlab_token:
            raise ValueError("GITLAB_TOKEN is required")


settings = Settings()
