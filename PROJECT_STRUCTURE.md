# Project Structure

```
open-webui-gitlab-tool/
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Data models
│   ├── blackboard.py             # Blackboard coordination
│   ├── orchestrator.py           # Agent orchestration
│   ├── gitlab_client.py          # GitLab API client
│   ├── ollama_client.py          # Ollama LLM client
│   └── agents/                   # Specialist agents
│       ├── __init__.py
│       ├── base.py               # Base agent class
│       ├── project_planner.py    # Project planning agent
│       ├── issue_summarizer.py   # Issue analysis agent
│       ├── mr_analyzer.py        # MR analysis agent
│       ├── code_reviewer.py      # Code review agent
│       ├── pipeline_reviewer.py  # Pipeline analysis agent
│       └── repo_browser.py       # Repository browser agent
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_gitlab_client.py
│   └── test_blackboard.py
│
├── docs/                         # Documentation (generated)
│
├── .env.example                  # Environment template
├── .gitignore
├── pyproject.toml               # Project metadata & deps
├── Dockerfile                   # Docker image
├── docker-compose.yml           # Docker Compose setup
├── Makefile                     # Development commands
├── README.md                    # Main documentation
├── USAGE.md                     # Usage guide
├── ARCHITECTURE.md              # Architecture docs
├── MIGRATION.md                 # V1 to V2 migration
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT License
└── gitlab_v1_legacy.py          # Legacy V1 code (reference)
```

## Key Components

### Core Application (`src/`)

- **main.py**: FastAPI server with all API endpoints
- **config.py**: Pydantic settings from environment
- **models.py**: Type-safe data models
- **blackboard.py**: Central coordination using Flock
- **orchestrator.py**: Manages agent execution

### Integrations

- **gitlab_client.py**: GitLab REST API wrapper
- **ollama_client.py**: Ollama LLM wrapper

### Agents (`src/agents/`)

Each agent is a specialist with domain expertise:

1. **ProjectPlannerAgent**: Overall project analysis
2. **IssueSummarizerAgent**: Issue analysis and summarization
3. **MRAnalyzerAgent**: Merge request analysis
4. **CodeReviewerAgent**: AI-powered code review
5. **PipelineReviewerAgent**: CI/CD pipeline analysis
6. **RepoBrowserAgent**: Repository browsing

### Configuration Files

- **pyproject.toml**: Dependencies, build config, tool settings
- **.env.example**: Environment variable template
- **Dockerfile**: Container image definition
- **docker-compose.yml**: Multi-container setup
- **Makefile**: Common development tasks

### Documentation

- **README.md**: Project overview and quick start
- **USAGE.md**: Detailed API usage examples
- **ARCHITECTURE.md**: System design documentation
- **MIGRATION.md**: V1 to V2 migration guide
- **CHANGELOG.md**: Version history

## Development Workflow

1. **Setup**: `make dev-install`
2. **Configure**: `cp .env.example .env` and edit
3. **Test**: `make test`
4. **Lint**: `make lint`
5. **Format**: `make format`
6. **Run**: `make run`

## Deployment

### Local Development
```bash
make run
```

### Docker
```bash
make docker-build
make docker-run
```

### Production
- Build Docker image
- Configure environment variables
- Deploy with Docker Compose or Kubernetes
- Set up reverse proxy (nginx/traefik)
- Configure monitoring and logging

## Testing

```
tests/
├── conftest.py           # Pytest configuration
├── test_gitlab_client.py # GitLab client tests
├── test_blackboard.py    # Blackboard tests
└── test_agents.py        # Agent tests (TODO)
```

Run tests:
```bash
make test           # Run all tests
make test-cov       # With coverage report
```

## File Sizes

Approximate line counts:

- **main.py**: ~500 lines (API endpoints)
- **blackboard.py**: ~300 lines (coordination)
- **orchestrator.py**: ~200 lines (execution)
- **gitlab_client.py**: ~300 lines (API wrapper)
- **ollama_client.py**: ~150 lines (LLM wrapper)
- **agents/*.py**: ~100-200 lines each
- **Total**: ~2500 lines (vs 2000 lines monolithic V1)

The increase in lines gives us:
- Better modularity
- Type safety
- Testing
- Documentation
- Error handling
- Extensibility

## Extension Points

To add new functionality:

1. **New Agent**: Create in `src/agents/`
2. **New Endpoint**: Add to `src/main.py`
3. **New Model**: Add to `src/models.py`
4. **New Operation Type**: Update `OperationType` enum

## Dependencies

### Production
- flock-sdk: Blackboard pattern
- fastapi: Web framework
- uvicorn: ASGI server
- pydantic: Data validation
- httpx: HTTP client
- ollama: LLM integration

### Development
- pytest: Testing
- pytest-asyncio: Async test support
- pytest-httpx: HTTP mocking
- ruff: Linting & formatting
- mypy: Type checking
