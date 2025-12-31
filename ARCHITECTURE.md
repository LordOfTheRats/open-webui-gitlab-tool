# Architecture Documentation

## Overview

The GitLab Flock Tool implements a sophisticated multi-agent system using the Flock blackboard pattern for coordinating GitLab operations with AI assistance.

## Core Components

### 1. Blackboard (`src/blackboard.py`)

The central coordination mechanism implementing the blackboard pattern:

- **Shared State**: All agents read from and write to a shared blackboard
- **Task Management**: Creates, updates, and tracks tasks
- **Message Bus**: Agents communicate through messages
- **Approval System**: Manages human approval workflows

Key features:
- Thread-safe with asyncio locks
- Task lifecycle management
- Message history (last 1000 messages)
- Automatic cleanup of old data

### 2. Orchestrator (`src/orchestrator.py`)

Manages agent lifecycle and task execution:

- **Task Submission**: Routes tasks to appropriate agents
- **Async Execution**: Runs tasks concurrently with timeouts
- **Approval Management**: Handles approval request/response flow
- **Status Tracking**: Monitors task progress

### 3. Specialist Agents (`src/agents/`)

Each agent is specialized for specific operations:

#### Project Planner (`project_planner.py`)
- Analyzes overall project health
- Provides planning and prioritization insights
- Assesses issues, MRs, and pipelines holistically

#### Issue Summarizer (`issue_summarizer.py`)
- Summarizes individual issues
- Analyzes collections of issues
- Identifies patterns and priorities

#### MR Analyzer (`mr_analyzer.py`)
- Analyzes merge requests
- Evaluates merge readiness
- Provides code review context

#### Code Reviewer (`code_reviewer.py`)
- Reviews code files
- Identifies bugs and security issues
- Suggests improvements

#### Pipeline Reviewer (`pipeline_reviewer.py`)
- Analyzes CI/CD pipelines
- Identifies failure patterns
- Provides optimization recommendations

### 4. GitLab Client (`src/gitlab_client.py`)

Handles all GitLab API interactions:

- **Read Operations**: Projects, issues, MRs, pipelines, files
- **Write Operations**: Create issues (with approval)
- **Error Handling**: Proper exception handling and logging
- **Path Encoding**: Correct URL encoding for GitLab API

### 5. Ollama Client (`src/ollama_client.py`)

Manages LLM interactions:

- **Generation**: Text completion for agent reasoning
- **Chat**: Multi-turn conversations
- **Embeddings**: Vector representations (future use)
- **Rate Limiting**: Respects concurrent request limits

### 6. FastAPI Server (`src/main.py`)

REST API implementing Open WebUI specification:

- **Analysis Endpoints**: Read-only operations
- **Write Endpoints**: Operations requiring approval
- **Approval Endpoints**: Human-in-the-loop controls
- **Task Status**: Monitor operation progress

## Data Flow

### Read Operation Flow

```
User Request
    ↓
FastAPI Endpoint
    ↓
Orchestrator.submit_task()
    ↓
Blackboard.create_task()
    ↓
Agent.execute()
    ↓
GitLab API + Ollama LLM
    ↓
Agent.process_task()
    ↓
Blackboard.update_task()
    ↓
Response to User
```

### Write Operation Flow (with Approval)

```
User Request
    ↓
FastAPI Endpoint
    ↓
Orchestrator.submit_task(requires_approval=True)
    ↓
Blackboard.request_approval()
    ↓
Task Status: REQUIRES_APPROVAL
    ↓
User Approval Decision
    ↓
Orchestrator.approve_task()
    ↓
Blackboard.resolve_approval()
    ↓
Resume Agent Execution
    ↓
GitLab Write Operation
    ↓
Response to User
```

## Agent Communication

Agents communicate through the blackboard using messages:

```python
await blackboard.post_message(
    agent_role=AgentRole.ISSUE_SUMMARIZER,
    content={
        "event": "analysis_complete",
        "summary": "...",
        "insights": [...]
    },
    task_id=task.id,
)
```

Other agents can subscribe to messages:

```python
messages = await blackboard.get_messages(
    agent_role=AgentRole.ISSUE_SUMMARIZER,
    since=datetime.utcnow() - timedelta(minutes=5),
)
```

## Configuration

### Environment Variables

- **GITLAB_URL**: GitLab instance URL
- **GITLAB_TOKEN**: Private access token
- **OLLAMA_URL**: Ollama API endpoint
- **OLLAMA_MODEL**: Model to use (e.g., llama3.2)
- **OLLAMA_MAX_CONCURRENT**: Max concurrent LLM requests
- **AGENT_TIMEOUT**: Max agent execution time
- **REQUIRE_APPROVAL_FOR_WRITES**: Enable approval for writes
- **APPROVAL_TIMEOUT**: How long to wait for approval

### Settings Management

Pydantic Settings with validation:

```python
from src.config import settings

settings.gitlab_url  # Validated HttpUrl
settings.ollama_max_concurrent  # Constrained int (1-10)
```

## Error Handling

### Timeout Handling

All agent executions have configurable timeouts:

```python
async with asyncio.timeout(settings.agent_timeout):
    await agent.process_task(task)
```

### Task Failure

Failed tasks are marked with error information:

```python
await blackboard.update_task(
    task_id,
    status=TaskStatus.FAILED,
    error=str(exception),
)
```

### Approval Timeout

Approval requests expire after configured timeout:

```python
if datetime.utcnow() > approval.expires_at:
    approval.status = ApprovalStatus.TIMEOUT
```

## Security

### GitLab Token

- Store in environment variable
- Never log or expose
- Use PRIVATE-TOKEN header

### Human Approval

Critical operations require approval:
- Creating/modifying issues
- Pipeline actions
- Repository writes

### CORS

Configured for Open WebUI:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Returns:
```json
{"status": "healthy", "version": "2.0.0"}
```

### Task Status

Monitor any task:
```bash
curl http://localhost:8000/api/tasks/{task_id}
```

### Logging

Structured logging throughout:
```python
logger.info("Agent %s completed task %s", self.role.value, task.id)
logger.error("Task %s failed: %s", task_id, error)
```

## Performance Considerations

### Concurrent Requests

Ollama concurrent requests are limited:
```python
OLLAMA_MAX_CONCURRENT=2  # Keep low for self-hosted
```

### Task Timeouts

Balance responsiveness with LLM response times:
```python
AGENT_TIMEOUT=600  # 10 minutes default
OLLAMA_TIMEOUT=300  # 5 minutes for LLM
```

### Message History

Bounded to prevent memory issues:
```python
if len(self.messages) > 1000:
    self.messages = self.messages[-1000:]
```

## Extending the System

### Adding New Agents

1. Create agent class in `src/agents/`:
```python
class MyAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(AgentRole.MY_AGENT, *args, **kwargs)
    
    async def can_handle(self, task: Task) -> bool:
        return task.agent_role == self.role
    
    async def execute(self, task: Task) -> dict:
        # Implementation
        pass
```

2. Register in `src/agents/__init__.py`
3. Add to `create_agents()` function

### Adding New Endpoints

Add to `src/main.py`:
```python
@app.post("/api/my-operation")
async def my_operation(request: MyRequest) -> TaskStatusResponse:
    task = await orchestrator.submit_task(
        agent_role=AgentRole.MY_AGENT,
        operation_type=OperationType.ANALYSIS,
        input_data=request.dict(),
    )
    return await orchestrator.wait_for_task(task.id)
```

## Testing

Run tests:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src tests/
```

## Deployment

### Docker

```bash
docker build -t gitlab-flock-tool .
docker run -p 8000:8000 --env-file .env gitlab-flock-tool
```

### Docker Compose

```bash
docker-compose up -d
```

Includes both the tool and Ollama.

### Production Considerations

- Use proper secret management
- Configure CORS restrictively
- Set up reverse proxy (nginx)
- Monitor resource usage
- Configure log aggregation
