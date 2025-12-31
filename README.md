# GitLab Flock Tool

A sophisticated GitLab integration tool using the Flock blackboard pattern with specialized AI agents. This is a complete reimagination of GitLab automation, moving from a monolithic tool to a dynamic multi-agent system.

## ✨ Features

- **🤖 Dynamic Agent Orchestration**: Specialist agents for project planning, code review, pipeline analysis, and more
- **📋 Flock Blackboard Pattern**: Collaborative problem-solving with shared state coordination
- **⚡ FastAPI Server**: Implements Open WebUI tool server specification (OpenAPI-based)
- **✅ Human Approval**: Critical operations require human confirmation for safety
- **🏠 Self-hosted Ready**: Optimized for self-hosted GitLab CE and Ollama instances
- **🔄 Async Execution**: Non-blocking task execution with status tracking
- **📊 Comprehensive Analysis**: AI-powered insights for projects, issues, MRs, code, and pipelines

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (Port 8000)               │
│                  Open WebUI Tool Specification              │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   Orchestrator                              │
│            Task Management & Execution Control              │
└────────┬───────────────────────────────────────────┬────────┘
         │                                           │
┌────────▼───────────────────────────────────────────▼────────┐
│                  Flock Blackboard                           │
│     Shared State • Task Queue • Message Bus • Approvals    │
└─┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬────┬──┘
  │    │    │    │    │    │    │    │    │    │    │    │
  ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼
┌──────────────────────────────────────────────────────────────┐
│                    Specialist Agents                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  🎯 Project Planner    📝 Issue Summarizer                  │
│     • Project analysis    • Issue summarization             │
│     • Planning insights   • Pattern detection               │
│                                                              │
│  🔀 MR Analyzer        👨‍💻 Code Reviewer                     │
│     • MR evaluation       • Code quality review             │
│     • Merge readiness     • Security analysis               │
│                                                              │
│  🔧 Pipeline Reviewer  📁 Repo Browser                       │
│     • CI/CD analysis      • Repository navigation           │
│     • Failure patterns    • File inspection                 │
│                                                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                 External Services                            │
├──────────────────────────────────────────────────────────────┤
│  🦊 GitLab API        🤖 Ollama LLM                         │
│     • Projects           • Text generation                   │
│     • Issues/MRs         • Chat completion                   │
│     • Pipelines          • Embeddings                        │
│     • Repository         • Model: llama3.2                   │
└──────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- GitLab instance (self-hosted CE or GitLab.com)
- GitLab private access token with `api` scope
- Ollama installed with a model (e.g., `llama3.2`)

### Installation

1. **Clone and Install**

```bash
git clone https://github.com/LordOfTheRats/open-webui-gitlab-tool.git
cd open-webui-gitlab-tool
make install
```

2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

Required configuration:
```env
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

3. **Run Server**

```bash
make run
```

Server starts at http://localhost:8000

### Using Docker

```bash
# Copy and configure .env
cp .env.example .env

# Start both tool and Ollama
make docker-run

# View logs
make docker-logs
```

## 📚 Documentation

- **[Quick Start Guide](QUICKSTART.md)** - Get started in 5 minutes
- **[Usage Guide](USAGE.md)** - API endpoints and examples
- **[Architecture](ARCHITECTURE.md)** - System design and internals
- **[Project Structure](PROJECT_STRUCTURE.md)** - File organization
- **[Migration Guide](MIGRATION.md)** - Upgrade from V1 to V2
- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Complete overview

## 🔧 Development

```bash
# Install dev dependencies
make dev-install

# Run tests
make test

# Run tests with coverage
make test-cov

# Lint code
make lint

# Format code
make format
```

## Open WebUI Integration

The server implements the Open WebUI tool server specification and can be added as a function tool:

1. Go to Open WebUI Settings → Functions
2. Add new function with URL: `http://your-server:8000`
3. The tool will auto-register available operations

## License

MIT
