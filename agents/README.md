# GitLab Deepagents Harness

This directory contains a Deepagents-powered GitLab agent that wraps the LangChain `GitLabToolkit`.

## Setup
- Install dependencies: `pip install -r requirements.txt`
- Set environment variables:
  - `GITLAB_TOKEN` (required): GitLab PAT with `api` scope.
  - `GITLAB_URL` (optional): Defaults to `https://gitlab.example.com`.
  - `GITLAB_VERIFY_SSL` (optional): `true`/`false`, defaults to `true`.
  - `GITLAB_COMPACT_RESULTS` (optional): default `true` to favor compact payloads.
  - `GITLAB_ALLOW_WRITES` (optional): set to enable repository write tools.
  - `GITLAB_AGENT_MODEL` (optional): LangChain model id (e.g., `openai:gpt-4o` or `ollama:llama3`).
  - `OLLAMA_BASE_URL` (optional): Base URL for your Ollama instance, default `http://localhost:11434`.

## Usage
Run a single request:

```bash
python -m agents.gitlab_deepagent "List open merge requests in acme/api targeting main"
```

Specify options explicitly:

```bash
python -m agents.gitlab_deepagent "Triage the latest failed pipeline for acme/api on main" \
  --model openai:gpt-4o \
  --gitlab-url https://gitlab.example.com \
  --token $GITLAB_TOKEN \
  --allow-writes
```

Use a self-hosted Ollama model:

```bash
python -m agents.gitlab_deepagent "List open issues tagged bug in acme/api" \
  --model ollama:llama3 \
  --ollama-base-url http://localhost:11434
```

## FastAPI server + htmx UI
Run the web server:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 for a simple htmx UI. You can override the GitLab token per request (leave blank to use the server env), switch models (OpenAI or `ollama:`), and toggle repository writes. The `/chat` endpoint also accepts JSON payloads:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"List open MRs in acme/api","model":"ollama:llama3","gitlab_token":"<PAT>"}'
```

## Agent behavior
The agent uses Deepagents defaults (todos, filesystem, sub-agents) plus a GitLab-specific system prompt that:
- Prioritizes read-only operations unless writes are explicitly allowed.
- Encourages quick todo planning for multi-step work (triage, reviews, planning).
- Uses GitLabToolkit tools for issues, merge requests, pipelines, wiki, and repo operations.
- Summarizes with concise next steps and relevant `web_url` links from tool outputs.

### Coordinator + specialists
The top-level agent now delegates to specialist sub-agents:
- `planner`: clarifies scope and crafts a short plan.
- `issues-and-mrs`: triages and edits issues/MRs (create/update/merge/comment).
- `pipelines`: triages pipelines and surfaces failing job traces.
- `repo-and-wiki`: reads files/diffs and, when writes are allowed, edits repo/wiki content.
- `summarizer`: produces concise summaries and next steps.

You can override the model (and options like `temperature`) per specialist when calling `create_gitlab_agent` or `run_once` by passing `subagent_models`, a dict keyed by specialist name. Examples:

```python
run_once(
  "Summarize the failing pipeline in acme/api",
  model_name="openai:gpt-4o",
  temperature=0.2,
  subagent_models={
    "pipelines": {"model": "ollama:llama3", "temperature": 0.1},
    "summarizer": "openai:gpt-4o-mini",
  },
)
```
Top-level model options `temperature`, `top_p`, and `top_k` can be provided directly to `run_once` / `create_gitlab_agent` / CLI flags, and subagent overrides can include the same keys in their dictionaries. If no override is provided for a specialist, it reuses the main model.
