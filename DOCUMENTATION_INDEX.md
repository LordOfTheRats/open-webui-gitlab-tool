# GitLab Multi-Agent Tool - Documentation Index

## Overview

This repository contains comprehensive documentation for implementing a GitLab multi-agent tool using the flock-core framework, Ollama for LLM capabilities, and FastAPI for the API layer.

## Documentation Files

### 1. [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) - Main Architecture Document
**Purpose**: Complete technical specification and architecture design

**Contents**:
- Architecture principles and design goals
- Detailed specifications for all 5 agents:
  - Issue Summarization Agent
  - MR Summarization Agent
  - Code Review Agent
  - Pipeline Triage Agent
  - Repository Operations Agent
- Artifact system design (Pydantic models)
- Ollama integration patterns
- Prompt engineering guidelines
- Agent implementation examples
- Orchestration patterns
- FastAPI integration
- Human approval workflow
- Testing strategy
- Deployment considerations
- Best practices

**Target Audience**: Technical architects, senior developers

**Length**: ~13,000 lines

---

### 2. [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Step-by-Step Guide
**Purpose**: Practical implementation roadmap with code samples

**Contents**:
- File structure to create
- Implementation order (10 steps over 20 days)
- Code snippets for each component:
  - OllamaClient
  - BaseAgent
  - Individual agents
  - Agent factory
  - Orchestration layer
  - FastAPI endpoints
  - Approval UI
- Testing checklist
- Validation steps (curl examples)
- Troubleshooting guide
- Performance tuning tips

**Target Audience**: Developers implementing the system

**Length**: ~900 lines

---

### 3. [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md) - Visual Documentation
**Purpose**: ASCII diagrams showing system architecture

**Contents**:
- System overview diagram
- Agent execution flow
- Concurrency control visualization
- Artifact flow
- Approval workflow state machine
- Agent class hierarchy
- Data flow diagram
- Component dependencies
- Deployment architecture (Docker & K8s)
- Performance characteristics
- Security model

**Target Audience**: All stakeholders, especially visual learners

**Length**: ~800 lines

---

## Quick Navigation

### For Project Managers / Stakeholders
1. Start with: **ARCHITECTURE_DIAGRAMS.md** - System Overview section
2. Then read: **AGENT_ARCHITECTURE.md** - Overview and Agent Specifications sections
3. Review: **IMPLEMENTATION_GUIDE.md** - Implementation Checklist

### For Architects / Tech Leads
1. Start with: **AGENT_ARCHITECTURE.md** - Complete read
2. Reference: **ARCHITECTURE_DIAGRAMS.md** - For visualization
3. Plan with: **IMPLEMENTATION_GUIDE.md** - Step-by-step timeline

### For Developers
1. Start with: **IMPLEMENTATION_GUIDE.md** - Implementation order
2. Reference: **AGENT_ARCHITECTURE.md** - Specific agent details
3. Use: **ARCHITECTURE_DIAGRAMS.md** - For understanding flows

### For DevOps / SRE
1. Start with: **ARCHITECTURE_DIAGRAMS.md** - Deployment Architecture
2. Read: **AGENT_ARCHITECTURE.md** - Deployment Considerations section
3. Reference: **IMPLEMENTATION_GUIDE.md** - Step 9 (Deployment)

---

## Key Design Decisions

### 1. Agent Framework: flock-core
**Rationale**: 
- Built for agent orchestration
- Artifact-based communication
- Type-safe with Pydantic
- SQLite persistence included

### 2. LLM Provider: Ollama (Self-Hosted)
**Rationale**:
- Self-hosted requirement met
- GPU acceleration support
- Simple API
- Multiple model support

**Constraint**: Max 2 concurrent requests
- Solution: Global semaphore limiter
- Prevents resource exhaustion
- Automatic queueing

### 3. API Layer: FastAPI
**Rationale**:
- Modern async Python framework
- Auto-generated OpenAPI docs
- Pydantic integration
- High performance

### 4. Human Approval System
**Rationale**:
- Safety for write operations
- Audit trail
- Timeout protection
- Simple workflow

---

## Core Patterns

### 1. Artifact-Based Communication
```python
Input Artifact → Agent.execute() → Output Artifact
```
- Type-safe with Pydantic
- Immutable
- Serializable
- Traceable

### 2. Concurrency Control
```python
async with limiter:
    response = await ollama.generate(prompt)
```
- Global semaphore (max 2)
- Automatic queueing
- No manual coordination needed

### 3. Approval Workflow
```python
if requires_approval:
    request = create_approval_request()
    await wait_for_approval(request)
    if approved:
        execute_operation()
```
- Async waiting
- Timeout handling
- Status tracking

### 4. Agent Independence
```python
class MyAgent(BaseAgent[InputT, OutputT]):
    async def execute(self, input: InputT) -> OutputT:
        # Completely self-contained
        pass
```
- No shared state
- Single responsibility
- Composable

---

## Implementation Timeline

### Phase 1: Core Infrastructure (Week 1-2)
- OllamaClient
- BaseAgent
- Orchestration
- First agent (Issue Summarization)

### Phase 2: Agent Development (Week 3-4)
- MR Summarization
- Code Review
- Pipeline Triage
- Repository Operations

### Phase 3: Integration (Week 5)
- Approval workflow
- Approval UI
- Integration tests

### Phase 4: Production (Week 6)
- Monitoring
- Deployment
- Documentation
- Security audit

---

## Technology Stack

### Core Dependencies
```toml
flock-core>=0.5.30        # Agent framework
fastapi>=0.115.0          # API layer
uvicorn[standard]>=0.32.0 # ASGI server
httpx>=0.27.0             # Async HTTP client
pydantic>=2.9.0           # Data validation
pydantic-settings>=2.6.0  # Config management
python-dotenv>=1.0.0      # Environment vars
```

### Development Dependencies
```toml
pytest>=8.3.0             # Testing
pytest-asyncio>=0.24.0    # Async tests
pytest-cov>=6.0.0         # Coverage
black>=24.0.0             # Formatting
ruff>=0.7.0               # Linting
mypy>=1.13.0              # Type checking
```

### External Services
- **GitLab CE**: Self-hosted (required)
- **Ollama**: Self-hosted with GPU (required)
- **Open WebUI**: For user interface (optional)

---

## Configuration

### Required Environment Variables
```env
# GitLab
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Server
HOST=0.0.0.0
PORT=8000
MAX_CONCURRENT_REQUESTS=2

# Approval
REQUIRE_APPROVAL_FOR_WRITES=true
APPROVAL_TIMEOUT_SECONDS=300
```

### Optional Configuration
```env
# SSL
GITLAB_VERIFY_SSL=true

# Timeouts
GITLAB_TIMEOUT=30
OLLAMA_TIMEOUT=120

# Flock
FLOCK_STORE_PATH=.flock/history.db
FLOCK_LOG_LEVEL=INFO
```

---

## Agent Capabilities

### Issue Summarization Agent
- **Input**: Project + Issue IID
- **Output**: Summary, key points, priority, complexity
- **Use Cases**: 
  - Quick issue overview
  - Stakeholder identification
  - Priority assessment

### MR Summarization Agent
- **Input**: Project + MR IID
- **Output**: Changes summary, risks, recommendations
- **Use Cases**:
  - Review preparation
  - Risk identification
  - Change impact analysis

### Code Review Agent
- **Input**: Project + MR IID + Review depth
- **Output**: Issues, suggestions, approval recommendation
- **Use Cases**:
  - Automated code review
  - Security scanning
  - Style enforcement

### Pipeline Triage Agent
- **Input**: Project + Pipeline ID
- **Output**: Root cause, failed jobs, recommendations
- **Use Cases**:
  - CI/CD debugging
  - Failure analysis
  - Fix recommendations

### Repository Operations Agent
- **Input**: Operation type + parameters
- **Output**: Operation result
- **Use Cases**:
  - File operations
  - Repository queries
  - Batch operations

---

## API Endpoints

### Agent Endpoints
```
POST /api/summarize-issue       # Issue summarization
POST /api/summarize-mr          # MR summarization
POST /api/review-mr             # Code review
POST /api/triage-pipeline       # Pipeline triage
POST /api/repo-query            # Repository queries
POST /api/repo-write            # Repository writes (requires approval)
```

### Approval Endpoints
```
GET  /approvals                 # Approval UI
GET  /api/approvals/pending     # List pending approvals
GET  /api/approvals/{id}        # Get approval details
POST /api/approvals/{id}/approve # Approve operation
POST /api/approvals/{id}/reject  # Reject operation
```

### System Endpoints
```
GET  /health                    # Health check
GET  /api/status                # System status
GET  /docs                      # OpenAPI documentation
```

---

## Security Considerations

### Authentication
- Currently: No built-in user auth
- GitLab token stored in environment
- Recommendation: Add API key auth for production

### Authorization
- Human approval for write operations
- Configurable timeout (default 5 min)
- Audit trail via approval manager

### Data Protection
- Tokens in environment (not code)
- No sensitive data in logs
- TLS for external access

### Rate Limiting
- Ollama: Max 2 concurrent
- GitLab API: Respect rate limits
- Recommendation: Add endpoint rate limiting

---

## Testing Strategy

### Unit Tests
- Mock GitLab client
- Mock Ollama client
- Test each agent in isolation
- Coverage target: >80%

### Integration Tests
- Real GitLab instance (test environment)
- Real Ollama instance
- End-to-end workflows
- Approval scenarios

### Load Tests
- Concurrent request handling
- Concurrency limit verification
- Queue behavior
- Resource usage

### Manual Tests
- UI approval workflow
- Error handling
- Edge cases
- User experience

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Development)
```bash
docker-compose up -d
```
- Simple setup
- GPU support for Ollama
- Persistent volumes
- Easy to update

### Option 2: Kubernetes (Recommended for Production)
```bash
kubectl apply -f kubernetes/
```
- Scalable
- High availability
- Resource management
- Monitoring integration

### Option 3: Standalone
```bash
pip install -e .
uvicorn gitlab_tool.main:app
```
- Development only
- Requires separate Ollama
- Manual configuration

---

## Monitoring & Observability

### Metrics (Prometheus)
- `agent_invocations_total` - Counter by agent and status
- `agent_duration_seconds` - Histogram by agent
- `ollama_queue_size` - Current queue depth
- `approval_requests_pending` - Pending approval count

### Logging
- Structured JSON logging
- Request tracing
- Error context
- Performance metrics

### Health Checks
- `/health` - Overall system health
- `/api/status` - Detailed component status
- Ollama connectivity
- GitLab connectivity

---

## Troubleshooting

### Common Issues

**Issue**: Agents timeout
- **Cause**: Ollama slow or unavailable
- **Solution**: Check Ollama logs, verify GPU, increase timeout

**Issue**: Concurrency not working
- **Cause**: Limiter not initialized
- **Solution**: Verify `get_limiter()` called in OllamaClient

**Issue**: GitLab API errors
- **Cause**: Invalid token or rate limit
- **Solution**: Verify token scope, check rate limits

**Issue**: Approval doesn't work
- **Cause**: Approval manager not shared
- **Solution**: Use global `get_approval_manager()`

---

## Next Steps

After implementing the base system:

1. **Add more agents**:
   - Planning agent (project/milestone management)
   - Wiki operations agent
   - Branch management agent

2. **Enhance existing agents**:
   - Multi-file code review
   - Historical trend analysis
   - Predictive issue prioritization

3. **Add features**:
   - User authentication
   - Role-based access control
   - Webhook support
   - Slack/email notifications

4. **Optimize**:
   - Response caching
   - Batch operations
   - Multi-model support
   - Advanced prompt engineering

---

## References

### External Documentation
- [flock-core GitHub](https://github.com/whiteducksoftware/flock)
- [GitLab API Docs](https://docs.gitlab.com/ee/api/)
- [Ollama API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [Open WebUI Tools](https://docs.openwebui.com/features/tools/)

### Internal Documentation
- [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) - Architecture details
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Implementation steps
- [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md) - Visual diagrams
- [README.md](./README.md) - Project overview

---

## Support & Contributing

### Getting Help
1. Check documentation files above
2. Review existing issues
3. Test components individually
4. Ask in discussions

### Contributing
1. Read architecture docs
2. Follow implementation guide
3. Write tests
4. Update documentation
5. Submit pull request

---

## License

MIT License - See [LICENSE](./LICENSE) file for details.

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-31  
**Status**: Complete Planning Documentation
