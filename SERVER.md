# GitLab Deepagents Web Server

This directory contains a FastAPI web server that exposes the GitLab Deepagents agent through an HTTP API and htmx-based web UI.

## Prerequisites

1. **GitLab Personal Access Token** - You must have a GitLab instance with a Personal Access Token (PAT) with at least `api` scope
2. **Python 3.9+**
3. **Ollama** (optional, if using `ollama:` model prefix) - running on `http://localhost:11434` by default

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   # Copy the example
   cp .env.example .env
   
   # Edit .env with your GitLab token and settings
   export GITLAB_TOKEN="your-gitlab-personal-access-token"
   export GITLAB_URL="https://gitlab.example.com"  # or your GitLab instance
   ```

   **Required:**
   - `GITLAB_TOKEN` - GitLab Personal Access Token with `api` scope

   **Optional:**
   - `GITLAB_URL` - GitLab instance URL (defaults to `https://gitlab.example.com`)
   - `GITLAB_AGENT_MODEL` - LangChain model ID (defaults to `ollama:gpt-4o`)
   - `OLLAMA_BASE_URL` - Ollama server URL (defaults to `http://localhost:11434`)
   - `GITLAB_ALLOW_WRITES` - Allow repository write operations (defaults to `false`)
   - `GITLAB_VERIFY_SSL` - Verify SSL certificates (defaults to `true`)
   - `GITLAB_COMPACT_RESULTS` - Use compact tool responses (defaults to `true`)
   - `PORT` - Server port (defaults to `8000`)

## Running the Server

### Development Mode

```bash
python -m server.app
```

The server will start at `http://localhost:8000`

### Production Mode

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Web UI
- **GET** `/` - Web interface with form

### REST API
- **GET** `/health` - Health check
- **GET** `/config` - Get default configuration
- **POST** `/chat` - Main endpoint for sending requests

  Form or JSON body:
  ```json
  {
    "message": "What are the latest pipelines?",
    "model": "ollama:gpt-4o",
    "gitlab_url": "https://gitlab.example.com",
    "gitlab_token": "glpat-...",
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "verify_ssl": true,
    "allow_writes": false
  }
  ```

  Response (HTML for htmx, JSON otherwise):
  ```json
  {
    "result": "..."
  }
  ```

### Open WebUI Integration
- **POST** `/gitlab-agent` - Open WebUI tool endpoint

  Input:
  ```json
  {
    "message": "What are the latest pipelines?"
  }
  ```

  Output:
  ```json
  {
    "content": "..."
  }
  ```

## Troubleshooting

### 400 Bad Request: "GITLAB_TOKEN environment variable is required"
Make sure you've set the `GITLAB_TOKEN` environment variable. You can either:
1. Set it globally: `export GITLAB_TOKEN="glpat-..."`
2. Provide it in the request: Include `gitlab_token` in the form/JSON body
3. Create a `.env` file in the project root (see `.env.example`)

### Connection Errors
- If you're getting SSL errors, set `GITLAB_VERIFY_SSL=false` (only for development/testing)
- If your GitLab instance is at a different URL, set `GITLAB_URL=https://your-gitlab-instance.com`

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check the Ollama base URL in your request or `OLLAMA_BASE_URL` environment variable
- If Ollama is on a different machine, set `OLLAMA_BASE_URL=http://ollama-host:11434`

### Model Not Found
When using `ollama:` models:
1. Ensure the model is pulled: `ollama pull gpt-4o`
2. Check Ollama logs: `ollama serve` in another terminal
3. Or use an OpenAI model: `openai:gpt-4o` (requires `OPENAI_API_KEY`)

## Example Usage

### Using curl
```bash
# Form submission
curl -X POST http://localhost:8000/chat \
  -F "message=List all projects" \
  -F "model=ollama:gpt-4o"

# JSON submission
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all projects",
    "model": "ollama:gpt-4o",
    "gitlab_token": "glpat-..."
  }'
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What are the latest pipelines?",
        "model": "ollama:gpt-4o",
        "gitlab_token": "glpat-..."
    }
)

print(response.json())
```

## Testing

Run the test script to verify the server is working:

```bash
python test_server.py
```

This will test:
- Health endpoint
- Config endpoint
- Form submission
- JSON submission

## Architecture

The server is built with:
- **FastAPI** - Modern async web framework
- **Deepagents** - Agent framework with subagent support
- **GitLabToolkit** - 40+ GitLab tools organized into specialist subagents
- **htmx** - Lightweight dynamic HTML replacement
- **Pydantic** - Data validation

### Agent Structure

The coordinator agent manages 5 specialist subagents:
1. **Planner** - Clarifies goals and creates execution plans
2. **Issues & MRs** - Handles issues and merge requests
3. **Pipelines** - Triages CI/CD pipelines
4. **Repository & Wiki** - Manages repository and wiki operations
5. **Summarizer** - Provides concise summaries

Each specialist can be customized with:
- Custom model (e.g., `ollama:llama3` for planner, `ollama:gpt-4o` for others)
- Custom temperature, top_p, top_k parameters

## Configuration Examples

### Use Different Models for Different Specialists
```json
{
  "message": "Triage the failed pipeline",
  "model": "ollama:gpt-4o",
  "subagent_models": {
    "pipelines": {
      "model": "ollama:llama3",
      "temperature": 0.3
    }
  }
}
```

### Disable SSL Verification
```bash
export GITLAB_VERIFY_SSL=false
python -m server.app
```

### Allow Repository Writes
```bash
export GITLAB_ALLOW_WRITES=true
python -m server.app
```

## Performance Notes

- Agent invocation runs in a thread pool to avoid blocking the event loop
- Results are cached via tool responses (configurable with `GITLAB_COMPACT_RESULTS`)
- Large responses may take several seconds depending on GitLab instance size and network latency
