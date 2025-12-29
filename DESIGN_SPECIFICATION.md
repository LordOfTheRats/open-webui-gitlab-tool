# GitLab Tool for Open WebUI - Design Specification

**Version:** 1.8.0  
**Author:** René Vögeli  
**License:** MIT  
**Last Updated:** 2025-12-29

---

## 1. Overview

### 1.1 Purpose

The GitLab Tool is an Open WebUI integration that provides comprehensive access to GitLab instances (self-hosted or cloud). It enables AI assistants to interact with GitLab projects, issues, merge requests, repository files, and CI/CD pipelines through natural language commands.

### 1.2 Key Features

- **Project Management**: List and retrieve GitLab projects with filtering capabilities
- **Issue Tracking**: Full CRUD operations on issues including labels, milestones, assignees, time tracking, and comments
- **Merge Request Operations**: Create, list, approve, merge, and comment on merge requests
- **Repository Access**: Browse repository trees, read files (raw and base64), compare branches, and view diffs
- **Repository Writes**: Optional controlled write operations (create/update/delete/move/chmod files)
- **CI/CD Control**: List and monitor pipelines, view job logs, trigger pipelines, retry/cancel jobs
- **Helper Endpoints**: Search users, list labels, milestones, and project members
- **Compact Mode**: Configurable output mode to reduce response size while preserving essential information
- **Reliability Features**: Automatic retry logic with exponential backoff, rate limit handling, and jitter

### 1.3 Target Use Cases

- Project management automation through AI assistants
- Code review assistance
- Issue triage and management
- CI/CD monitoring and control
- Repository exploration and documentation generation
- Automated merge request workflows

---

## 2. Architecture

### 2.1 Design Patterns

#### 2.1.1 Open WebUI Toolkit Pattern

The tool follows Open WebUI's toolkit architecture:

```python
class Tools:
    def __init__(self):
        self.valves = self.Valves()
    
    class Valves(BaseModel):
        # Configuration parameters
        pass
```

All public methods are exposed as callable tools to the AI assistant.

#### 2.1.2 Async/Await Pattern

All API interactions use Python's async/await pattern for non-blocking I/O operations:

```python
async def gitlab_list_projects(...) -> list[Json]:
    data = await self._paginate("/projects", ...)
    return self._maybe_compact("project", data, compact)
```

#### 2.1.3 Type Safety

Strong typing throughout using:
- Type hints for all parameters and return values
- Pydantic models for configuration validation
- Type aliases for common patterns (`Json`, `ProjectRef`, `GroupRef`)
- Literal types for enumerated values

#### 2.1.4 Safety-First Design

- **Opt-in Write Operations**: Repository writes require explicit valve configuration
- **Input Validation**: All user inputs validated before API calls
- **Error Boundaries**: Comprehensive error handling with detailed messages
- **SSL Verification**: Enabled by default with opt-out for development environments

### 2.2 Core Components

#### 2.2.1 Configuration System (Valves)

The `Valves` class provides type-safe configuration:

| Parameter | Type | Default | Purpose |
|-----------|------|---------|---------|
| `base_url` | str | "https://gitlab.example.com" | GitLab instance URL |
| `token` | str | "" | Personal Access Token (PAT) |
| `verify_ssl` | bool | True | TLS certificate verification |
| `timeout_seconds` | float | 30.0 | HTTP request timeout |
| `per_page` | int | 20 | Default pagination size |
| `allow_repo_writes` | bool | False | Enable repository write operations |
| `compact_results_default` | bool | True | Default compact mode setting |
| `max_retries` | int | 3 | Maximum retry attempts |
| `backoff_initial_seconds` | float | 0.8 | Initial retry delay |
| `backoff_max_seconds` | float | 10.0 | Maximum retry delay |
| `retry_jitter` | float | 0.2 | Jitter proportion for retry delays |

#### 2.2.2 HTTP Client Layer

**Request Handler** (`_request`):
- Automatic retry logic for transient failures (429, 502, 503, 504, timeouts)
- Exponential backoff with configurable jitter
- Respect for `Retry-After` headers
- Support for both JSON and text responses
- Custom accept headers for specific endpoints

**Pagination Handler** (`_paginate`):
- Zero-based offset pagination
- Configurable page count
- Automatic detection of end-of-list
- GitLab API compliant (page=1 based)

#### 2.2.3 Data Transformation Layer

**Compact Mode System**:
- Reduces response payload size while preserving critical information
- Different compact schemas per entity type
- Never removes description fields (issues/MRs) or body fields (notes)
- Configurable per-request or globally

**Entity Types with Compact Support**:
- Projects
- Issues
- Merge Requests
- Pipelines
- Jobs
- Labels
- Milestones
- Members/Users
- Notes/Comments

#### 2.2.4 Authentication & Authorization

- **Authentication**: Personal Access Token via `PRIVATE-TOKEN` header
- **Required Scope**: `api` scope minimum
- **Write Operations**: Additional safety valve (`allow_repo_writes`)

---

## 3. API Surface

### 3.1 Project Operations

#### 3.1.1 List Projects
```python
async def gitlab_list_projects(
    search: Optional[str] = None,
    membership: bool = True,
    owned: bool = False,
    starred: bool = False,
    simple: bool = True,
    visibility: Optional[Literal["private", "internal", "public"]] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Purpose**: Discover and list projects with flexible filtering.

**Key Parameters**:
- `search`: Substring filter for project name/path
- `membership`: Limit to member projects
- `owned`: Limit to owned projects
- `visibility`: Filter by access level

**Compact Fields**: id, name, path_with_namespace, description, visibility, archived, default_branch, last_activity_at, web_url

#### 3.1.2 Get Project
```python
async def gitlab_get_project(
    project: ProjectRef,
    compact: Optional[bool] = None
) -> Json
```

**Purpose**: Retrieve detailed information about a single project.

### 3.2 Issue Operations

#### 3.2.1 List Issues
```python
async def gitlab_list_issues(
    project: ProjectRef,
    state: Optional[Literal["opened", "closed", "all"]] = "opened",
    labels: Optional[str] = None,
    assignee_username: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Purpose**: Query issues with filtering and search.

**Compact Fields**: id, iid, title, description (preserved), state, labels, author, assignee, assignees, milestone, time_stats, created_at, updated_at, due_date, web_url

#### 3.2.2 Get Issue
```python
async def gitlab_get_issue(
    project: ProjectRef,
    issue_iid: int,
    compact: Optional[bool] = None
) -> Json
```

**Purpose**: Retrieve a single issue by IID.

#### 3.2.3 Create Issue
```python
async def gitlab_create_issue(
    project: ProjectRef,
    title: str,
    description: Optional[str] = None,
    labels: Optional[str] = None,
    assignee_id: Optional[int] = None,
    milestone_id: Optional[int] = None,
    due_date: Optional[str] = None,
    compact: Optional[bool] = None,
) -> Json
```

**Purpose**: Create new issues programmatically.

**Note**: Uses single assignee model (`assignee_id`). For multiple assignees, GitLab API supports it but tool enforces single assignee for simplicity.

#### 3.2.4 Update Issue
```python
async def gitlab_update_issue(
    project: ProjectRef,
    issue_iid: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    assignee_id: Optional[int] = None,
    unassign: bool = False,
    labels: Optional[str] = None,
    add_labels: Optional[str] = None,
    remove_labels: Optional[str] = None,
    due_date: Optional[str] = None,
    clear_due_date: bool = False,
    milestone_id: Optional[int] = None,
    compact: Optional[bool] = None,
) -> Json
```

**Purpose**: Flexible issue updates with granular control.

**Label Management**:
- `labels`: Replace all labels
- `add_labels`: Add labels incrementally
- `remove_labels`: Remove labels incrementally

#### 3.2.5 Specialized Update Methods

**Set Issue Description**:
```python
async def gitlab_set_issue_description(
    project: ProjectRef,
    issue_iid: int,
    description: str,
    compact: Optional[bool] = None,
) -> Json
```

**Set Assignee**:
```python
async def gitlab_set_issue_assignee(
    project: ProjectRef,
    issue_iid: int,
    assignee_id: Optional[int],
    compact: Optional[bool] = None,
) -> Json
```

**Label Operations**:
```python
async def gitlab_add_issue_labels(...)
async def gitlab_remove_issue_labels(...)
async def gitlab_set_issue_labels(...)
```

**Due Date**:
```python
async def gitlab_set_issue_due_date(
    project: ProjectRef,
    issue_iid: int,
    due_date: Optional[str],  # "YYYY-MM-DD" or None
    compact: Optional[bool] = None,
) -> Json
```

#### 3.2.6 Time Tracking

**Set Time Estimate**:
```python
async def gitlab_set_issue_time_estimate(
    project: ProjectRef,
    issue_iid: int,
    duration: str,  # e.g., "1h", "30m", "2d 3h"
) -> Json
```

**Add Spent Time**:
```python
async def gitlab_add_issue_spent_time(
    project: ProjectRef,
    issue_iid: int,
    duration: str,
) -> Json
```

**Reset Operations**:
```python
async def gitlab_reset_issue_time_estimate(...)
async def gitlab_reset_issue_spent_time(...)
```

#### 3.2.7 Issue Comments

**Add Comment**:
```python
async def gitlab_add_issue_note(
    project: ProjectRef,
    issue_iid: int,
    body: str,  # Markdown supported
) -> Json
```

**List Comments**:
```python
async def gitlab_list_issue_notes(
    project: ProjectRef,
    issue_iid: int,
    sort: Optional[Literal["asc", "desc"]] = "asc",
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, body (preserved), author, created_at, updated_at, system, type

#### 3.2.8 Close Issue
```python
async def gitlab_close_issue(
    project: ProjectRef,
    issue_iid: int,
    compact: Optional[bool] = None,
) -> Json
```

### 3.3 Merge Request Operations

#### 3.3.1 List Merge Requests
```python
async def gitlab_list_merge_requests(
    project: ProjectRef,
    state: Optional[Literal["opened", "closed", "locked", "merged", "all"]] = "opened",
    source_branch: Optional[str] = None,
    target_branch: Optional[str] = None,
    search: Optional[str] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, iid, title, description (preserved), state, source_branch, target_branch, author, assignees, reviewers, created_at, updated_at, merged_at, web_url

#### 3.3.2 Get Merge Request
```python
async def gitlab_get_merge_request(
    project: ProjectRef,
    mr_iid: int,
    compact: Optional[bool] = None
) -> Json
```

#### 3.3.3 Create Merge Request
```python
async def gitlab_create_merge_request(
    project: ProjectRef,
    source_branch: str,
    target_branch: str,
    title: str,
    description: Optional[str] = None,
    remove_source_branch: bool = False,
    squash: Optional[bool] = None,
    draft: bool = False,
    compact: Optional[bool] = None,
) -> Json
```

**Draft Handling**: If `draft=True`, tool automatically prefixes title with "Draft: " if not already present.

#### 3.3.4 Approve Merge Request
```python
async def gitlab_approve_merge_request(
    project: ProjectRef,
    mr_iid: int,
    sha: Optional[str] = None,  # Optional SHA pinning
) -> Json
```

#### 3.3.5 Merge Merge Request
```python
async def gitlab_merge_merge_request(
    project: ProjectRef,
    mr_iid: int,
    merge_commit_message: Optional[str] = None,
    squash_commit_message: Optional[str] = None,
    should_remove_source_branch: Optional[bool] = None,
    squash: Optional[bool] = None,
    compact: Optional[bool] = None,
) -> Json
```

#### 3.3.6 MR Comments
```python
async def gitlab_add_mr_note(...)
async def gitlab_list_mr_notes(...)
```

Similar to issue comments with same compact behavior.

### 3.4 Repository Operations

#### 3.4.1 Browse Repository
```python
async def gitlab_list_repository_tree(
    project: ProjectRef,
    path: str = "",  # "" for root
    ref: Optional[str] = None,  # Branch/tag/commit
    recursive: bool = False,
    offset: int = 0,
    page_count: int = 1,
) -> list[Json]
```

**Purpose**: Navigate repository file structure.

#### 3.4.2 Read Files

**Get File Metadata + Base64 Content**:
```python
async def gitlab_get_file(
    project: ProjectRef,
    file_path: str,
    ref: str = "HEAD"
) -> Json
```

**Get Raw File Content**:
```python
async def gitlab_get_raw_file(
    project: ProjectRef,
    file_path: str,
    ref: str = "HEAD"
) -> str
```

**Purpose**: Direct text access to file contents, useful for code analysis.

#### 3.4.3 Compare Branches
```python
async def gitlab_compare(
    project: ProjectRef,
    from_ref: str,
    to_ref: str,
    straight: bool = False
) -> Json
```

**Purpose**: View diffs between branches, tags, or commits.

#### 3.4.4 Repository Write Operations

**⚠️ All write operations require `allow_repo_writes=True` in Valves.**

**Create or Update File**:
```python
async def gitlab_create_or_update_file(
    project: ProjectRef,
    branch: str,
    file_path: str,
    content: str,
    commit_message: str,
    encoding: Literal["text", "base64"] = "text",
    start_branch: Optional[str] = None,
    execute_filemode: Optional[bool] = None,
) -> Json
```

**Design**: Automatically detects if file exists and uses appropriate action (create/update).

**Delete File**:
```python
async def gitlab_delete_file(
    project: ProjectRef,
    branch: str,
    file_path: str,
    commit_message: str,
    start_branch: Optional[str] = None,
) -> Json
```

**Move/Rename File**:
```python
async def gitlab_move_file(
    project: ProjectRef,
    branch: str,
    file_path: str,  # New path
    previous_path: str,  # Old path
    commit_message: str,
    start_branch: Optional[str] = None,
) -> Json
```

**Change File Permissions**:
```python
async def gitlab_chmod_file(
    project: ProjectRef,
    branch: str,
    file_path: str,
    execute_filemode: bool,
    commit_message: str,
    start_branch: Optional[str] = None,
) -> Json
```

**Advanced Multi-Action Commit**:
```python
async def gitlab_create_commit(
    project: ProjectRef,
    branch: str,
    commit_message: str,
    actions: list[Json],  # GitLab commit actions
    start_branch: Optional[str] = None,
    author_email: Optional[str] = None,
    author_name: Optional[str] = None,
) -> Json
```

**Purpose**: Atomic multi-file operations in a single commit.

**Action Types**:
- `create`: Create new file
- `update`: Update existing file
- `delete`: Remove file
- `move`: Rename/move file
- `chmod`: Change executable bit

### 3.5 CI/CD Operations

#### 3.5.1 List Pipelines
```python
async def gitlab_list_pipelines(
    project: ProjectRef,
    ref: Optional[str] = None,
    status: Optional[Literal[
        "created", "waiting_for_resource", "preparing", "pending",
        "running", "success", "failed", "canceled", "skipped",
        "manual", "scheduled"
    ]] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, iid, status, ref, sha, created_at, updated_at, web_url

#### 3.5.2 Get Pipeline
```python
async def gitlab_get_pipeline(
    project: ProjectRef,
    pipeline_id: int,
    compact: Optional[bool] = None
) -> Json
```

#### 3.5.3 List Pipeline Jobs
```python
async def gitlab_list_pipeline_jobs(
    project: ProjectRef,
    pipeline_id: int,
    scope: Optional[Literal[
        "created", "pending", "running", "failed",
        "success", "canceled", "skipped", "manual"
    ]] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, name, stage, status, ref, created_at, started_at, finished_at, web_url

#### 3.5.4 Get Job Trace/Log
```python
async def gitlab_get_job_trace(
    project: ProjectRef,
    job_id: int
) -> str
```

**Purpose**: Retrieve plain text job logs for debugging.

#### 3.5.5 Pipeline Control

**Trigger Pipeline**:
```python
async def gitlab_run_pipeline(
    project: ProjectRef,
    ref: str,  # Branch/tag to run on
    variables: Optional[dict[str, str]] = None,
    compact: Optional[bool] = None,
) -> Json
```

**Retry Job**:
```python
async def gitlab_retry_job(
    project: ProjectRef,
    job_id: int,
    compact: Optional[bool] = None,
) -> Json
```

**Cancel Job**:
```python
async def gitlab_cancel_job(
    project: ProjectRef,
    job_id: int,
    compact: Optional[bool] = None,
) -> Json
```

### 3.6 Helper Lookup Endpoints

#### 3.6.1 List Labels
```python
async def gitlab_list_labels(
    project: ProjectRef,
    search: Optional[str] = None,
    include_ancestor_groups: bool = True,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, name, description (preserved), color, text_color

#### 3.6.2 List Milestones

**Project Milestones**:
```python
async def gitlab_list_milestones(
    project: ProjectRef,
    state: Optional[Literal["active", "closed", "all"]] = "active",
    search: Optional[str] = None,
    exclude_group_milestones: bool = False,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Group Milestones**:
```python
async def gitlab_list_group_milestones(
    group: GroupRef,
    state: Optional[Literal["active", "closed", "all"]] = "active",
    search: Optional[str] = None,
    include_subgroups: bool = True,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, iid, title, description (preserved), state, due_date, start_date, web_url

#### 3.6.3 Search Users
```python
async def gitlab_search_users(
    search: str,
    active: Optional[bool] = None,
    external: Optional[bool] = None,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Purpose**: Resolve display names/emails to GitLab user IDs and usernames.

**Compact Fields**: id, username, name, state, web_url

#### 3.6.4 List Project Members
```python
async def gitlab_list_project_members(
    project: ProjectRef,
    query: Optional[str] = None,
    include_inherited: bool = True,
    offset: int = 0,
    page_count: int = 1,
    compact: Optional[bool] = None,
) -> list[Json]
```

**Compact Fields**: id, username, name, state, access_level, web_url

---

## 4. Data Models

### 4.1 Type Aliases

```python
Json = dict[str, Any]
ProjectRef = Union[int, str]  # Numeric ID or "group/subgroup/project"
GroupRef = Union[int, str]    # Numeric ID or "group/subgroup"
```

### 4.2 Project Reference Handling

The tool supports flexible project identification:

1. **Numeric ID**: `12345`
2. **Full Path**: `"mygroup/subgroup/project"`

When using paths, the tool automatically URL-encodes them (e.g., slashes become `%2F`).

**Implementation**:
```python
def _project_id_or_path(self, project: ProjectRef) -> str:
    if isinstance(project, int):
        return str(project)
    return self._encode_path(project)
```

### 4.3 Compact Mode Schemas

Each entity type has a specific compact schema:

**Project**: Essential metadata + description
**Issue/MR**: Core fields + description (never removed) + assignees + dates
**Note**: Body (never removed) + author + timestamps
**Pipeline/Job**: Status + identifiers + timestamps
**Label**: Name + description (never removed) + colors
**Milestone**: Title + description (never removed) + dates

---

## 5. Reliability & Error Handling

### 5.1 Retry Strategy

**Retryable Conditions**:
- HTTP 429 (Rate Limited)
- HTTP 502, 503, 504 (Gateway/Service errors)
- Connection timeouts
- Read timeouts
- Pool timeouts
- Connection errors

**Backoff Algorithm**:
```python
def _compute_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
    if retry_after is not None and retry_after > 0:
        base = float(retry_after)
    else:
        base = backoff_initial_seconds * (2 ** (attempt - 1))
    
    base = min(base, backoff_max_seconds)
    
    if retry_jitter > 0:
        delta = base * retry_jitter
        base = base + random.uniform(-delta, delta)
    
    return max(0.0, base)
```

**Features**:
- Exponential backoff (2^n)
- Respects `Retry-After` header
- Configurable maximum delay
- Jitter to prevent thundering herd
- Configurable retry count

### 5.2 Error Messages

All errors include:
- HTTP status code
- Request method and path
- Detailed error response from GitLab

**Example**:
```
GitLab API error 404 for GET /projects/123/issues/456: {"message": "404 Not Found"}
```

### 5.3 Safety Mechanisms

**Write Protection**:
```python
def _ensure_writes_allowed(self) -> None:
    if not self.valves.allow_repo_writes:
        raise PermissionError(
            "Repository write operations are disabled. "
            "Set Valves.allow_repo_writes=true to enable."
        )
```

**Token Validation**:
```python
def _headers(self) -> dict[str, str]:
    if not self.valves.token:
        raise ValueError(
            "GitLab token is not set. Configure the tool Valves: token=..."
        )
    return {"PRIVATE-TOKEN": self.valves.token, ...}
```

---

## 6. Pagination System

### 6.1 Design Philosophy

- **Zero-based offset**: Aligned with common programming patterns
- **Configurable page count**: Fetch multiple pages in one call
- **Automatic termination**: Stops when GitLab returns fewer items than requested

### 6.2 Implementation

```python
async def _paginate(
    self,
    path: str,
    params: Optional[dict[str, Any]] = None,
    offset: int = 0,      # 0-based
    page_count: int = 1,
) -> list[Any]:
    params = dict(params or {})
    params.setdefault("per_page", self.valves.per_page)
    
    start_page = offset + 1  # GitLab uses 1-based pages
    end_page = start_page + page_count - 1
    
    out: list[Any] = []
    for page in range(start_page, end_page + 1):
        params["page"] = page
        chunk = await self._request("GET", path, params=params)
        
        if not isinstance(chunk, list):
            return [chunk]
        
        out.extend(chunk)
        
        if len(chunk) < int(params["per_page"]):
            break  # Reached end of list
    
    return out
```

### 6.3 Usage Example

```python
# Fetch pages 3-5 (0-based offset 2, count 3)
issues = await gitlab_list_issues(
    project="mygroup/project",
    offset=2,
    page_count=3
)
```

---

## 7. Security Considerations

### 7.1 Authentication

**Token Storage**:
- Stored in Valves configuration
- Not logged or exposed in error messages
- Transmitted via `PRIVATE-TOKEN` header

**Required Scopes**:
- Minimum: `api` scope
- Write operations: Same `api` scope (controlled by safety valve)

### 7.2 Write Operation Safety

**Two-Layer Protection**:
1. **Configuration Check**: `allow_repo_writes` valve must be `True`
2. **Method Gating**: All write methods call `_ensure_writes_allowed()`

**Design Rationale**:
- Prevents accidental repository modifications
- Explicit opt-in required
- Separate from authentication

### 7.3 SSL/TLS

**Default**: Certificate verification enabled
**Override**: `verify_ssl=False` for development/self-signed certificates
**Warning**: Only disable for trusted internal environments

### 7.4 Input Validation

**Path Encoding**:
- All file paths URL-encoded
- Prevents path traversal attempts
- Handles special characters correctly

**Type Validation**:
- Pydantic models for configuration
- Type hints enforce correct usage
- Literal types for enumerations

---

## 8. Extension Points

### 8.1 Adding New Endpoints

**Pattern**:
```python
async def gitlab_new_operation(
    self,
    project: ProjectRef,
    # ... parameters ...
    compact: Optional[bool] = None,
) -> Union[Json, list[Json]]:
    """
    Brief description.
    
    Args:
      project: Numeric project ID or "group/subgroup/project" path.
      # ... parameter docs ...
      compact: If true, tool returns a reduced field set.
    """
    pid = self._project_id_or_path(project)
    data = await self._request("METHOD", f"/projects/{pid}/endpoint")
    return self._maybe_compact("entity_type", data, compact)
```

### 8.2 Adding Compact Schemas

**Pattern**:
```python
def _compact_one(self, kind: str, obj: Any) -> Any:
    # ... existing cases ...
    
    if kind == "new_entity":
        return {
            "id": obj.get("id"),
            # Essential fields only
            "description": obj.get("description"),  # Keep if important
        }
    
    return obj
```

### 8.3 Custom Retry Logic

**Override Computation**:
```python
def _compute_delay(self, attempt: int, retry_after: Optional[float] = None) -> float:
    # Custom backoff algorithm
    pass
```

---

## 9. Integration Patterns

### 9.1 Open WebUI Usage

**Tool Registration**:
The tool is automatically discovered by Open WebUI when placed in the tools directory.

**Configuration**:
Users configure Valves through Open WebUI's admin interface:
1. Navigate to Tools settings
2. Find "GitLab (Self-hosted)"
3. Configure `base_url` and `token`
4. Optionally enable `allow_repo_writes`

**Invocation**:
AI assistants invoke methods through natural language:
- "List all open issues in mygroup/project"
- "Create a merge request from feature-branch to main"
- "Show me the CI pipeline status"

### 9.2 Workflow Examples

**Issue Triage Workflow**:
1. `gitlab_list_issues(state="opened")` - Get open issues
2. `gitlab_search_users(search="John")` - Find assignee
3. `gitlab_set_issue_assignee(assignee_id=user_id)` - Assign issue
4. `gitlab_add_issue_labels(labels="bug,priority:high")` - Tag issue

**Code Review Workflow**:
1. `gitlab_list_merge_requests(state="opened")` - Get pending MRs
2. `gitlab_get_merge_request(mr_iid=42)` - Get MR details
3. `gitlab_list_mr_notes(mr_iid=42)` - Review comments
4. `gitlab_add_mr_note(body="LGTM!")` - Add review comment
5. `gitlab_approve_merge_request(mr_iid=42)` - Approve

**CI Monitoring Workflow**:
1. `gitlab_list_pipelines(status="running")` - Get active pipelines
2. `gitlab_list_pipeline_jobs(pipeline_id=123)` - Get job details
3. `gitlab_get_job_trace(job_id=456)` - Fetch logs
4. `gitlab_retry_job(job_id=456)` - Retry if needed

---

## 10. Performance Characteristics

### 10.1 Request Overhead

**Per Request**:
- HTTP overhead: ~50-200ms (network dependent)
- TLS handshake: ~100-300ms (first request only, connection pooling)
- GitLab processing: Variable (simple queries <100ms, complex >1s)

**Retry Overhead**:
- Initial backoff: 0.8s (configurable)
- Maximum backoff: 10s (configurable)
- Total maximum: ~30s for 3 retries with max backoff

### 10.2 Pagination Performance

**Trade-offs**:
- Smaller `per_page`: More requests, lower memory, more responsive
- Larger `per_page`: Fewer requests, higher memory, longer first response

**Recommendation**:
- Default 20 items: Good balance
- Large lists (>100 items): Consider fetching multiple pages
- Real-time updates: Use `page_count=1` with polling

### 10.3 Compact Mode Impact

**Bandwidth Reduction**:
- Typical reduction: 40-70% of response size
- Projects: ~50% reduction
- Issues: ~60% reduction (with description preserved)
- Pipelines: ~70% reduction

**CPU Overhead**:
- Negligible (<1ms per entity)
- Dictionary filtering is O(n) where n = number of fields

---

## 11. Testing Strategy

### 11.1 Recommended Test Coverage

**Unit Tests** (Internal Methods):
- `_encode_path`: URL encoding correctness
- `_project_id_or_path`: Type conversion
- `_compute_delay`: Backoff calculation
- `_compact_one`: Schema correctness
- `_maybe_compact`: Mode selection

**Integration Tests** (With Mock GitLab API):
- Pagination edge cases (empty list, single page, multiple pages)
- Retry logic (429 handling, timeout handling)
- Error handling (4xx, 5xx responses)
- Authentication (missing token, invalid token)

**End-to-End Tests** (With Real GitLab Instance):
- Full workflow tests (create issue → comment → close)
- Write operations (if enabled)
- Search and filtering
- CI/CD operations

### 11.2 Test Environment Setup

**Requirements**:
- GitLab instance (can be local docker container)
- Test project with:
  - Sample issues
  - Sample merge requests
  - CI/CD configured
  - Multiple branches
- Personal Access Token with `api` scope

**Recommended Tools**:
- `pytest` for test framework
- `pytest-asyncio` for async test support
- `respx` for HTTP mocking
- `docker` for local GitLab instance

---

## 12. Deployment Considerations

### 12.1 Open WebUI Integration

**Installation**:
1. Copy `gitlab.py` to Open WebUI tools directory
2. Restart Open WebUI
3. Configure through admin UI

**Configuration Management**:
- Valves are stored in Open WebUI's database
- Per-user or global configuration possible
- Credentials never exposed to end users

### 12.2 Resource Requirements

**Memory**:
- Base: ~10MB (Python process)
- Per request: ~1-5MB (depending on payload size)
- Concurrent requests: Linear scaling

**Network**:
- Outbound HTTPS to GitLab instance required
- Typical bandwidth: 1-10 KB/request (without large files)
- Keep-alive connections reduce overhead

### 12.3 GitLab Server Requirements

**Versions**:
- Minimum: GitLab 12.0+ (API v4)
- Recommended: GitLab 15.0+ (latest features)
- Tested: GitLab 16.x

**API Rate Limits**:
- Default: 600 requests/minute per user
- Tool respects rate limits with automatic retry
- Consider increasing limits for heavy automation

---

## 13. Known Limitations

### 13.1 Current Limitations

1. **Single Assignee Model**: While GitLab supports multiple assignees, the tool enforces single assignee for simplicity in issue creation/updates
2. **No Binary File Support**: Repository operations handle text and base64, but large binary files may cause issues
3. **No Wiki Operations**: GitLab wiki API not yet implemented
4. **No Group-Level Issue Operations**: Only project-scoped issue operations
5. **No Epic Support**: GitLab premium feature not implemented
6. **No Discussions API**: Only basic notes/comments supported
7. **No Packages/Container Registry**: Package operations not implemented

### 13.2 Future Enhancement Opportunities

1. **Multiple Assignee Support**: Extend issue/MR operations to support assignee lists
2. **Wiki Operations**: Add wiki page CRUD operations
3. **Group Operations**: Extend to group-level issues and epics
4. **Advanced Search**: Implement GitLab's advanced search API
5. **GraphQL API**: Alternative to REST for complex queries
6. **Webhooks**: Setup/management of webhook integrations
7. **Project Settings**: Read/modify project configuration
8. **Branch Protection**: Manage protected branches
9. **Access Control**: Manage project members and permissions
10. **Releases**: Create and manage project releases

---

## 14. Maintenance Guidelines

### 14.1 Version Compatibility

**Breaking Changes**:
- Major version bump for breaking API changes
- Minor version bump for new features
- Patch version bump for bug fixes

**Deprecation Policy**:
- Deprecated features marked with warnings
- Minimum 2 minor versions before removal
- Migration guide provided

### 14.2 Dependency Management

**Current Dependencies**:
- `httpx`: Async HTTP client
- `pydantic`: Data validation

**Update Policy**:
- Pin major versions
- Test thoroughly before updates
- Monitor security advisories

### 14.3 GitLab API Changes

**Monitoring**:
- Follow GitLab release notes
- Test with new GitLab versions
- Update API endpoints as needed

**Compatibility Strategy**:
- Support N-2 GitLab versions (current and 2 previous major versions)
- Graceful degradation for missing features
- Feature detection where possible

---

## 15. Troubleshooting Guide

### 15.1 Common Issues

**"GitLab token is not set"**:
- **Cause**: Missing or empty token in Valves
- **Solution**: Configure token in Open WebUI settings

**"Repository write operations are disabled"**:
- **Cause**: `allow_repo_writes=False`
- **Solution**: Enable in Valves if write access needed

**"GitLab API error 401"**:
- **Cause**: Invalid token or insufficient permissions
- **Solution**: Verify token has `api` scope

**"GitLab API error 404"**:
- **Cause**: Project/resource not found or access denied
- **Solution**: Check project path/ID and access permissions

**"Connection timeout"**:
- **Cause**: Network issues or slow GitLab server
- **Solution**: Increase `timeout_seconds` in Valves

**Rate limit errors (429)**:
- **Cause**: Too many requests
- **Solution**: Tool retries automatically; increase `max_retries` if needed

### 15.2 Debug Logging

**Enable Detailed Errors**:
- All errors include full GitLab API response
- Check Open WebUI logs for detailed stack traces

**Network Debugging**:
- Disable SSL verification temporarily to rule out certificate issues
- Use network monitoring tools (Wireshark, Charles Proxy)

---

## 16. Glossary

**Term** | **Definition**
---------|---------------
**IID** | Internal ID, project-scoped sequential integer (e.g., issue #42)
**Global ID** | GitLab-wide unique identifier
**PAT** | Personal Access Token for authentication
**Valve** | Configuration parameter in Open WebUI toolkit
**Compact Mode** | Reduced response payload preserving essential information
**ProjectRef** | Union type accepting numeric ID or string path
**Jitter** | Random variation in retry delays to prevent synchronized retries
**Backoff** | Progressively increasing delay between retry attempts
**Base64** | Binary-safe encoding for file content
**Pagination** | Technique to fetch large lists in chunks
**Ref** | Git reference (branch, tag, or commit SHA)
**Draft MR** | Work-in-progress merge request (prefixed with "Draft:")

---

## 17. Appendix

### 17.1 Example Use Cases

**Automated Issue Triage**:
```
User: "Assign all critical bugs to Alice"
AI: 
1. gitlab_list_issues(labels="bug,priority:critical")
2. gitlab_search_users(search="Alice")
3. For each issue: gitlab_set_issue_assignee(assignee_id=alice_id)
```

**Release Notes Generation**:
```
User: "What issues were closed in the last release?"
AI:
1. gitlab_compare(from_ref="v1.0", to_ref="v1.1")
2. gitlab_list_issues(state="closed")
3. Filter by commit SHAs in comparison
4. Generate markdown list
```

**CI/CD Monitoring**:
```
User: "Why did the latest pipeline fail?"
AI:
1. gitlab_list_pipelines(status="failed", page_count=1)
2. gitlab_list_pipeline_jobs(pipeline_id=X)
3. For failed jobs: gitlab_get_job_trace(job_id=Y)
4. Analyze error messages
```

### 17.2 API Reference Quick Links

**GitLab API Documentation**:
- Projects API: https://docs.gitlab.com/ee/api/projects.html
- Issues API: https://docs.gitlab.com/ee/api/issues.html
- Merge Requests API: https://docs.gitlab.com/ee/api/merge_requests.html
- Repository Files API: https://docs.gitlab.com/ee/api/repository_files.html
- Commits API: https://docs.gitlab.com/ee/api/commits.html
- Pipelines API: https://docs.gitlab.com/ee/api/pipelines.html
- Jobs API: https://docs.gitlab.com/ee/api/jobs.html

### 17.3 Version History

**1.8.0** (Current):
- Complete functionality as documented

**Future Roadmap**:
- Wiki operations
- Group-level issue management
- Epic support
- GraphQL API integration
- Advanced search capabilities

---

**Document End**

This specification reflects the current state of the GitLab Tool for Open WebUI version 1.8.0. For the latest updates, see the project repository: https://github.com/LordOfTheRats/open-webui-gitlab-tool
