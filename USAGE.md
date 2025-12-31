# Usage Guide

## Quick Start

1. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your GitLab URL and token
```

2. **Install Dependencies**

```bash
pip install -e .
```

3. **Run Server**

```bash
uvicorn src.main:app --reload
```

## Using Docker

```bash
docker-compose up -d
```

## API Endpoints

### Analysis Operations

#### Analyze Project
```bash
curl -X POST http://localhost:8000/api/analyze-project \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name"}'
```

#### Analyze Issue
```bash
curl -X POST http://localhost:8000/api/analyze-issue \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name", "issue_iid": 123}'
```

#### List and Analyze Issues
```bash
curl -X POST http://localhost:8000/api/list-issues \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name", "state": "opened"}'
```

#### Analyze Merge Request
```bash
curl -X POST http://localhost:8000/api/analyze-mr \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name", "mr_iid": 456}'
```

#### Review Code
```bash
curl -X POST http://localhost:8000/api/review-code \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name", "file_path": "src/main.py", "ref": "main"}'
```

#### Analyze Pipelines
```bash
curl -X POST http://localhost:8000/api/analyze-pipelines \
  -H "Content-Type: application/json" \
  -d '{"project": "group/project-name"}'
```

### Write Operations (Require Approval)

#### Create Issue
```bash
curl -X POST http://localhost:8000/api/create-issue \
  -H "Content-Type: application/json" \
  -d '{
    "project": "group/project-name",
    "title": "New issue title",
    "description": "Issue description",
    "labels": ["bug", "priority-high"]
  }'
```

This returns an `approval_id` that must be approved before execution.

#### Get Pending Approvals
```bash
curl http://localhost:8000/api/approvals/pending
```

#### Approve Operation
```bash
curl -X POST http://localhost:8000/api/approve/{approval_id} \
  -H "Content-Type: application/json" \
  -d '{
    "approval_id": "abc-123",
    "approved": true,
    "comment": "Approved for execution"
  }'
```

### Task Status

#### Check Task Status
```bash
curl http://localhost:8000/api/tasks/{task_id}
```

## Open WebUI Integration

1. In Open WebUI, go to **Settings → Functions**
2. Click **Add Function**
3. Select **Import from URL**
4. Enter: `http://localhost:8000`
5. The tool will auto-register

Now you can use natural language in Open WebUI:
- "Analyze the issues in project X"
- "Review the code in file Y"
- "What's the status of merge request Z?"

## Agent Architecture

The system uses specialized agents:

- **Project Planner**: Overall project analysis and planning
- **Issue Summarizer**: Issue analysis and summarization
- **MR Analyzer**: Merge request analysis
- **Code Reviewer**: Code quality review
- **Pipeline Reviewer**: CI/CD pipeline analysis

All agents communicate through the Flock blackboard pattern for coordination.

## Human Approval Workflow

1. Submit a write operation (e.g., create issue)
2. System creates an approval request
3. Check pending approvals: `GET /api/approvals/pending`
4. Approve or reject: `POST /api/approve/{id}`
5. If approved, agent executes the operation

## Configuration Options

See [.env.example](.env.example) for all configuration options:

- GitLab URL and token
- Ollama URL and model
- Agent timeouts and limits
- Approval requirements
- Logging levels

## Troubleshooting

### Ollama Connection Issues
```bash
# Test Ollama
curl http://localhost:11434/api/generate -d '{"model":"llama3.2","prompt":"test"}'
```

### GitLab Token Issues
Ensure your token has these scopes:
- `api` - Full API access
- `read_repository` - Read repository files
- `write_repository` - Write operations (if enabled)

### Agent Timeouts
Increase timeout in `.env`:
```
AGENT_TIMEOUT=900
OLLAMA_TIMEOUT=600
```
