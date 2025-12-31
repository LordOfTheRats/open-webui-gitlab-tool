"""Deepagents GitLab agent harness built around the GitLabToolkit."""

from __future__ import annotations

import argparse
import os
from typing import Optional

from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from tools.gitlab import GitLabToolkit

try:
    # Optional import; only needed when using Ollama.
    from langchain_ollama import ChatOllama  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    ChatOllama = None  # type: ignore


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


SYSTEM_PROMPT = """
You are a GitLab expert assistant who manages issues, merge requests, reviews, pipelines, and repo operations.
Use the GitLabToolkit tools for all GitLab interactions. Default to read-only actions unless explicitly
allowed to write. Ask for the project path or ID when it is ambiguous. Prefer compact responses from tools
unless details are needed to decide. For multi-step work (triage, reviews, planning), create a short todo
plan before executing and update it as you progress. When suggesting or performing repository changes, state
why the change is needed and the branch/commit context. For pipeline triage, pull recent pipelines, drill
into failing jobs, and surface the job trace that explains the failure. Summaries should be concise and end
with clear next steps and any relevant web_url links from tool outputs.
"""


def build_gitlab_toolkit(
    *,
    gitlab_url: Optional[str] = None,
    gitlab_token: Optional[str] = None,
    verify_ssl: Optional[bool] = None,
    compact_results_default: Optional[bool] = None,
    allow_repo_writes: Optional[bool] = None,
) -> GitLabToolkit:
    """Create a configured GitLabToolkit instance."""

    url = gitlab_url or os.getenv("GITLAB_URL", "https://gitlab.example.com")
    pat = gitlab_token or os.getenv("GITLAB_TOKEN")
    if not pat:
        raise ValueError("Set GITLAB_TOKEN to a GitLab PAT with api scope.")

    return GitLabToolkit(
        gitlab_url=url,
        token=pat,
        verify_ssl=bool(_env_flag("GITLAB_VERIFY_SSL", True) if verify_ssl is None else verify_ssl),
        compact_results_default=bool(
            _env_flag("GITLAB_COMPACT_RESULTS", True)
            if compact_results_default is None
            else compact_results_default
        ),
        allow_repo_writes=bool(
            _env_flag("GITLAB_ALLOW_WRITES", False)
            if allow_repo_writes is None
            else allow_repo_writes
        ),
    )


def create_gitlab_agent(
    *,
    model_name: Optional[str] = None,
    ollama_base_url: Optional[str] = None,
    gitlab_url: Optional[str] = None,
    gitlab_token: Optional[str] = None,
    verify_ssl: Optional[bool] = None,
    compact_results_default: Optional[bool] = None,
    allow_repo_writes: Optional[bool] = None,
):
    """Create a Deepagents GitLab agent ready for invocations."""

    toolkit = build_gitlab_toolkit(
        gitlab_url=gitlab_url,
        gitlab_token=gitlab_token,
        verify_ssl=verify_ssl,
        compact_results_default=compact_results_default,
        allow_repo_writes=allow_repo_writes,
    )

    model_id = model_name or os.getenv("GITLAB_AGENT_MODEL", "openai:gpt-4o")
    model = _make_model(model_id, ollama_base_url)

    return create_deep_agent(
        model=model,
        tools=toolkit.get_tools(),
        system_prompt=SYSTEM_PROMPT,
    )


def run_once(message: str, **agent_kwargs):
    """Invoke the GitLab agent on a single user message and return the result."""

    agent = create_gitlab_agent(**agent_kwargs)
    return agent.invoke({"messages": [{"role": "user", "content": message}]})


def _parse_args():
    parser = argparse.ArgumentParser(description="Run the Deepagents GitLab agent for a single message.")
    parser.add_argument("message", help="User request to send to the agent")
    parser.add_argument("--model", dest="model_name", default=None, help="LangChain model id (e.g., openai:gpt-4o)")
    parser.add_argument(
        "--ollama-base-url",
        dest="ollama_base_url",
        default=None,
        help="Base URL for Ollama (e.g., http://localhost:11434). Used when model starts with 'ollama:'.",
    )
    parser.add_argument("--gitlab-url", dest="gitlab_url", default=None, help="GitLab instance URL")
    parser.add_argument("--gitlab-token", dest="gitlab_token", default=None, help="GitLab personal access token")
    parser.add_argument("--allow-writes", action="store_true", help="Allow repository write operations")
    parser.add_argument("--no-verify-ssl", dest="verify_ssl", action="store_false", help="Disable SSL verification")
    return parser.parse_args()


def _make_model(model_name: str, ollama_base_url: Optional[str]):
    """Return a LangChain chat model, supporting Ollama via the `ollama:` prefix."""

    if model_name.startswith("ollama:"):
        if ChatOllama is None:
            raise ImportError(
                "Install langchain-ollama to use Ollama models (pip install langchain-ollama)."
            )

        ollama_model = model_name.split("ollama:", 1)[1] or "llama3"
        base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=ollama_model, base_url=base_url)

    return init_chat_model(model_name)


if __name__ == "__main__":
    args = _parse_args()
    result = run_once(
        args.message,
        model_name=args.model_name,
        ollama_base_url=args.ollama_base_url,
        gitlab_url=args.gitlab_url,
        gitlab_token=args.gitlab_token,
        verify_ssl=args.verify_ssl,
        allow_repo_writes=args.allow_writes,
    )
    print(result)
