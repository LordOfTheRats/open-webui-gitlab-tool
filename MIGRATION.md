# Migration from V1 to V2

## Overview

Version 2.0 is a complete architectural reimagination of the GitLab tool, moving from a monolithic design to a multi-agent system using the Flock blackboard pattern.

## Key Differences

### V1 (Legacy - `gitlab_v1_legacy.py`)

- **Architecture**: Monolithic Open WebUI function
- **Execution**: Synchronous, direct API calls
- **State**: No shared state or coordination
- **AI**: Basic prompt-response pattern
- **Approval**: Valve-based simple flags
- **Extensibility**: Limited, requires modifying core code

### V2 (Current)

- **Architecture**: Multi-agent system with Flock blackboard
- **Execution**: Asynchronous task-based with orchestration
- **State**: Shared blackboard for agent coordination
- **AI**: Specialized agents with domain expertise
- **Approval**: Robust approval workflow with timeout handling
- **Extensibility**: Easy to add new agents and capabilities

## Migration Path

### For Users

V2 is not backward compatible. To migrate:

1. **Update Integration**
   - V1: Single Open WebUI function file
   - V2: FastAPI server with multiple endpoints

2. **Configuration**
   - V1: Valves in Open WebUI
   - V2: Environment variables (.env file)

3. **API Changes**
   - V1: Function parameters
   - V2: REST API endpoints

### For Developers

V2 provides better extension points:

1. **Adding New Operations**
   - V1: Modify single file with new function
   - V2: Create new agent class or endpoint

2. **Customization**
   - V1: Fork and modify
   - V2: Extend base classes, add agents

## Feature Comparison

| Feature | V1 | V2 |
|---------|----|----|
| GitLab Projects | ✅ | ✅ |
| Issues | ✅ | ✅ Enhanced with AI |
| Merge Requests | ✅ | ✅ Enhanced with AI |
| Code Review | ❌ | ✅ AI-powered |
| Pipelines | ✅ Basic | ✅ Enhanced with AI |
| Wiki | ✅ | 🚧 Planned |
| Approval Workflow | Basic | ✅ Robust |
| Agent Coordination | ❌ | ✅ Blackboard pattern |
| Async Execution | ❌ | ✅ |
| Task Tracking | ❌ | ✅ |
| Docker Support | ❌ | ✅ |
| Tests | ❌ | ✅ |

## Why Rebuild?

### Problems with V1

1. **Monolithic**: 2000+ lines in single file
2. **Limited AI**: Simple prompt-response, no reasoning
3. **No State**: Each operation isolated
4. **Synchronous**: Blocking operations
5. **Hard to Extend**: Deep modifications required
6. **No Testing**: Difficult to test monolith

### Benefits of V2

1. **Modular**: Clear separation of concerns
2. **Intelligent**: Specialized agents with domain knowledge
3. **Coordinated**: Agents share state and collaborate
4. **Async**: Non-blocking, better performance
5. **Extensible**: Add agents without touching core
6. **Testable**: Unit tests for components
7. **Professional**: Docker, proper logging, monitoring

## Example Comparison

### V1: Analyze Issue

```python
# V1 - Direct implementation in monolith
async def get_issue(
    project: str,
    issue_iid: int,
    compact: bool = None,
    ...
) -> str:
    # Direct API call
    # Direct LLM prompt
    # Return formatted string
```

### V2: Analyze Issue

```python
# V2 - Agent-based with orchestration
class IssueSummarizerAgent(BaseAgent):
    async def execute(self, task: Task) -> dict:
        # Agent reads from blackboard
        # Specialized analysis logic
        # Posts results to blackboard
        # Returns structured data

# Orchestration
task = await orchestrator.submit_task(
    agent_role=AgentRole.ISSUE_SUMMARIZER,
    operation_type=OperationType.ANALYSIS,
    input_data={"project": "...", "issue_iid": 123},
)
result = await orchestrator.wait_for_task(task.id)
```

## Preserving V1 Capabilities

All V1 operations are supported in V2:

- ✅ List projects
- ✅ Get project details
- ✅ List/get issues
- ✅ List/get merge requests
- ✅ Get file content
- ✅ List pipelines
- ✅ Create issues (with approval)
- 🚧 Wiki operations (planned)
- 🚧 Pipeline actions (planned)

## Timeline

- **V1**: 2024 - Initial release
- **V2**: 2025 - Complete rewrite with Flock

V1 is preserved as `gitlab_v1_legacy.py` for reference but is not maintained.

## Getting Help

- **V2 Issues**: Use GitHub Issues
- **V1 Questions**: Refer to legacy file, no active support
- **Migration Help**: Open a discussion on GitHub

## Recommendation

**New users**: Start with V2
**V1 users**: Plan migration to V2 for better features and support
