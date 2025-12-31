"""Configuration management for GitLab tool."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
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
    gitlab_url: str = Field(
        default="https://gitlab.example.com",
        description="GitLab instance URL",
    )
    gitlab_token: str = Field(
        default="",
        description="GitLab Personal Access Token with api scope",
    )
    gitlab_verify_ssl: bool = Field(
        default=True,
        description="Verify SSL certificates for GitLab",
    )
    gitlab_timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    ollama_model: str = Field(
        default="llama3.2:latest",
        description="Default Ollama model to use",
    )
    ollama_timeout: int = Field(
        default=120,
        description="Ollama request timeout in seconds",
    )

    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host to bind to",
    )
    port: int = Field(
        default=8000,
        description="Server port to bind to",
    )
    max_concurrent_requests: int = Field(
        default=2,
        description="Maximum concurrent Ollama requests",
    )

    # Human Approval Configuration
    require_approval_for_writes: bool = Field(
        default=True,
        description="Require human approval for write operations",
    )
    approval_timeout_seconds: int = Field(
        default=300,
        description="Timeout for approval requests in seconds",
    )

    # Flock Configuration
    flock_store_path: Optional[str] = Field(
        default=".flock/history.db",
        description="Path to flock SQLite store",
    )
    flock_log_level: str = Field(
        default="INFO",
        description="Flock logging level",
    )

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.gitlab_token:
            errors.append("GITLAB_TOKEN is required")

        if not self.gitlab_url.startswith(("http://", "https://")):
            errors.append("GITLAB_URL must start with http:// or https://")

        if self.max_concurrent_requests < 1:
            errors.append("MAX_CONCURRENT_REQUESTS must be at least 1")

        if self.approval_timeout_seconds < 10:
            errors.append("APPROVAL_TIMEOUT_SECONDS must be at least 10")

        return errors


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
