"""Deepagents GitLab agent harness built around the GitLabToolkit."""

from __future__ import annotations

import argparse
import os
from typing import Any, Dict, List, Optional

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
You are the manager and primary point of contact for GitLab work. Own the conversation, gather missing
project context, and delegate to the right specialists when execution is required. Default to read-only
actions unless writes are explicitly allowed. Prefer compact tool responses unless details are needed to
decide. For multi-step work (triage, reviews, planning), create a short todo plan before executing and
update it as you progress. When suggesting or performing repository changes, state why the change is needed
and the branch/commit context. For pipeline triage, pull recent pipelines, drill into failing jobs, and
surface the job trace that explains the failure. Summaries should be concise and end with clear next steps
and any relevant web_url links from tool outputs.
"""

PLANNER_PROMPT = """
You are the planner/dispatcher for GitLab requests. Clarify the goal, scope, and target project, then create
a short, ordered plan. Delegate execution to the appropriate specialist subagent when action is needed.
"""

ISSUES_MRS_PROMPT = """
You handle issues and merge requests: triage, create/update, comment, and merge when safe. Surface risks,
owners, labels, and timelines. Keep responses concise and action-oriented.
"""

PIPELINES_PROMPT = """
You triage CI/CD pipelines. Find the most recent relevant pipeline, identify failing jobs, retrieve the job
trace that explains the failure, and propose the next remediation steps.
"""

REPO_WIKI_PROMPT = """
You perform repository and wiki operations. Read files, diffs, and wikis to answer questions. Only write or
merge when explicitly allowed. Always mention the branch and path when proposing or making changes.
"""

SUMMARY_PROMPT = """
You summarize findings and decisions. Produce crisp summaries with next steps and link to any relevant
GitLab web URLs present in the tool outputs.
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
    subagent_models: Optional[Dict[str, Any]] = None,
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

    tools = toolkit.get_tools()
    subagents = _build_subagents(
        tools,
        base_model=model,
        base_model_name=model_id,
        model_overrides=subagent_models,
        ollama_base_url=ollama_base_url,
    )

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        subagents=subagents,
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


def _make_model(model_name: str, ollama_base_url: Optional[str], **model_kwargs: Any):
    """Return a LangChain chat model, supporting Ollama via the `ollama:` prefix."""

    if model_name.startswith("ollama:"):
        if ChatOllama is None:
            raise ImportError(
                "Install langchain-ollama to use Ollama models (pip install langchain-ollama)."
            )

        ollama_model = model_name.split("ollama:", 1)[1] or "llama3"
        base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=ollama_model, base_url=base_url, **model_kwargs)

    return init_chat_model(model_name, **model_kwargs)


def _resolve_model_for_subagent(
    *,
    base_model_name: str,
    base_model: Any,
    ollama_base_url: Optional[str],
    override: Optional[Any],
) -> Any:
    """Resolve a model for a subagent, allowing overrides per role."""

    if override is None:
        return base_model

    if isinstance(override, str):
        return _make_model(override, ollama_base_url)

    if isinstance(override, dict):
        override_name = override.get("model") or override.get("model_name") or base_model_name
        model_opts = {k: v for k, v in override.items() if k not in {"model", "model_name"}}
        return _make_model(override_name, ollama_base_url, **model_opts)

    return base_model


def _tool_picker(tools: List[Any]):
    by_name = {getattr(t, "name", ""): t for t in tools}

    def pick(names: List[str]) -> List[Any]:
        return [by_name[n] for n in names if n in by_name]

    return pick


def _build_subagents(
    tools: List[Any],
    *,
    base_model: Any,
    base_model_name: str,
    model_overrides: Optional[Dict[str, Any]],
    ollama_base_url: Optional[str],
) -> List[Dict[str, Any]]:
    """Define specialist subagents that the coordinator can delegate to."""

    model_overrides = model_overrides or {}
    pick = _tool_picker(tools)

    model_for = lambda key: _resolve_model_for_subagent(
        base_model_name=base_model_name,
        base_model=base_model,
        ollama_base_url=ollama_base_url,
        override=model_overrides.get(key),
    )

    planner_tools = pick(
        [
            "gitlab_list_projects",
            "gitlab_get_project",
            "gitlab_list_issues",
            "gitlab_list_merge_requests",
            "gitlab_list_pipelines",
        ]
    )

    issues_mrs_tools = pick(
        [
            "gitlab_list_projects",
            "gitlab_get_project",
            "gitlab_list_issues",
            "gitlab_get_issue",
            "gitlab_create_issue",
            "gitlab_update_issue",
            "gitlab_close_issue",
            "gitlab_add_issue_note",
            "gitlab_list_issue_notes",
            "gitlab_list_merge_requests",
            "gitlab_get_merge_request",
            "gitlab_create_merge_request",
            "gitlab_approve_merge_request",
            "gitlab_merge_merge_request",
            "gitlab_add_merge_request_note",
            "gitlab_list_merge_request_notes",
            "gitlab_search_users",
            "gitlab_list_labels",
            "gitlab_list_milestones",
            "gitlab_list_project_members",
        ]
    )

    pipelines_tools = pick(
        [
            "gitlab_list_projects",
            "gitlab_get_project",
            "gitlab_list_pipelines",
            "gitlab_get_pipeline",
            "gitlab_list_pipeline_jobs",
            "gitlab_get_job_trace",
            "gitlab_run_pipeline",
            "gitlab_retry_job",
            "gitlab_cancel_job",
        ]
    )

    repo_wiki_tools = pick(
        [
            "gitlab_list_projects",
            "gitlab_get_project",
            "gitlab_list_repository_tree",
            "gitlab_get_file",
            "gitlab_get_raw_file",
            "gitlab_compare_refs",
            "gitlab_create_or_update_file",
            "gitlab_delete_file",
            "gitlab_move_file",
            "gitlab_chmod_file",
            "gitlab_list_wiki_pages",
            "gitlab_get_wiki_page",
            "gitlab_create_wiki_page",
            "gitlab_update_wiki_page",
            "gitlab_delete_wiki_page",
        ]
    )

    return [
        {
            "name": "planner",
            "description": "Plans tasks and dispatches work to specialists.",
            "system_prompt": PLANNER_PROMPT,
            "tools": planner_tools,
            "model": model_for("planner"),
        },
        {
            "name": "issues-and-mrs",
            "description": "Handles issues and merge requests: triage, updates, comments, and merges when safe.",
            "system_prompt": ISSUES_MRS_PROMPT,
            "tools": issues_mrs_tools,
            "model": model_for("issues_and_mrs"),
        },
        {
            "name": "pipelines",
            "description": "Triage CI/CD pipelines and jobs, find failing traces, and suggest fixes.",
            "system_prompt": PIPELINES_PROMPT,
            "tools": pipelines_tools,
            "model": model_for("pipelines"),
        },
        {
            "name": "repo-and-wiki",
            "description": "Reads and, when allowed, edits repository files and wiki pages with proper branch context.",
            "system_prompt": REPO_WIKI_PROMPT,
            "tools": repo_wiki_tools,
            "model": model_for("repo_and_wiki"),
        },
        {
            "name": "summarizer",
            "description": "Produces concise summaries and next steps using gathered evidence.",
            "system_prompt": SUMMARY_PROMPT,
            "tools": [],
            "model": model_for("summarizer"),
        },
    ]


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
