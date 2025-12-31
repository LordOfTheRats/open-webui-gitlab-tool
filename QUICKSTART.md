# Quick Start Guide

This guide will help you get the GitLab Multi-Agent Tool running in minutes.

## Prerequisites

- Python 3.11 or higher
- GitLab instance (self-hosted or GitLab.com)
- Ollama running locally or remotely
- GitLab Personal Access Token with `api` scope

## Installation Methods

### Method 1: Using Docker Compose (Recommended)

This method includes Ollama in the stack.

```bash
# Clone the repository
git clone https://github.com/LordOfTheRats/open-webui-gitlab-tool.git
cd open-webui-gitlab-tool

# Create .env file
cp .env.example .env

# Edit .env and set your GitLab token
nano .env

# Start services
docker-compose up -d

# Pull Ollama model (first time only)
docker-compose exec ollama ollama pull llama3.2:latest

# Check logs
docker-compose logs -f gitlab-tool
```

The server will be available at `http://localhost:8000`.

### Method 2: Using Python directly

Requires Ollama to be installed separately.

```bash
# Clone the repository
git clone https://github.com/LordOfTheRats/open-webui-gitlab-tool.git
cd open-webui-gitlab-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create .env file
cp .env.example .env

# Edit .env and configure settings
nano .env

# Run server
uvicorn gitlab_tool.main:app --host 0.0.0.0 --port 8000
```

### Method 3: Using Docker (standalone)

Requires Ollama to be running separately.

```bash
# Build image
docker build -t gitlab-tool .

# Run container
docker run -d \
  -p 8000:8000 \
  -e GITLAB_URL=https://gitlab.example.com \
  -e GITLAB_TOKEN=your-token \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name gitlab-tool \
  gitlab-tool
```

## Configuration

Edit the `.env` file to configure the tool:

```env
# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Server Configuration
MAX_CONCURRENT_REQUESTS=2
```

### Getting a GitLab Token

1. Go to your GitLab instance
2. Navigate to: Profile → Preferences → Access Tokens
3. Create a new token with:
   - Name: "Open WebUI Tool"
   - Scopes: `api`
   - Expiration: Choose based on your needs
4. Copy the token and add it to `.env`

### Installing Ollama Models

If using Ollama, you need to pull a model:

```bash
# Using docker-compose
docker-compose exec ollama ollama pull llama3.2:latest

# Using standalone Ollama
ollama pull llama3.2:latest
```

Recommended models:
- `llama3.2:latest` - Fast, good quality (3B parameters)
- `llama3.1:8b` - Better quality (8B parameters)
- `codellama:13b` - Best for code review (13B parameters)

## Verifying Installation

### 1. Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "gitlab_url": "https://gitlab.example.com",
  "ollama_url": "http://localhost:11434",
  "ollama_status": "healthy",
  "concurrency": {
    "max": 2,
    "available": 2
  }
}
```

### 2. View API Documentation

Open in browser: `http://localhost:8000/docs`

This shows all available endpoints with interactive testing.

### 3. Test an Agent

List projects:
```bash
curl -X POST http://localhost:8000/projects/list \
  -H "Content-Type: application/json" \
  -d '{
    "search": "",
    "membership": true,
    "page": 1,
    "per_page": 5
  }'
```

Summarize an issue:
```bash
curl -X POST http://localhost:8000/issues/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "project": "group/project",
    "issue_iid": 1,
    "include_comments": true
  }'
```

## Connecting to Open WebUI

1. Open Open WebUI settings
2. Go to "Admin Panel" → "Tools"
3. Click "Add OpenAPI Server"
4. Enter URL: `http://localhost:8000`
5. Click "Save"

The tool will appear in Open WebUI with all available operations.

## Common Operations

### Summarize an Issue
```
Ask the LLM: "Summarize issue #42 in mygroup/myproject"
```

### Review a Merge Request
```
Ask the LLM: "Review merge request !15 in mygroup/myproject"
```

### Triage a Failed Pipeline
```
Ask the LLM: "Why did pipeline 123 fail in mygroup/myproject?"
```

### Get Repository File
```
Ask the LLM: "Show me the README.md file from mygroup/myproject"
```

## Troubleshooting

### GitLab Connection Issues

**Problem:** "GitLab API error 401"
- Check your `GITLAB_TOKEN` is correct
- Verify token has `api` scope
- Ensure token hasn't expired

**Problem:** "GitLab API error 404"
- Verify project path is correct
- Check you have access to the project
- Try using project ID instead of path

### Ollama Connection Issues

**Problem:** "Ollama health check failed"
- Ensure Ollama is running: `ollama list`
- Check Ollama URL is correct
- Verify model is pulled: `ollama pull llama3.2`

**Problem:** "Ollama request timed out"
- Increase `OLLAMA_TIMEOUT` in `.env`
- Try a smaller model
- Check system resources

### Performance Issues

**Problem:** Requests are slow
- Reduce `MAX_CONCURRENT_REQUESTS` to 1
- Use a smaller Ollama model
- Increase timeout values

**Problem:** Out of memory
- Use a smaller model (e.g., `llama3.2:latest` instead of `codellama:13b`)
- Reduce concurrent requests
- Add more RAM or swap

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black gitlab_tool/
```

### Type Checking
```bash
mypy gitlab_tool/
```

## Next Steps

- Read the [full README](README.md) for architecture details
- Check [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) for agent design
- Review [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) for customization

## Getting Help

- Check logs: `docker-compose logs -f gitlab-tool`
- Enable debug logging: Set `FLOCK_LOG_LEVEL=DEBUG`
- Review FastAPI docs: `http://localhost:8000/docs`
- Open an issue on GitHub

## Security Notes

- Never commit `.env` file with real tokens
- Use HTTPS for GitLab in production
- Consider firewall rules for port 8000
- Enable `REQUIRE_APPROVAL_FOR_WRITES=true` for safety
