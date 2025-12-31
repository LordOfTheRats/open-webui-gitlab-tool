# Implementation Guide: Flock-Core Agent Architecture

## Quick Start

This guide provides a step-by-step implementation roadmap for the GitLab multi-agent tool using flock-core. For complete architectural details, see [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md).

## File Structure to Create

```
gitlab_tool/
├── agents/
│   ├── __init__.py                    # Export agents
│   ├── base.py                        # BaseAgent class ✓ CREATE
│   ├── factory.py                     # AgentFactory ✓ CREATE
│   ├── issue_summarization.py        # ✓ CREATE
│   ├── mr_summarization.py            # ✓ CREATE
│   ├── code_review.py                 # ✓ CREATE
│   ├── pipeline_triage.py             # ✓ CREATE
│   └── repository_operations.py       # ✓ CREATE
│
├── llm/
│   ├── __init__.py                    # ✓ CREATE
│   ├── ollama.py                      # OllamaClient ✓ CREATE
│   └── utils.py                       # Token mgmt ✓ CREATE
│
├── orchestration.py                   # ✓ CREATE
├── main.py                            # ✓ UPDATE (add agent endpoints)
│
└── artifacts/
    └── requests.py                    # ✓ UPDATE (add missing models)
```

## Implementation Order

### Step 1: Core Infrastructure (Day 1-2)

#### 1.1 Create Ollama Client

**File**: `gitlab_tool/llm/ollama.py`

```python
from typing import Optional
import httpx
from gitlab_tool.config import Settings
from gitlab_tool.utils.concurrency import get_limiter

class OllamaClient:
    """Async Ollama client with concurrency control."""
    
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
        self.limiter = get_limiter()
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate completion with concurrency control."""
        async with self.limiter:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature}
                }
                if system:
                    payload["system"] = system
                if max_tokens:
                    payload["options"]["num_predict"] = max_tokens
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
```

**Test**: Verify concurrency limiting works

#### 1.2 Create Base Agent

**File**: `gitlab_tool/agents/base.py`

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from pydantic import BaseModel
from gitlab_tool.config import Settings
from gitlab_tool.client.gitlab import GitLabClient
from gitlab_tool.llm.ollama import OllamaClient

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)

class BaseAgent(ABC, Generic[InputT, OutputT]):
    """Base class for all agents."""
    
    def __init__(
        self,
        settings: Settings,
        gitlab_client: GitLabClient,
        ollama_client: OllamaClient,
    ):
        self.settings = settings
        self.gitlab = gitlab_client
        self.ollama = ollama_client
    
    @abstractmethod
    async def execute(self, input_artifact: InputT) -> OutputT:
        """Execute agent logic and return output artifact."""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """Return agent name."""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """Return agent description."""
        pass
```

#### 1.3 Create Orchestration Layer

**File**: `gitlab_tool/orchestration.py`

```python
from pydantic import BaseModel
from gitlab_tool.config import Settings
from gitlab_tool.client.gitlab import GitLabClient
from gitlab_tool.llm.ollama import OllamaClient
from gitlab_tool.agents.factory import AgentFactory

async def invoke_agent(
    agent_name: str,
    input_artifact: BaseModel,
    settings: Settings,
) -> BaseModel:
    """Invoke a single agent."""
    gitlab_client = GitLabClient(settings)
    ollama_client = OllamaClient(settings)
    
    agent = AgentFactory.create(
        agent_name,
        settings,
        gitlab_client,
        ollama_client
    )
    
    return await agent.execute(input_artifact)
```

### Step 2: First Agent - Issue Summarization (Day 3-4)

#### 2.1 Update Artifact Models

**File**: `gitlab_tool/artifacts/gitlab.py` (update)

Add:
```python
class IssueSummary(BaseModel):
    """Enhanced issue summary."""
    issue_iid: int
    project: str
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    status: str
    priority: Optional[str] = None
    complexity: Optional[str] = None
    stakeholders: list[str] = Field(default_factory=list)  # NEW
    related_issues: list[int] = Field(default_factory=list)  # NEW
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**File**: `gitlab_tool/artifacts/requests.py` (update)

Add:
```python
class IssueSummaryRequest(BaseModel):
    """Request to summarize an issue."""
    project: str = Field(..., description="Project path")
    issue_iid: int = Field(..., description="Issue IID")
    include_comments: bool = Field(default=False)
    max_comments: int = Field(default=50)  # NEW
```

#### 2.2 Implement Issue Summarization Agent

**File**: `gitlab_tool/agents/issue_summarization.py`

See complete implementation in AGENT_ARCHITECTURE.md section "Agent Implementation".

Key methods:
- `execute()`: Main logic
- `_build_prompt()`: Create LLM prompt
- `_parse_response()`: Parse JSON from LLM
- `_extract_stakeholders()`: Extract usernames

#### 2.3 Create Agent Factory

**File**: `gitlab_tool/agents/factory.py`

```python
from typing import Dict, Type
from .base import BaseAgent
from .issue_summarization import IssueSummarizationAgent

class AgentFactory:
    _agents: Dict[str, Type[BaseAgent]] = {
        "issue_summarizer": IssueSummarizationAgent,
    }
    
    @classmethod
    def create(cls, agent_name: str, settings, gitlab_client, ollama_client):
        agent_class = cls._agents.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {agent_name}")
        return agent_class(settings, gitlab_client, ollama_client)
    
    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())
```

#### 2.4 Add FastAPI Endpoint

**File**: `gitlab_tool/main.py` (update)

```python
from gitlab_tool.orchestration import invoke_agent
from gitlab_tool.artifacts.requests import IssueSummaryRequest

@app.post("/api/summarize-issue")
async def summarize_issue(request: IssueSummaryRequest):
    """Summarize a GitLab issue."""
    try:
        result = await invoke_agent("issue_summarizer", request, settings)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 2.5 Write Tests

**File**: `tests/agents/test_issue_summarization.py`

See complete test in AGENT_ARCHITECTURE.md "Testing Strategy" section.

### Step 3: MR Summarization Agent (Day 5-6)

#### 3.1 Update Artifacts

**File**: `gitlab_tool/artifacts/gitlab.py` (update)

```python
class MergeRequestSummary(BaseModel):
    """Enhanced MR summary."""
    mr_iid: int
    project: str
    title: str
    summary: str
    changes_summary: str
    files_changed: list[str] = Field(default_factory=list)  # NEW
    additions: int = 0  # NEW
    deletions: int = 0  # NEW
    review_status: str
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)  # NEW
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

**File**: `gitlab_tool/artifacts/requests.py` (update)

```python
class MRSummaryRequest(BaseModel):
    """Request to summarize an MR."""
    project: str
    mr_iid: int
    include_diff: bool = True
    max_diff_lines: int = 500  # NEW
    include_comments: bool = True
```

#### 3.2 Implement Agent

**File**: `gitlab_tool/agents/mr_summarization.py`

Key logic:
1. Fetch MR metadata
2. Get diff if requested (truncate with `prepare_diff_for_llm()`)
3. Get comments
4. Call Ollama with structured prompt
5. Parse and return summary

#### 3.3 Add to Factory

**File**: `gitlab_tool/agents/factory.py` (update)

```python
from .mr_summarization import MRSummarizationAgent

class AgentFactory:
    _agents = {
        "issue_summarizer": IssueSummarizationAgent,
        "mr_summarizer": MRSummarizationAgent,  # ADD
    }
```

#### 3.4 Add Endpoint

**File**: `gitlab_tool/main.py` (update)

```python
@app.post("/api/summarize-mr")
async def summarize_mr(request: SummarizeMergeRequestRequest):
    """Summarize a merge request."""
    result = await invoke_agent("mr_summarizer", request, settings)
    return result.model_dump()
```

### Step 4: Code Review Agent (Day 7-9)

#### 4.1 Create Artifact Models

**File**: `gitlab_tool/artifacts/gitlab.py` (update)

```python
class CodeIssue(BaseModel):
    """Code issue found in review."""
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str  # "security", "bug", "style", "performance"
    file_path: str
    line_number: Optional[int] = None
    description: str
    recommendation: str

class CodeSuggestion(BaseModel):
    """Code improvement suggestion."""
    file_path: str
    line_number: Optional[int] = None
    description: str
    suggested_code: Optional[str] = None

class CodeReview(BaseModel):
    """Code review results."""
    mr_iid: int
    project: str
    overall_assessment: str
    issues_found: list[CodeIssue] = Field(default_factory=list)
    suggestions: list[CodeSuggestion] = Field(default_factory=list)
    approval_recommendation: bool
    review_depth: str
    confidence_score: float  # 0.0-1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### 4.2 Implement Agent

**File**: `gitlab_tool/agents/code_review.py`

Special considerations:
- Chunk large diffs
- Different prompts for review_depth ("quick", "standard", "thorough")
- Parse structured JSON with issues/suggestions
- Calculate confidence score

#### 4.3 Add Utility for Diff Processing

**File**: `gitlab_tool/llm/utils.py`

```python
def prepare_diff_for_llm(diff: str, max_tokens: int = 2000) -> str:
    """Prepare diff for LLM consumption."""
    estimated = estimate_tokens(diff)
    if estimated <= max_tokens:
        return diff
    
    # Keep file headers, truncate hunks
    lines = diff.split("\n")
    result = []
    current_tokens = 0
    
    for line in lines:
        line_tokens = estimate_tokens(line)
        if line.startswith(("diff --git", "+++", "---")):
            result.append(line)
            current_tokens += line_tokens
        elif current_tokens + line_tokens <= max_tokens:
            result.append(line)
            current_tokens += line_tokens
        else:
            result.append("[... diff truncated ...]")
            break
    
    return "\n".join(result)
```

### Step 5: Pipeline Triage Agent (Day 10-11)

#### 5.1 Create Artifacts

**File**: `gitlab_tool/artifacts/gitlab.py` (update)

```python
class JobFailure(BaseModel):
    """Failed job details."""
    job_id: int
    job_name: str
    stage: str
    failure_reason: str
    error_messages: list[str] = Field(default_factory=list)
    log_snippet: str
    suggested_fix: Optional[str] = None

class PipelineAnalysis(BaseModel):
    """Pipeline triage results."""
    pipeline_id: int
    project: str
    status: str
    ref: str
    failed_jobs: list[JobFailure] = Field(default_factory=list)
    root_cause: Optional[str] = None
    recommendations: list[str] = Field(default_factory=list)
    related_commits: list[str] = Field(default_factory=list)
    estimated_fix_time: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### 5.2 Implement Agent

**File**: `gitlab_tool/agents/pipeline_triage.py`

Key logic:
1. Get pipeline and jobs
2. Filter failed jobs
3. Fetch logs (truncate to max_log_lines)
4. Extract error messages/stack traces
5. Analyze collectively with Ollama
6. Identify common root cause
7. Generate recommendations

### Step 6: Repository Operations Agent (Day 12-13)

#### 6.1 Create Artifacts

**File**: `gitlab_tool/artifacts/requests.py` (update)

```python
class RepoQueryRequest(BaseModel):
    """Repository query request."""
    project: str
    operation: Literal["list_tree", "get_file", "search_files", "compare"]
    path: str = ""
    ref: str = "HEAD"
    recursive: bool = False
    query: Optional[str] = None

class RepoWriteRequest(BaseModel):
    """Repository write request."""
    project: str
    operation: Literal["create_file", "update_file", "delete_file"]
    file_path: str
    content: Optional[str] = None
    branch: str
    commit_message: str
    requires_approval: bool = True
```

**File**: `gitlab_tool/artifacts/gitlab.py` (update)

```python
class RepoQueryResult(BaseModel):
    """Repository query result."""
    project: str
    operation: str
    results: list[dict]
    summary: str  # LLM-generated
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class RepoWriteResult(BaseModel):
    """Repository write result."""
    project: str
    operation: str
    file_path: str
    branch: str
    commit_sha: Optional[str] = None
    approval_required: bool
    approval_status: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

#### 6.2 Implement Agent

**File**: `gitlab_tool/agents/repository_operations.py`

Two execution paths:
- **Query**: Execute GitLab API, use Ollama to summarize
- **Write**: Check approval requirement, create approval request, wait, execute

### Step 7: Human Approval UI (Day 14)

#### 7.1 Create Templates Directory

**File**: `gitlab_tool/templates/approvals.html`

Simple HTML page with:
- List of pending approvals
- Approve/Reject buttons
- Auto-refresh every 10s
- AJAX calls to approval endpoints

#### 7.2 Add Approval Endpoints

**File**: `gitlab_tool/main.py` (update)

```python
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from gitlab_tool.utils.approval import get_approval_manager

templates = Jinja2Templates(directory="gitlab_tool/templates")

@app.get("/approvals", response_class=HTMLResponse)
async def approvals_ui(request: Request):
    manager = get_approval_manager()
    pending = manager.list_pending()
    return templates.TemplateResponse(
        "approvals.html",
        {"request": request, "pending_requests": pending}
    )

@app.get("/api/approvals/pending")
async def list_pending_approvals():
    manager = get_approval_manager()
    return [req.model_dump() for req in manager.list_pending()]

@app.post("/api/approvals/{request_id}/approve")
async def approve_request(request_id: str):
    manager = get_approval_manager()
    request = manager.approve(request_id)
    return request.model_dump()

@app.post("/api/approvals/{request_id}/reject")
async def reject_request(request_id: str, reason: str = None):
    manager = get_approval_manager()
    request = manager.reject(request_id, reason)
    return request.model_dump()
```

### Step 8: Testing & Documentation (Day 15-16)

#### 8.1 Unit Tests

For each agent, create:
- Mock fixtures for GitLab client
- Mock fixtures for Ollama client
- Test successful execution
- Test error handling
- Test edge cases

#### 8.2 Integration Tests

**File**: `tests/integration/test_orchestration.py`

Test:
- Agent invocation end-to-end
- Approval workflow
- Concurrency limiting
- Error propagation

#### 8.3 Load Tests

**File**: `tests/load/test_concurrency.py`

Verify:
- Max 2 concurrent Ollama requests
- Proper queueing
- No deadlocks

#### 8.4 Documentation

Update README.md with:
- Quick start guide
- Agent descriptions
- Configuration options
- Example requests/responses

### Step 9: Deployment (Day 17-18)

#### 9.1 Docker Setup

**File**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install -e .

COPY gitlab_tool ./gitlab_tool

RUN mkdir -p .flock

EXPOSE 8000

CMD ["uvicorn", "gitlab_tool.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**File**: `docker-compose.yml`

Include:
- gitlab-tool service
- ollama service (with GPU)
- Volume mounts for .flock storage

#### 9.2 Environment Configuration

Create `.env.example` with all required variables.

#### 9.3 Monitoring

Add Prometheus metrics:
- Agent invocation counts
- Agent duration histograms
- Ollama queue depth
- Approval pending count

### Step 10: Production Hardening (Day 19-20)

#### 10.1 Error Handling

Add comprehensive error handling:
- GitLab API errors
- Ollama timeouts
- Network failures
- Invalid LLM responses

#### 10.2 Logging

Structured logging with:
- Request IDs
- Agent execution traces
- Performance metrics
- Error context

#### 10.3 Security

- Input validation (all user inputs)
- Rate limiting
- Token sanitization in logs
- HTTPS enforcement

#### 10.4 Performance

- Response caching where appropriate
- Connection pooling
- Batch operations when possible

## Testing Checklist

- [ ] Unit tests for each agent pass
- [ ] Integration tests pass
- [ ] Concurrency limit verified (max 2 Ollama)
- [ ] Approval workflow tested
- [ ] All endpoints return valid responses
- [ ] Error cases handled gracefully
- [ ] Load test with 10+ concurrent requests
- [ ] Docker Compose deploys successfully
- [ ] Health check endpoint responds
- [ ] Metrics endpoint exports data

## Validation Steps

### 1. Test Issue Summarization

```bash
curl -X POST http://localhost:8000/api/summarize-issue \
  -H "Content-Type: application/json" \
  -d '{
    "project": "mygroup/myproject",
    "issue_iid": 1,
    "include_comments": true
  }'
```

Expected: JSON with summary, key_points, priority, etc.

### 2. Test MR Summarization

```bash
curl -X POST http://localhost:8000/api/summarize-mr \
  -H "Content-Type: application/json" \
  -d '{
    "project": "mygroup/myproject",
    "mr_iid": 1,
    "include_diff": true
  }'
```

Expected: JSON with changes_summary, risks, recommendations.

### 3. Test Code Review

```bash
curl -X POST http://localhost:8000/api/review-mr \
  -H "Content-Type: application/json" \
  -d '{
    "project": "mygroup/myproject",
    "mr_iid": 1,
    "review_depth": "standard"
  }'
```

Expected: JSON with issues_found, suggestions, approval_recommendation.

### 4. Test Pipeline Triage

```bash
curl -X POST http://localhost:8000/api/triage-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "project": "mygroup/myproject",
    "pipeline_id": 123,
    "include_logs": true
  }'
```

Expected: JSON with failed_jobs, root_cause, recommendations.

### 5. Test Concurrency

```bash
# Run 5 concurrent requests
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/summarize-issue \
    -H "Content-Type: application/json" \
    -d "{\"project\": \"test\", \"issue_iid\": $i}" &
done
wait
```

Expected: All complete, but only 2 hit Ollama at a time.

### 6. Test Approval Workflow

```bash
# Check pending approvals
curl http://localhost:8000/api/approvals/pending

# Approve via UI
open http://localhost:8000/approvals
```

Expected: Approval UI shows pending requests, can approve/reject.

## Troubleshooting

### Ollama Connection Issues

```bash
# Test Ollama directly
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:latest", "prompt": "Hello"}'
```

If fails:
- Check Ollama is running: `docker ps`
- Check logs: `docker logs <ollama-container>`
- Verify model pulled: `docker exec <ollama-container> ollama list`

### GitLab API Errors

```bash
# Test GitLab token
curl -H "PRIVATE-TOKEN: your-token" \
  https://gitlab.example.com/api/v4/projects
```

If fails:
- Verify token has `api` scope
- Check GitLab URL in config
- Verify SSL settings

### Concurrency Not Working

Check:
- `MAX_CONCURRENT_REQUESTS` set correctly
- `get_limiter()` called before agent execution
- `async with self.limiter:` in OllamaClient methods

### Agent Not Found

Check:
- Agent registered in `AgentFactory._agents`
- Agent module imported in factory
- Correct agent name in request

## Performance Tuning

### Ollama Performance

- Use GPU for Ollama (see docker-compose.yml)
- Adjust `num_predict` (max tokens) based on need
- Use smaller models for faster responses: `llama3.2:3b` vs `llama3.2:latest`

### GitLab API

- Increase `per_page` for fewer round trips
- Use `simple=True` for project lists
- Cache frequently accessed data

### Agent Optimization

- Truncate inputs aggressively
- Use `review_depth="quick"` when appropriate
- Limit comment/log fetching

## Next Steps After Implementation

1. **Add More Agents**:
   - Planning agent (project/milestone management)
   - Wiki operations agent
   - Branch management agent

2. **Advanced Features**:
   - Agent chaining workflows
   - Custom prompt templates
   - Multi-model support (GPT-4, Claude)

3. **UI Enhancements**:
   - Rich approval UI with diff preview
   - Agent execution history
   - Configuration dashboard

4. **Integrations**:
   - Slack notifications for approvals
   - Jira synchronization
   - GitHub dual-mode support

## Support

For issues or questions:
1. Check [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) for details
2. Review existing issues in repository
3. Check flock-core documentation
4. Test components individually

---

**Good luck with your implementation!** 🚀
