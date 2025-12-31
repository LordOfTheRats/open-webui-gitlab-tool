# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### Complete Rewrite

This is a complete architectural reimagination of the GitLab tool.

### Added

- **Multi-Agent System**: Specialized agents using Flock blackboard pattern
  - Project Planner Agent
  - Issue Summarizer Agent
  - Merge Request Analyzer Agent
  - Code Reviewer Agent
  - Pipeline Reviewer Agent
  
- **FastAPI Server**: REST API implementing Open WebUI tool server specification
  - `/api/analyze-project` - Project analysis with AI insights
  - `/api/analyze-issue` - Issue summarization
  - `/api/list-issues` - Issue list analysis
  - `/api/analyze-mr` - MR analysis
  - `/api/list-mrs` - MR list analysis
  - `/api/review-code` - AI-powered code review
  - `/api/analyze-pipelines` - Pipeline analysis
  - `/api/create-issue` - Create issue (requires approval)
  - `/api/approvals/pending` - List pending approvals
  - `/api/approve/{id}` - Approve/reject operations
  - `/api/tasks/{id}` - Task status tracking

- **Human Approval System**: Robust approval workflow for critical operations
  - Configurable approval requirements
  - Timeout handling
  - Comment support
  
- **Blackboard Coordination**: Shared state management for agents
  - Task management
  - Message bus
  - Approval requests
  - History tracking

- **Orchestrator**: Manages agent execution and task lifecycle
  - Async execution with timeouts
  - Task status tracking
  - Approval workflow integration

- **Infrastructure**:
  - Docker support with Dockerfile
  - Docker Compose with Ollama
  - Makefile for development tasks
  - Comprehensive test suite
  - Type hints throughout
  - Structured logging

- **Documentation**:
  - Architecture documentation
  - Usage guide
  - Migration guide
  - API examples

### Changed

- **Architecture**: From monolithic to multi-agent system
- **Execution**: From synchronous to asynchronous
- **Configuration**: From Open WebUI valves to environment variables
- **Integration**: From single function to REST API server

### Technical Improvements

- **Type Safety**: Full type hints with mypy validation
- **Code Quality**: Ruff linting and formatting
- **Testing**: pytest with async support
- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy to add new agents
- **Performance**: Async execution, controlled concurrency
- **Reliability**: Timeouts, error handling, retries

### Dependencies

- `flock-sdk>=0.5.0` - Blackboard pattern implementation
- `fastapi>=0.115.0` - Web framework
- `uvicorn[standard]>=0.32.0` - ASGI server
- `pydantic>=2.9.0` - Data validation
- `pydantic-settings>=2.6.0` - Settings management
- `httpx>=0.27.0` - Async HTTP client
- `ollama>=0.4.0` - LLM integration

### Removed

- Open WebUI function format (use REST API instead)
- Synchronous execution model
- Valve-based configuration

## [1.9.1] - 2024

### Last V1 Release

Final version of the monolithic implementation. See `gitlab_v1_legacy.py`.

Features:
- GitLab projects, issues, MRs
- Repository browsing
- Wiki operations
- Pipeline controls
- Compact output mode

---

## Migration Note

Version 2.0 is not backward compatible with 1.x. See [MIGRATION.md](MIGRATION.md) for details.

For V1 users:
- V1 code preserved as `gitlab_v1_legacy.py`
- No further V1 updates planned
- Recommend migration to V2

[2.0.0]: https://github.com/LordOfTheRats/open-webui-gitlab-tool/releases/tag/v2.0.0
[1.9.1]: https://github.com/LordOfTheRats/open-webui-gitlab-tool/releases/tag/v1.9.1
