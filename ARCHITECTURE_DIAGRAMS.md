# Architecture Diagrams

Visual representations of the flock-core agent architecture for the GitLab multi-agent tool.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Open WebUI                              │
│                    (User Interface Layer)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/JSON (OpenAPI)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server                             │
│                   (API Endpoint Layer)                          │
│                                                                 │
│  /api/summarize-issue     /api/review-mr                       │
│  /api/summarize-mr        /api/triage-pipeline                 │
│  /api/approvals/*         /health                              │
└────────────┬──────────────────────────┬─────────────────────────┘
             │                          │
             │ Orchestration            │ Approval
             ▼                          ▼
┌────────────────────────┐    ┌─────────────────────┐
│  Agent Orchestrator    │    │  Approval Manager   │
│  - invoke_agent()      │    │  - Human-in-loop    │
│  - parallel_agents()   │    │  - Timeout handling │
│  - agent_chain()       │    └─────────────────────┘
└────────────┬───────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Factory                              │
│                   (Agent Lifecycle)                             │
└────────────┬────────────────────────────────────────────────────┘
             │
     ┌───────┴───────┬───────────┬───────────┬────────────┐
     ▼               ▼           ▼           ▼            ▼
┌─────────┐    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Issue   │    │   MR    │ │  Code   │ │Pipeline │ │  Repo   │
│Summarize│    │Summarize│ │ Review  │ │ Triage  │ │   Ops   │
│ Agent   │    │ Agent   │ │ Agent   │ │ Agent   │ │ Agent   │
└────┬────┘    └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │              │           │           │           │
     └──────────────┴───────────┴───────────┴───────────┘
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
┌──────────────────┐  ┌──────────────────┐
│  GitLab Client   │  │  Ollama Client   │
│  - API calls     │  │  - LLM requests  │
│  - Auth/retry    │  │  - Concurrency   │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  GitLab API      │  │  Ollama Server   │
│  (Self-hosted)   │  │  (Self-hosted)   │
└──────────────────┘  └──────────────────┘
```

## Agent Execution Flow

```
┌──────────────┐
│ User Request │
│ (via API)    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ FastAPI Endpoint                         │
│ - Validate request (Pydantic)            │
│ - Create input artifact                  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Orchestrator: invoke_agent()             │
│ - Get settings                           │
│ - Create GitLabClient                    │
│ - Create OllamaClient                    │
│ - Get agent from factory                 │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Agent.execute(input_artifact)            │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ 1. Fetch data from GitLab          │  │
│ │    - Issue/MR/Pipeline details     │  │
│ │    - Comments/Notes                │  │
│ │    - Diffs/Logs                    │  │
│ └────────┬───────────────────────────┘  │
│          │                               │
│          ▼                               │
│ ┌────────────────────────────────────┐  │
│ │ 2. Prepare prompt                  │  │
│ │    - Build context                 │  │
│ │    - Truncate if needed            │  │
│ │    - Structure request             │  │
│ └────────┬───────────────────────────┘  │
│          │                               │
│          ▼                               │
│ ┌────────────────────────────────────┐  │
│ │ 3. Call Ollama                     │  │
│ │    ┌─────────────────────────────┐ │  │
│ │    │ async with limiter:         │ │  │
│ │    │   [Wait if 2 already active]│ │  │
│ │    │   Send HTTP request         │ │  │
│ │    │   Get LLM response          │ │  │
│ │    └─────────────────────────────┘ │  │
│ └────────┬───────────────────────────┘  │
│          │                               │
│          ▼                               │
│ ┌────────────────────────────────────┐  │
│ │ 4. Parse response                  │  │
│ │    - Extract JSON                  │  │
│ │    - Validate structure            │  │
│ │    - Handle errors                 │  │
│ └────────┬───────────────────────────┘  │
│          │                               │
│          ▼                               │
│ ┌────────────────────────────────────┐  │
│ │ 5. Build output artifact           │  │
│ │    - Populate Pydantic model       │  │
│ │    - Add metadata                  │  │
│ │    - Return artifact               │  │
│ └────────┬───────────────────────────┘  │
└──────────┼───────────────────────────────┘
           │
           ▼
    ┌──────────────┐
    │ Output       │
    │ Artifact     │
    │ (JSON)       │
    └──────────────┘
```

## Concurrency Control

```
                    Ollama Concurrency Limiter
                    ┌─────────────────────────┐
                    │  Semaphore (max=2)      │
                    │  ┌─────┐ ┌─────┐        │
                    │  │Slot1│ │Slot2│        │
                    │  └─────┘ └─────┘        │
                    └────┬────────┬────────────┘
                         │        │
    ┌────────────────────┼────────┼────────────────────┐
    │                    │        │                    │
    ▼                    ▼        ▼                    ▼
┌────────┐         ┌────────┐ ┌────────┐         ┌────────┐
│Agent 1 │         │Agent 2 │ │Agent 3 │         │Agent 4 │
│(active)│         │(active)│ │(queued)│         │(queued)│
└───┬────┘         └───┬────┘ └───┬────┘         └───┬────┘
    │                  │          │                  │
    │ Ollama req       │          │ Waiting...       │ Waiting...
    ▼                  ▼          │                  │
  ┌────┐             ┌────┐       │                  │
  │LLM │             │LLM │       │                  │
  └────┘             └────┘       │                  │
    │                  │          │                  │
    │ Response         │          │                  │
    ▼                  ▼          │                  │
┌────────┐         ┌────────┐    │                  │
│Agent 1 │         │Agent 2 │    │                  │
│(done)  │         │(done)  │    │                  │
└────────┘         └────────┘    │                  │
                                 │ Slot available!  │
                                 ▼                  │
                            ┌────────┐              │
                            │Agent 3 │              │
                            │(active)│              │
                            └───┬────┘              │
                                │                   │
                                │ Ollama req        │
                                ▼                   │
                              ┌────┐                │
                              │LLM │                │
                              └────┘                │
                                                    │
                            When Agent 3 completes, │
                            Agent 4 gets a slot     ▼
                                             ┌────────┐
                                             │Agent 4 │
                                             │(active)│
                                             └────────┘
```

## Artifact Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Artifact Lifecycle                          │
└─────────────────────────────────────────────────────────────────┘

1. Request Artifact (Input)
   ┌───────────────────────────────┐
   │ IssueSummaryRequest           │
   │ - project: "group/project"    │
   │ - issue_iid: 42               │
   │ - include_comments: True      │
   │ - max_comments: 50            │
   └───────────┬───────────────────┘
               │
               ▼
         [Agent Processing]
               │
               ▼
2. Output Artifact
   ┌───────────────────────────────┐
   │ IssueSummary                  │
   │ - issue_iid: 42               │
   │ - project: "group/project"    │
   │ - title: "Bug in auth"        │
   │ - summary: "Login fails..."   │
   │ - key_points: [...]           │
   │ - priority: "high"            │
   │ - complexity: "moderate"      │
   │ - stakeholders: ["alice"]     │
   │ - related_issues: [41, 43]    │
   │ - timestamp: 2025-12-31...    │
   └───────────┬───────────────────┘
               │
               ▼
3. Serialization (JSON Response)
   {
     "issue_iid": 42,
     "project": "group/project",
     "title": "Bug in auth",
     ...
   }
```

## Approval Workflow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Write Operation Flow                          │
└──────────────────────────────────────────────────────────────────┘

User Request
     │
     ▼
┌─────────────────────┐
│ Repo Write Request  │
│ - operation: create │
│ - file_path: "x.py" │
│ - content: "..."    │
└─────────┬───────────┘
          │
          ▼
    ┌──────────────────┐
    │ Requires         │  No
    │ Approval?        ├──────────────┐
    └──────┬───────────┘              │
           │ Yes                       │
           ▼                           │
┌──────────────────────┐               │
│ Create Approval Req  │               │
│ - request_id: uuid   │               │
│ - operation: "..."   │               │
│ - project: "..."     │               │
│ - expires_at: +5min  │               │
└──────────┬───────────┘               │
           │                           │
           │ Store in ApprovalManager  │
           ▼                           │
┌──────────────────────┐               │
│ Return request_id to │               │
│ user/display in UI   │               │
└──────────┬───────────┘               │
           │                           │
    ┌──────┴─────────┐                 │
    │                │                 │
    ▼                ▼                 │
┌────────┐      ┌─────────┐            │
│ User   │      │ Timeout │            │
│ Action │      │ (5 min) │            │
└───┬────┘      └────┬────┘            │
    │                │                 │
Approve         Expires                │
    │                │                 │
    ▼                ▼                 │
┌──────────────────────────┐           │
│ ApprovalManager          │           │
│ - Set status: APPROVED   │           │
│ - Wake waiting task      │           │
└──────────┬───────────────┘           │
           │                           │
           ▼                           │
┌──────────────────────┐               │
│ Execute GitLab API   │◄──────────────┘
│ - Create file        │
│ - Get commit SHA     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Return Result        │
│ - commit_sha: "..."  │
│ - approval_status    │
└──────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                   Approval State Machine                         │
└──────────────────────────────────────────────────────────────────┘

    PENDING
       │
   ┌───┼────┬────────┐
   │   │    │        │
   │   │    │        │
   ▼   ▼    ▼        ▼
APPROVED REJECTED EXPIRED
(execute) (abort)  (abort)
```

## Agent Class Hierarchy

```
                    BaseAgent<InputT, OutputT>
                           │
            ┌──────────────┼──────────────┬──────────────┬───────────────┐
            │              │              │              │               │
            ▼              ▼              ▼              ▼               ▼
┌────────────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ IssueSummarization │ │   MR     │ │   Code   │ │ Pipeline │ │ Repository   │
│      Agent         │ │Summarize │ │  Review  │ │  Triage  │ │  Operations  │
│                    │ │  Agent   │ │  Agent   │ │  Agent   │ │   Agent      │
├────────────────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├──────────────┤
│ Input:             │ │ Input:   │ │ Input:   │ │ Input:   │ │ Input:       │
│ IssueSummaryReq    │ │ MRSummary│ │ CodeReview│ │ Pipeline │ │ RepoQueryReq │
│                    │ │ Req      │ │ Req      │ │ TriageReq│ │ RepoWriteReq │
│ Output:            │ │          │ │          │ │          │ │              │
│ IssueSummary       │ │ Output:  │ │ Output:  │ │ Output:  │ │ Output:      │
│                    │ │ MRSummary│ │ CodeReview│ │ Pipeline │ │ RepoQueryRes │
│ Methods:           │ │          │ │          │ │ Analysis │ │ RepoWriteRes │
│ - execute()        │ │ Methods: │ │ Methods: │ │          │ │              │
│ - _build_prompt()  │ │ - execute│ │ - execute│ │ Methods: │ │ Methods:     │
│ - _parse_response()│ │ - _prepare│ │ - _chunk │ │ - execute│ │ - execute    │
│ - _extract_stake   │ │   _diff  │ │   _diff  │ │ - _extract│ │ - _handle_   │
│   holders()        │ │ - _analyze│ │ - _detect│ │   _errors│ │   query()    │
│                    │ │   _risks │ │   _issues│ │ - _find_ │ │ - _handle_   │
│                    │ │          │ │          │ │   root_  │ │   write()    │
│                    │ │          │ │          │ │   cause  │ │              │
└────────────────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  End-to-End Data Flow                           │
└─────────────────────────────────────────────────────────────────┘

HTTP Request                   GitLab API                 Ollama API
     │                              │                          │
     ▼                              │                          │
┌──────────┐                        │                          │
│ FastAPI  │                        │                          │
│ Endpoint │                        │                          │
└────┬─────┘                        │                          │
     │ Pydantic validation          │                          │
     ▼                              │                          │
┌──────────────┐                    │                          │
│ Input        │                    │                          │
│ Artifact     │                    │                          │
└────┬─────────┘                    │                          │
     │ Pass to orchestrator         │                          │
     ▼                              │                          │
┌──────────────┐                    │                          │
│ Orchestrator │                    │                          │
│ invoke_agent │                    │                          │
└────┬─────────┘                    │                          │
     │ Create agent                 │                          │
     ▼                              │                          │
┌──────────────┐                    │                          │
│ Agent        │                    │                          │
│ execute()    │                    │                          │
└────┬─────────┘                    │                          │
     │                              │                          │
     ├─────────────────────────────►│                          │
     │ Fetch issue/MR/pipeline      │                          │
     │                              ▼                          │
     │                         ┌────────┐                      │
     │                         │ GitLab │                      │
     │                         │   API  │                      │
     │                         └────┬───┘                      │
     │ GitLab data                  │                          │
     │◄─────────────────────────────┘                          │
     │                                                         │
     ├────────────────────────────────────────────────────────►│
     │ Generate summary/review/analysis                        │
     │ (respects concurrency limit)                            │
     │                                                         ▼
     │                                                    ┌────────┐
     │                                                    │ Ollama │
     │                                                    │  LLM   │
     │                                                    └────┬───┘
     │ LLM response                                            │
     │◄────────────────────────────────────────────────────────┘
     │
     │ Parse and build output artifact
     ▼
┌──────────────┐
│ Output       │
│ Artifact     │
└────┬─────────┘
     │ Serialize
     ▼
┌──────────────┐
│ JSON Response│
└────┬─────────┘
     │
     ▼
  HTTP 200 OK
```

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                   Component Dependency Graph                    │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   FastAPI    │
                    │   (main.py)  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │Orchestration │ │ Approval │ │    Config    │
    │              │ │ Manager  │ │   Settings   │
    └──────┬───────┘ └──────────┘ └──────────────┘
           │
      ┌────┴────┐
      ▼         ▼
┌──────────┐ ┌─────────────┐
│  Agent   │ │   Clients   │
│ Factory  │ │ (GitLab,    │
└────┬─────┘ │  Ollama)    │
     │       └──────┬──────┘
     │              │
     ▼              ▼
┌──────────────────────────────┐
│         Agents               │
│  - IssueSummarization        │
│  - MRSummarization           │
│  - CodeReview                │
│  - PipelineTriage            │
│  - RepositoryOperations      │
└───────┬──────────────────────┘
        │
        ▼
┌──────────────┐
│  Artifacts   │
│  (Pydantic)  │
│  - Requests  │
│  - Responses │
└──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   External Dependencies                         │
└─────────────────────────────────────────────────────────────────┘

Application                External Services
     │
     ├──────► GitLab API (Self-hosted)
     │        - Issue management
     │        - MR operations
     │        - CI/CD pipelines
     │        - Repository files
     │
     ├──────► Ollama Server (Self-hosted)
     │        - Text generation
     │        - Code analysis
     │        - Summarization
     │
     └──────► flock-core (Optional)
              - Artifact store
              - Task orchestration
              - Agent coordination
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Docker Compose Deployment                     │
└─────────────────────────────────────────────────────────────────┘

Docker Host
  │
  ├─── Container: gitlab-tool
  │    ├─── FastAPI app (port 8000)
  │    ├─── Agents
  │    ├─── Volume: .flock/ (artifact store)
  │    └─── Env: GITLAB_URL, GITLAB_TOKEN, ...
  │
  ├─── Container: ollama
  │    ├─── Ollama server (port 11434)
  │    ├─── GPU access (NVIDIA)
  │    ├─── Models: llama3.2:latest
  │    └─── Volume: ollama_data/
  │
  └─── Network: bridge
       - gitlab-tool:8000 → ollama:11434
       - External → gitlab-tool:8000

┌─────────────────────────────────────────────────────────────────┐
│                   Kubernetes Deployment                         │
└─────────────────────────────────────────────────────────────────┘

Namespace: gitlab-agents
  │
  ├─── Deployment: gitlab-tool
  │    ├─── Replica: 1 (single instance for approval state)
  │    ├─── Container: gitlab-tool:2.0.0
  │    ├─── ConfigMap: gitlab-config
  │    ├─── Secret: gitlab-secrets
  │    └─── PVC: flock-storage (RWO)
  │
  ├─── Deployment: ollama
  │    ├─── Replica: 1
  │    ├─── Container: ollama:latest
  │    ├─── GPU: nvidia.com/gpu: 1
  │    └─── PVC: ollama-models (RWO)
  │
  ├─── Service: gitlab-tool (LoadBalancer)
  │    └─── Port: 8000 → 8000
  │
  └─── Service: ollama (ClusterIP)
       └─── Port: 11434 → 11434
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────┐
│                   Latency Breakdown                             │
└─────────────────────────────────────────────────────────────────┘

Operation: Issue Summarization (with comments)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                  Total: ~5-8s
                                                  
FastAPI handling          ▓ (~10ms)
GitLab API - Get issue    ▓▓ (~100ms)
GitLab API - Get comments ▓▓ (~100ms)
Build prompt              ▓ (~10ms)
Wait for Ollama slot      ░░░░░░░░ (0-300s if queue full)
Ollama generation         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (~3-5s)
Parse response            ▓ (~10ms)
Build artifact            ▓ (~10ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Operation: Code Review (thorough, large diff)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                  Total: ~10-15s
                                                  
FastAPI handling          ▓ (~10ms)
GitLab API - Get MR       ▓▓ (~100ms)
GitLab API - Get diff     ▓▓▓ (~200ms)
Process/chunk diff        ▓▓ (~100ms)
Wait for Ollama slot      ░░░░░░░░ (0-300s if queue full)
Ollama generation         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ (~8-12s)
Parse response            ▓▓ (~50ms)
Build artifact            ▓ (~10ms)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Concurrent Load (5 requests, max_concurrent=2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                                  Total: ~15-20s
                                                  
Request 1 ▓▓▓▓▓▓▓▓ (0-5s)
Request 2 ▓▓▓▓▓▓▓▓ (0-5s)       } Batch 1 (parallel)
Request 3 ░░░░░░░░▓▓▓▓▓▓▓▓ (5-10s)
Request 4 ░░░░░░░░▓▓▓▓▓▓▓▓ (5-10s)   } Batch 2 (parallel)
Request 5 ░░░░░░░░░░░░░░░░▓▓▓▓▓▓▓▓ (10-15s) } Batch 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Legend:
▓ = Active processing
░ = Queued/waiting
```

## Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│                   Security Boundaries                           │
└─────────────────────────────────────────────────────────────────┘

External User
     │
     │ HTTPS (TLS 1.2+)
     ▼
┌──────────────────────┐
│  FastAPI Server      │
│                      │
│  ┌────────────────┐  │
│  │ Input          │  │ ← Pydantic validation
│  │ Validation     │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │ Authentication │  │ ← GitLab token
│  │ (optional)     │  │
│  └────────────────┘  │
└──────────┬───────────┘
           │
           ▼
    ┌────────────────┐
    │ Approval       │
    │ Required?      │
    └────┬───────────┘
         │
    ┌────┴────┐
    │         │
    No       Yes
    │         │
    │         ▼
    │    ┌────────────────┐
    │    │ Human Approval │
    │    │ - Timeout      │
    │    │ - Audit log    │
    │    └────┬───────────┘
    │         │
    │         │ Approved
    └────┬────┘
         │
         ▼
┌──────────────────────┐
│  Agent Execution     │
│                      │
│  ┌────────────────┐  │
│  │ GitLab Client  │  │
│  │ - Token auth   │  │ ← Stored in env
│  │ - Rate limit   │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │ Ollama Client  │  │
│  │ - Local only   │  │ ← No external access
│  │ - No auth      │  │
│  └────────────────┘  │
└──────────────────────┘

Security Measures:
✓ Input validation (Pydantic)
✓ Human approval for writes
✓ GitLab token in env (not code)
✓ TLS for external access
✓ Rate limiting
✓ Audit logging
✓ Ollama isolated (no external)
✗ Currently no user authentication
```

---

## Summary

These diagrams illustrate:

1. **System Overview**: High-level architecture with all components
2. **Agent Execution Flow**: Step-by-step processing within an agent
3. **Concurrency Control**: How Ollama semaphore manages requests
4. **Artifact Flow**: Input/output artifact lifecycle
5. **Approval Workflow**: Human-in-the-loop process
6. **Class Hierarchy**: Agent inheritance structure
7. **Data Flow**: End-to-end request processing
8. **Component Dependencies**: How modules relate
9. **Deployment**: Docker and Kubernetes setups
10. **Performance**: Latency characteristics
11. **Security**: Protection boundaries

For implementation details, see [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md) and [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md).
