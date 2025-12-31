# Flock-Core Agent Architecture for GitLab Multi-Agent Tool

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [Agent Specifications](#agent-specifications)
4. [Artifact System](#artifact-system)
5. [Ollama Integration](#ollama-integration)
6. [Agent Implementation](#agent-implementation)
7. [Orchestration Patterns](#orchestration-patterns)
8. [FastAPI Integration](#fastapi-integration)
9. [Human Approval Integration](#human-approval-integration)
10. [Testing Strategy](#testing-strategy)
11. [Deployment Considerations](#deployment-considerations)

---

## Overview

This document describes the flock-core agent architecture for the GitLab multi-agent tool. The system uses specialized agents that communicate via Pydantic artifacts, with Ollama as the LLM provider and strict concurrency control.

### Key Design Goals

- **Modularity**: Each agent is independent and composable
- **Concurrency Control**: Maximum 2 concurrent Ollama requests
- **Type Safety**: Pydantic models for all artifacts and I/O
- **Human Approval**: Critical operations require explicit approval
- **Self-Hosted**: Optimized for on-premise GitLab and Ollama

### Technology Stack

- **Agent Framework**: flock-core (>=0.5.30)
- **API Layer**: FastAPI (>=0.115.0)
- **LLM Provider**: Ollama (self-hosted)
- **Data Validation**: Pydantic (>=2.9.0)
- **API Client**: httpx (async)

---

## Architecture Principles

### 1. Agent Independence

Each agent:
- Has a single, well-defined responsibility
- Can be invoked independently
- Does not maintain state between invocations
- Communicates only through artifacts

### 2. Artifact-Based Communication

- All inter-agent communication uses typed Pydantic artifacts
- Artifacts are immutable once created
- Each artifact has a clear producer and consumer
- Artifacts support serialization for persistence

### 3. Concurrency Management

- Global semaphore limits Ollama requests to 2 concurrent
- Agents queue automatically when limit is reached
- GitLab API requests are not limited (separate from LLM calls)
- Each agent respects the global limiter

### 4. Human-in-the-Loop

Operations requiring approval:
- Creating/modifying files
- Creating/merging merge requests
- Running/canceling pipelines
- Approval requests timeout after configurable duration

---

## Agent Specifications

### 1. Issue Summarization Agent

**Purpose**: Analyze GitLab issues and produce concise summaries

**Input Artifact**:
```python
class IssueSummaryRequest(BaseModel):
    project: str
    issue_iid: int
    include_comments: bool = False
    max_comments: int = 50  # Limit for context window
```

**Output Artifact**:
```python
class IssueSummary(BaseModel):
    issue_iid: int
    project: str
    title: str
    summary: str  # 2-3 sentence overview
    key_points: list[str]  # Bullet points of main topics
    status: str  # "open", "closed"
    priority: Optional[str]  # "low", "medium", "high", "critical"
    complexity: Optional[str]  # "simple", "moderate", "complex"
    stakeholders: list[str]  # Usernames of key participants
    related_issues: list[int]  # Issue IIDs mentioned
    timestamp: datetime
```

**Agent Behavior**:
1. Fetch issue details from GitLab
2. If `include_comments`, fetch and analyze comments
3. Use Ollama to generate summary with prompt engineering
4. Extract key entities (priorities, stakeholders, related issues)
5. Return structured summary artifact

**Prompt Template**:
```
Analyze this GitLab issue and provide a concise summary:

Title: {title}
Description: {description}
Labels: {labels}
Assignees: {assignees}

Comments (if included):
{comments}

Provide:
1. A 2-3 sentence summary
2. 3-5 key points as bullet points
3. Estimated priority (low/medium/high/critical)
4. Estimated complexity (simple/moderate/complex)
5. List any related issue numbers mentioned
```

---

### 2. MR Summarization Agent

**Purpose**: Analyze merge requests including code changes and comments

**Input Artifact**:
```python
class MRSummaryRequest(BaseModel):
    project: str
    mr_iid: int
    include_diff: bool = True
    max_diff_lines: int = 500  # Limit for context
    include_comments: bool = True
```

**Output Artifact**:
```python
class MergeRequestSummary(BaseModel):
    mr_iid: int
    project: str
    title: str
    summary: str  # Overview of MR purpose
    changes_summary: str  # What code changed
    files_changed: list[str]
    additions: int
    deletions: int
    review_status: str  # "approved", "needs_review", "changes_requested"
    recommendations: list[str]  # Action items
    risks: list[str]  # Potential issues identified
    timestamp: datetime
```

**Agent Behavior**:
1. Fetch MR metadata from GitLab
2. If `include_diff`, fetch changes (truncate if too large)
3. Fetch comments and reviews
4. Use Ollama to analyze changes and context
5. Identify risks and recommendations
6. Return structured summary

**Prompt Template**:
```
Analyze this merge request:

Title: {title}
Source: {source_branch} -> {target_branch}
Description: {description}

Code Changes:
{diff_summary}

Review Comments:
{comments}

Provide:
1. Overall purpose and summary (2-3 sentences)
2. Summary of code changes
3. Current review status
4. List of recommendations for reviewers
5. Potential risks or concerns
```

---

### 3. Code Review Agent

**Purpose**: Perform automated code review on merge requests

**Input Artifact**:
```python
class CodeReviewRequest(BaseModel):
    project: str
    mr_iid: int
    review_depth: Literal["quick", "standard", "thorough"] = "standard"
    focus_areas: list[str] = []  # e.g., ["security", "performance"]
    file_patterns: list[str] = []  # Filter to specific files
```

**Output Artifact**:
```python
class CodeReview(BaseModel):
    mr_iid: int
    project: str
    overall_assessment: str
    issues_found: list[CodeIssue]
    suggestions: list[CodeSuggestion]
    approval_recommendation: bool
    review_depth: str
    confidence_score: float  # 0.0-1.0
    timestamp: datetime

class CodeIssue(BaseModel):
    severity: Literal["critical", "high", "medium", "low", "info"]
    category: str  # "security", "bug", "style", "performance"
    file_path: str
    line_number: Optional[int]
    description: str
    recommendation: str

class CodeSuggestion(BaseModel):
    file_path: str
    line_number: Optional[int]
    description: str
    suggested_code: Optional[str]
```

**Agent Behavior**:
1. Fetch MR diff from GitLab
2. Filter files based on patterns if provided
3. Chunk diff into manageable pieces for LLM
4. Analyze for issues based on review depth:
   - **Quick**: Basic syntax, obvious bugs, security
   - **Standard**: Above + code style, best practices
   - **Thorough**: Above + architecture, performance, edge cases
5. Generate structured issues and suggestions
6. Compute confidence score based on completeness
7. Return review artifact

**Prompt Templates by Depth**:

*Quick*:
```
Review this code diff for critical issues only:

{diff_chunk}

Focus on:
- Security vulnerabilities
- Obvious bugs or errors
- Syntax issues

Provide a list of issues with severity and location.
```

*Standard*:
```
Review this code diff:

{diff_chunk}

Check for:
- Security vulnerabilities
- Bugs and logic errors
- Code style and conventions
- Best practices
- Error handling

Provide issues and suggestions with file/line references.
```

*Thorough*:
```
Perform a comprehensive code review:

{diff_chunk}

Context:
- Project: {project}
- Target branch: {target_branch}
- Files changed: {file_count}

Analyze:
- Security vulnerabilities
- Bugs and edge cases
- Architecture and design
- Performance implications
- Code maintainability
- Test coverage gaps
- Documentation needs

Provide detailed issues, suggestions, and overall assessment.
```

---

### 4. Pipeline Triage Agent

**Purpose**: Analyze failed CI/CD pipelines and identify root causes

**Input Artifact**:
```python
class PipelineTriageRequest(BaseModel):
    project: str
    pipeline_id: int
    include_logs: bool = True
    max_log_lines: int = 1000  # Per job
    focus_on_failures: bool = True
```

**Output Artifact**:
```python
class PipelineAnalysis(BaseModel):
    pipeline_id: int
    project: str
    status: str
    ref: str
    failed_jobs: list[JobFailure]
    root_cause: Optional[str]  # Primary cause if identifiable
    recommendations: list[str]
    related_commits: list[str]  # SHAs that may be relevant
    estimated_fix_time: Optional[str]  # "minutes", "hours", "days"
    timestamp: datetime

class JobFailure(BaseModel):
    job_id: int
    job_name: str
    stage: str
    failure_reason: str
    error_messages: list[str]
    log_snippet: str  # Relevant portion of log
    suggested_fix: Optional[str]
```

**Agent Behavior**:
1. Fetch pipeline details from GitLab
2. List all jobs, identify failed ones
3. For each failed job:
   - Fetch logs (truncate if too large)
   - Extract error messages and stack traces
   - Identify failure patterns
4. Use Ollama to analyze failures collectively
5. Determine if failures are related (common root cause)
6. Generate recommendations
7. Return triage artifact

**Prompt Template**:
```
Analyze these CI/CD pipeline failures:

Pipeline #{pipeline_id} on {ref}
Status: {status}

Failed Jobs:
{job_details}

Job Logs:
{log_excerpts}

Determine:
1. Root cause of failures (if common cause exists)
2. Individual failure reasons for each job
3. Recommended fixes for each issue
4. Whether failures are related or independent
5. Estimated time to fix (minutes/hours/days)
6. Any relevant commits that may have introduced issues
```

---

### 5. Repository Operations Agent

**Purpose**: Handle file operations and repository queries

**Input Artifacts**:
```python
class RepoQueryRequest(BaseModel):
    project: str
    operation: Literal["list_tree", "get_file", "search_files", "compare"]
    path: str = ""
    ref: str = "HEAD"
    recursive: bool = False
    query: Optional[str] = None  # For search

class RepoWriteRequest(BaseModel):
    project: str
    operation: Literal["create_file", "update_file", "delete_file"]
    file_path: str
    content: Optional[str] = None
    branch: str
    commit_message: str
    requires_approval: bool = True
```

**Output Artifacts**:
```python
class RepoQueryResult(BaseModel):
    project: str
    operation: str
    results: list[dict]
    summary: str  # LLM-generated summary of results
    timestamp: datetime

class RepoWriteResult(BaseModel):
    project: str
    operation: str
    file_path: str
    branch: str
    commit_sha: Optional[str]
    approval_required: bool
    approval_status: Optional[str]
    timestamp: datetime
```

**Agent Behavior**:

For **Query Operations**:
1. Execute GitLab API call based on operation
2. Process results (filter, format)
3. Use Ollama to generate natural language summary
4. Return result artifact

For **Write Operations**:
1. Validate operation parameters
2. If `requires_approval`, create approval request
3. Wait for approval (with timeout)
4. Execute write operation via GitLab API
5. Return result with commit SHA

**Prompt Template for Summaries**:
```
Summarize these repository query results:

Operation: {operation}
Path: {path}
Ref: {ref}

Results:
{results_json}

Provide a natural language summary suitable for a user.
```

---

## Artifact System

### Artifact Flow Diagram

```
┌──────────────┐
│ FastAPI      │
│ Endpoint     │
└──────┬───────┘
       │ Request
       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Orchestrator │────▶│ Agent 1      │────▶│ GitLabClient │
└──────┬───────┘     └──────┬───────┘     └──────────────┘
       │                    │ Artifact
       │                    ▼
       │             ┌──────────────┐     ┌──────────────┐
       │             │ Ollama       │────▶│ Limiter      │
       │             │ Generator    │     │ (max 2)      │
       │             └──────┬───────┘     └──────────────┘
       │                    │ Response
       │                    ▼
       │             ┌──────────────┐
       │             │ Agent 1      │
       │             └──────┬───────┘
       │                    │ Output Artifact
       ▼                    ▼
┌──────────────────────────────┐
│ Response                      │
│ (Artifact Serialized)         │
└───────────────────────────────┘
```

### Artifact Storage

Flock-core provides artifact persistence via SQLite store:

```python
from flock import Store

store = Store(path=".flock/history.db")

# Store artifact
await store.put_artifact(
    agent_name="issue_summarizer",
    artifact=issue_summary,
    metadata={"project": project, "issue_iid": iid}
)

# Retrieve artifacts
artifacts = await store.get_artifacts(
    agent_name="issue_summarizer",
    filters={"project": project}
)
```

### Artifact Best Practices

1. **Immutability**: Once created, artifacts should not be modified
2. **Timestamps**: Always include creation timestamp
3. **Traceability**: Include source identifiers (issue_iid, mr_iid, etc.)
4. **Versioning**: Consider adding `artifact_version` field for schema evolution
5. **Metadata**: Store additional context in separate metadata dict

---

## Ollama Integration

### Ollama Client Wrapper

Create `gitlab_tool/llm/ollama.py`:

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
        async with self.limiter:  # Acquire semaphore
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                    }
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
                
                data = response.json()
                return data["response"]
    
    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
    ) -> str:
        """Chat completion with concurrency control."""
        async with self.limiter:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                return data["message"]["content"]
```

### Prompt Engineering Guidelines

1. **System Prompts**: Define agent role and constraints
2. **Context Management**: Limit context to fit model window (typically 2048-8192 tokens)
3. **Structured Output**: Request JSON format for easier parsing
4. **Few-Shot Examples**: Include examples for complex tasks
5. **Temperature**:
   - 0.1-0.3 for factual analysis (code review, triage)
   - 0.5-0.7 for summaries
   - 0.7-0.9 for creative suggestions

### Token Management

Create `gitlab_tool/llm/utils.py`:

```python
def estimate_tokens(text: str) -> int:
    """Rough estimation: 1 token ≈ 4 characters."""
    return len(text) // 4

def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to fit token limit."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    
    # Truncate with ellipsis
    return text[:max_chars - 100] + "\n\n[... truncated ...]"

def prepare_diff_for_llm(diff: str, max_tokens: int = 2000) -> str:
    """Prepare diff for LLM consumption."""
    estimated = estimate_tokens(diff)
    
    if estimated <= max_tokens:
        return diff
    
    # Strategy: Keep file headers, truncate large hunks
    lines = diff.split("\n")
    result = []
    current_tokens = 0
    
    for line in lines:
        line_tokens = estimate_tokens(line)
        
        # Always keep file headers
        if line.startswith("diff --git") or line.startswith("+++") or line.startswith("---"):
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

---

## Agent Implementation

### Base Agent Class

Create `gitlab_tool/agents/base.py`:

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

### Example: Issue Summarization Agent

Create `gitlab_tool/agents/issue_summarization.py`:

```python
from datetime import datetime
from typing import Optional
import json
import re
from gitlab_tool.artifacts.gitlab import IssueSummary
from gitlab_tool.artifacts.requests import IssueSummaryRequest
from .base import BaseAgent

class IssueSummarizationAgent(BaseAgent[IssueSummaryRequest, IssueSummary]):
    """Agent for summarizing GitLab issues."""
    
    def name(self) -> str:
        return "issue_summarizer"
    
    def description(self) -> str:
        return "Analyzes GitLab issues and produces concise summaries"
    
    async def execute(self, input_artifact: IssueSummaryRequest) -> IssueSummary:
        """Execute issue summarization."""
        # 1. Fetch issue data
        issue = await self.gitlab.get_issue(
            input_artifact.project,
            input_artifact.issue_iid
        )
        
        # 2. Optionally fetch comments
        comments = []
        if input_artifact.include_comments:
            comments = await self.gitlab.list_issue_notes(
                input_artifact.project,
                input_artifact.issue_iid,
                per_page=input_artifact.max_comments
            )
        
        # 3. Prepare prompt
        prompt = self._build_prompt(issue, comments)
        
        # 4. Call Ollama (respects concurrency limit)
        system_prompt = (
            "You are an expert at analyzing GitLab issues. "
            "Provide concise, structured summaries. "
            "Output must be valid JSON."
        )
        
        response = await self.ollama.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.6
        )
        
        # 5. Parse response and build artifact
        analysis = self._parse_response(response)
        
        return IssueSummary(
            issue_iid=input_artifact.issue_iid,
            project=input_artifact.project,
            title=issue["title"],
            summary=analysis["summary"],
            key_points=analysis["key_points"],
            status=issue["state"],
            priority=analysis.get("priority"),
            complexity=analysis.get("complexity"),
            stakeholders=self._extract_stakeholders(issue, comments),
            related_issues=analysis.get("related_issues", []),
            timestamp=datetime.utcnow()
        )
    
    def _build_prompt(self, issue: dict, comments: list) -> str:
        """Build analysis prompt."""
        prompt_parts = [
            "Analyze this GitLab issue and provide a structured summary.\n",
            f"Title: {issue['title']}\n",
            f"Description:\n{issue.get('description', 'No description')}\n",
            f"Labels: {', '.join(issue.get('labels', []))}\n",
            f"State: {issue['state']}\n",
        ]
        
        if comments:
            prompt_parts.append("\nComments:\n")
            for comment in comments[:10]:  # Limit to recent comments
                author = comment.get("author", {}).get("username", "unknown")
                body = comment.get("body", "")[:500]  # Truncate long comments
                prompt_parts.append(f"- {author}: {body}\n")
        
        prompt_parts.append(
            "\nProvide a JSON response with:\n"
            "{\n"
            '  "summary": "2-3 sentence overview",\n'
            '  "key_points": ["point 1", "point 2", ...],\n'
            '  "priority": "low|medium|high|critical",\n'
            '  "complexity": "simple|moderate|complex",\n'
            '  "related_issues": [123, 456]\n'
            "}\n"
        )
        
        return "".join(prompt_parts)
    
    def _parse_response(self, response: str) -> dict:
        """Parse LLM response."""
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: construct from text
        return {
            "summary": response[:500],
            "key_points": [],
            "priority": None,
            "complexity": None,
            "related_issues": []
        }
    
    def _extract_stakeholders(self, issue: dict, comments: list) -> list[str]:
        """Extract stakeholder usernames."""
        stakeholders = set()
        
        # Author
        if issue.get("author"):
            stakeholders.add(issue["author"]["username"])
        
        # Assignees
        for assignee in issue.get("assignees", []):
            stakeholders.add(assignee["username"])
        
        # Comment authors
        for comment in comments:
            if comment.get("author"):
                stakeholders.add(comment["author"]["username"])
        
        return sorted(stakeholders)
```

### Agent Factory

Create `gitlab_tool/agents/factory.py`:

```python
from typing import Dict, Type
from gitlab_tool.config import Settings
from gitlab_tool.client.gitlab import GitLabClient
from gitlab_tool.llm.ollama import OllamaClient
from .base import BaseAgent
from .issue_summarization import IssueSummarizationAgent

class AgentFactory:
    """Factory for creating agent instances."""
    
    _agents: Dict[str, Type[BaseAgent]] = {
        "issue_summarizer": IssueSummarizationAgent,
        # Other agents will be added here:
        # "mr_summarizer": MRSummarizationAgent,
        # "code_reviewer": CodeReviewAgent,
        # "pipeline_triager": PipelineTriageAgent,
        # "repo_operations": RepositoryOperationsAgent,
    }
    
    @classmethod
    def create(
        cls,
        agent_name: str,
        settings: Settings,
        gitlab_client: GitLabClient,
        ollama_client: OllamaClient,
    ) -> BaseAgent:
        """Create an agent instance."""
        agent_class = cls._agents.get(agent_name)
        if not agent_class:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return agent_class(settings, gitlab_client, ollama_client)
    
    @classmethod
    def list_agents(cls) -> list[str]:
        """List available agent names."""
        return list(cls._agents.keys())
```

---

## Orchestration Patterns

### Pattern 1: Single Agent Invocation

Create `gitlab_tool/orchestration.py`:

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
    
    result = await agent.execute(input_artifact)
    return result
```

### Pattern 2: Sequential Agent Chain

```python
async def agent_chain(
    agents: list[tuple[str, BaseModel]],
    settings: Settings,
) -> list[BaseModel]:
    """Execute agents in sequence."""
    results = []
    gitlab_client = GitLabClient(settings)
    ollama_client = OllamaClient(settings)
    
    for agent_name, input_artifact in agents:
        agent = AgentFactory.create(
            agent_name,
            settings,
            gitlab_client,
            ollama_client
        )
        
        result = await agent.execute(input_artifact)
        results.append(result)
    
    return results
```

### Pattern 3: Parallel Agent Execution

```python
import asyncio

async def parallel_agents(
    tasks: list[tuple[str, BaseModel]],
    settings: Settings,
) -> list[BaseModel]:
    """Execute agents in parallel."""
    gitlab_client = GitLabClient(settings)
    ollama_client = OllamaClient(settings)
    
    async def run_agent(agent_name: str, input_artifact: BaseModel):
        agent = AgentFactory.create(
            agent_name,
            settings,
            gitlab_client,
            ollama_client
        )
        return await agent.execute(input_artifact)
    
    # Create tasks
    coros = [run_agent(name, artifact) for name, artifact in tasks]
    
    # Execute with gather (concurrent but limited by Ollama semaphore)
    results = await asyncio.gather(*coros, return_exceptions=True)
    
    return results
```

### Pattern 4: Human Approval Orchestration

```python
from typing import Optional
from gitlab_tool.utils.approval import get_approval_manager, ApprovalStatus

async def agent_with_approval(
    agent_name: str,
    input_artifact: BaseModel,
    operation_description: str,
    settings: Settings,
) -> tuple[Optional[BaseModel], Optional[str]]:
    """Execute agent with approval gate."""
    approval_manager = get_approval_manager()
    
    # Create approval request
    request = approval_manager.create_request(
        operation=agent_name,
        description=operation_description,
        project=getattr(input_artifact, 'project', 'unknown'),
        details=input_artifact.model_dump()
    )
    
    # Wait for approval
    approved_request = await approval_manager.wait_for_approval(request.request_id)
    
    if approved_request.status != ApprovalStatus.APPROVED:
        return None, f"Operation {approved_request.status.value}"
    
    # Execute agent
    result = await invoke_agent(agent_name, input_artifact, settings)
    return result, None
```

---

## FastAPI Integration

Create `gitlab_tool/main.py`:

```python
from fastapi import FastAPI, HTTPException
from gitlab_tool.artifacts.requests import (
    SummarizeIssueRequest,
    SummarizeMergeRequestRequest,
    ReviewMergeRequestRequest,
    TriagePipelineRequest,
)
from gitlab_tool.config import get_settings
from gitlab_tool.orchestration import invoke_agent
from gitlab_tool.utils.concurrency import get_limiter
from gitlab_tool.utils.approval import get_approval_manager
from gitlab_tool.agents.factory import AgentFactory

app = FastAPI(
    title="GitLab Multi-Agent Tool",
    description="Flock-core powered GitLab automation",
    version="2.0.0"
)

settings = get_settings()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}

@app.get("/api/status")
async def system_status():
    """Get system status including concurrency info."""
    limiter = get_limiter()
    approval_manager = get_approval_manager()
    
    return {
        "ollama": {
            "max_concurrent": limiter.max_concurrent,
            "available_slots": limiter.available,
        },
        "approvals": {
            "pending_count": len(approval_manager.list_pending()),
        },
        "agents": {
            "available": AgentFactory.list_agents(),
        }
    }

@app.post("/api/summarize-issue")
async def summarize_issue(request: SummarizeIssueRequest):
    """Summarize a GitLab issue."""
    try:
        result = await invoke_agent("issue_summarizer", request, settings)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Additional endpoints for other agents will be added similarly
```

---

## Human Approval Integration

### Approval Endpoints

Add to `gitlab_tool/main.py`:

```python
from gitlab_tool.utils.approval import get_approval_manager

@app.get("/api/approvals/pending")
async def list_pending_approvals():
    """List pending approval requests."""
    manager = get_approval_manager()
    pending = manager.list_pending()
    return [req.model_dump() for req in pending]

@app.get("/api/approvals/{request_id}")
async def get_approval(request_id: str):
    """Get approval request details."""
    manager = get_approval_manager()
    request = manager.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request.model_dump()

@app.post("/api/approvals/{request_id}/approve")
async def approve_request(request_id: str):
    """Approve an operation."""
    manager = get_approval_manager()
    try:
        request = manager.approve(request_id)
        return request.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/approvals/{request_id}/reject")
async def reject_request(request_id: str, reason: str = None):
    """Reject an operation."""
    manager = get_approval_manager()
    try:
        request = manager.reject(request_id, reason)
        return request.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

---

## Testing Strategy

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── agents/
│   ├── __init__.py
│   ├── test_issue_summarization.py
│   ├── test_mr_summarization.py
│   ├── test_code_review.py
│   ├── test_pipeline_triage.py
│   └── test_repository_operations.py
├── integration/
│   ├── __init__.py
│   └── test_orchestration.py
├── load/
│   ├── __init__.py
│   └── test_concurrency.py
└── test_approval.py
```

### Example Test

Create `tests/agents/test_issue_summarization.py`:

```python
import pytest
from unittest.mock import AsyncMock
from gitlab_tool.agents.issue_summarization import IssueSummarizationAgent
from gitlab_tool.artifacts.requests import IssueSummaryRequest

@pytest.fixture
def mock_gitlab_client():
    client = AsyncMock()
    client.get_issue.return_value = {
        "id": 1,
        "iid": 42,
        "title": "Test Issue",
        "description": "Test description",
        "state": "opened",
        "labels": ["bug"],
        "author": {"username": "alice"},
        "assignees": [{"username": "bob"}],
    }
    client.list_issue_notes.return_value = []
    return client

@pytest.fixture
def mock_ollama_client():
    client = AsyncMock()
    client.generate.return_value = '''
    {
        "summary": "This is a test issue summary",
        "key_points": ["Point 1", "Point 2"],
        "priority": "high",
        "complexity": "moderate"
    }
    '''
    return client

@pytest.mark.asyncio
async def test_issue_summarization_agent(
    mock_gitlab_client,
    mock_ollama_client,
    test_settings
):
    agent = IssueSummarizationAgent(
        test_settings,
        mock_gitlab_client,
        mock_ollama_client
    )
    
    request = IssueSummaryRequest(
        project="test/project",
        issue_iid=42,
        include_comments=False
    )
    
    result = await agent.execute(request)
    
    assert result.issue_iid == 42
    assert result.project == "test/project"
    assert result.title == "Test Issue"
    assert len(result.key_points) == 2
    assert result.priority == "high"
```

---

## Deployment Considerations

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  gitlab-tool:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITLAB_URL=${GITLAB_URL}
      - GITLAB_TOKEN=${GITLAB_TOKEN}
      - OLLAMA_BASE_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3.2:latest
      - MAX_CONCURRENT_REQUESTS=2
    volumes:
      - ./.flock:/app/.flock
    depends_on:
      - ollama
  
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

volumes:
  ollama_data:
```

### Environment Configuration

Create `.env.example`:

```env
# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=glpat-xxxxxxxxxxxxx
GITLAB_VERIFY_SSL=true
GITLAB_TIMEOUT=30

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
OLLAMA_TIMEOUT=120

# Server Configuration
HOST=0.0.0.0
PORT=8000
MAX_CONCURRENT_REQUESTS=2

# Human Approval
REQUIRE_APPROVAL_FOR_WRITES=true
APPROVAL_TIMEOUT_SECONDS=300

# Flock Configuration
FLOCK_STORE_PATH=.flock/history.db
FLOCK_LOG_LEVEL=INFO
```

---

## Best Practices Summary

### Agent Design
- ✅ Keep agents focused on single responsibility
- ✅ Use Pydantic for all I/O validation
- ✅ Implement comprehensive error handling
- ✅ Respect Ollama concurrency limits
- ✅ Truncate inputs to fit model context window

### Prompt Engineering
- ✅ Use system prompts to define agent role
- ✅ Request structured output (JSON)
- ✅ Include few-shot examples for complex tasks
- ✅ Adjust temperature based on task type
- ✅ Validate and sanitize LLM outputs

### Security
- ✅ Require approval for all write operations
- ✅ Validate all GitLab API inputs
- ✅ Don't log sensitive data (tokens, secrets)
- ✅ Implement rate limiting
- ✅ Use HTTPS for production

### Performance
- ✅ Limit concurrent Ollama requests (max 2)
- ✅ Cache GitLab API responses when possible
- ✅ Truncate large inputs (diffs, logs)
- ✅ Use async/await throughout
- ✅ Monitor queue depths and latencies

---

## Implementation Checklist

### Phase 1: Core Implementation (Week 1-2)
- [ ] Create base agent class structure
- [ ] Implement OllamaClient with concurrency control
- [ ] Implement Issue Summarization Agent
- [ ] Add FastAPI endpoints for issue summarization
- [ ] Write unit tests
- [ ] Update artifact models

### Phase 2: Additional Agents (Week 3-4)
- [ ] Implement MR Summarization Agent
- [ ] Implement Code Review Agent
- [ ] Implement Pipeline Triage Agent
- [ ] Implement Repository Operations Agent
- [ ] Add comprehensive tests

### Phase 3: Orchestration (Week 5)
- [ ] Implement orchestration patterns
- [ ] Add human approval workflow
- [ ] Create approval UI
- [ ] Integration testing

### Phase 4: Production Readiness (Week 6)
- [ ] Add monitoring and metrics
- [ ] Create Docker Compose setup
- [ ] Write deployment documentation
- [ ] Load testing and optimization
- [ ] Security audit

---

## References

- [flock-core Documentation](https://github.com/whiteducksoftware/flock)
- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [Ollama API Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-31  
**Status**: Implementation Plan
