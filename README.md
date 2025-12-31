# GitLab Multi-Agent Tool for Open WebUI

A reimagined GitLab integration for Open WebUI powered by [flock-core](https://github.com/whiteducksoftware/flock), featuring dynamic agent orchestration for common GitLab operations.

## 🎯 Features

- **Multi-Agent Architecture**: Specialized agents for different GitLab operations
  - 📋 **Project Planning Agent**: Issues and merge request management
  - 📝 **Summarization Agents**: Intelligent summaries of issues and MRs
  - 🔍 **Code Review Agent**: Automated code review assistance
  - 🔧 **Pipeline Triage Agent**: CI/CD pipeline analysis and debugging
  - 📁 **Repository Operations Agent**: File and branch management

- **Human Approval Gates**: Critical operations require explicit approval
- **Self-Hosted Focus**: Optimized for GitLab Community Edition
- **Ollama Integration**: Uses self-hosted LLMs with concurrency control
- **Open WebUI Compatible**: Implements OpenAPI tool server specification

## 🏗️ Architecture

```
┌─────────────────┐
│   Open WebUI    │
└────────┬────────┘
         │ HTTP/OpenAPI
┌────────▼────────┐
│  FastAPI Server │
│  (Tool Endpoints)│
└────────┬────────┘
         │
┌────────▼────────┐
│  Flock-Core     │
│  Orchestrator   │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┬──────────┐
    ▼         ▼         ▼         ▼          ▼
┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Planning│ │Summary│ │Review│ │Pipeline│ │Repository│
│ Agent  │ │Agent  │ │Agent │ │ Agent  │ │  Agent   │
└────────┘ └──────┘ └──────┘ └──────┘ └──────────┘
         │         │         │         │          │
         └─────────┴─────────┴─────────┴──────────┘
                        │
                 ┌──────▼──────┐
                 │ GitLab API  │
                 └─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Self-hosted GitLab CE instance
- Self-hosted Ollama instance
- GitLab Personal Access Token with `api` scope

### Installation

```bash
# Clone repository
git clone https://github.com/LordOfTheRats/open-webui-gitlab-tool.git
cd open-webui-gitlab-tool

# Install dependencies
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

### Configuration

Create a `.env` file:

```env
# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Server Configuration
HOST=0.0.0.0
PORT=8000
MAX_CONCURRENT_REQUESTS=2

# Optional: Human Approval
REQUIRE_APPROVAL_FOR_WRITES=true
APPROVAL_TIMEOUT_SECONDS=300
```

### Running the Server

```bash
# Development mode with auto-reload
uvicorn gitlab_tool.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn gitlab_tool.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Connect to Open WebUI

1. Open Open WebUI settings
2. Navigate to "Tools" → "OpenAPI Servers"
3. Add new server: `http://localhost:8000`
4. The tool will appear automatically with all available operations

## 🔧 Usage

### Example: Issue Summarization

```python
POST /summarize-issue
{
  "project": "mygroup/myproject",
  "issue_iid": 42
}
```

Response:
```json
{
  "summary": "This issue discusses implementing user authentication...",
  "key_points": ["Add OAuth2 support", "Secure password storage"],
  "status": "open",
  "priority": "high"
}
```

### Example: Pipeline Triage

```python
POST /triage-pipeline
{
  "project": "mygroup/myproject",
  "pipeline_id": 123
}
```

Response:
```json
{
  "status": "failed",
  "failed_jobs": ["test", "lint"],
  "analysis": "Tests failed due to missing dependency...",
  "recommendations": ["Install missing package", "Update requirements.txt"]
}
```

## 🔐 Security

- Human approval required for:
  - Creating/updating/deleting files
  - Creating/merging merge requests
  - Running/canceling pipelines
  - Modifying CI/CD configuration

- Sensitive data handling:
  - GitLab tokens stored in environment variables
  - No credentials in logs
  - Rate limiting to prevent abuse

## 🛠️ Development

### Project Structure

```
gitlab_tool/
├── __init__.py
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── agents/              # Flock-core agents
│   ├── __init__.py
│   ├── base.py
│   ├── planning.py
│   ├── summarization.py
│   ├── review.py
│   ├── pipeline.py
│   └── repository.py
├── artifacts/           # Pydantic models
│   ├── __init__.py
│   ├── gitlab.py
│   └── requests.py
├── client/              # GitLab API client
│   ├── __init__.py
│   └── gitlab.py
└── utils/               # Utilities
    ├── __init__.py
    ├── approval.py
    └── concurrency.py
```

### Running Tests

```bash
pytest
pytest --cov=gitlab_tool
```

### Code Quality

```bash
# Format code
black gitlab_tool/

# Lint
ruff check gitlab_tool/

# Type check
mypy gitlab_tool/
```

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 🙏 Acknowledgments

- Built on [flock-core](https://github.com/whiteducksoftware/flock) by White Duck Software
- Integrates with [Open WebUI](https://github.com/open-webui/open-webui)
- Original monolithic tool by René Vögeli
