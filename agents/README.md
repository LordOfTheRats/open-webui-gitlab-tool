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
