"""FastAPI application implementing Open WebUI tool server specification."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import settings
from .models import AgentRole, ApprovalStatus, OperationType
from .orchestrator import orchestrator

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting GitLab Flock Tool Server")
    settings.validate_gitlab_config()
    yield
    logger.info("Shutting down GitLab Flock Tool Server")
    await orchestrator.cleanup()


app = FastAPI(
    title="GitLab Flock Tool",
    description="AI-powered GitLab operations using specialist agents with Flock blackboard pattern",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for Open WebUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AnalyzeProjectRequest(BaseModel):
    """Request to analyze a project."""

    project: str = Field(..., description="Project ID or path (e.g., 'group/project')")


class AnalyzeIssueRequest(BaseModel):
    """Request to analyze an issue."""

    project: str = Field(..., description="Project ID or path")
    issue_iid: int = Field(..., description="Issue IID")


class ListIssuesRequest(BaseModel):
    """Request to list and analyze issues."""

    project: str = Field(..., description="Project ID or path")
    state: str | None = Field(None, description="Issue state (opened/closed)")
    labels: list[str] | None = Field(None, description="Filter by labels")


class AnalyzeMRRequest(BaseModel):
    """Request to analyze a merge request."""

    project: str = Field(..., description="Project ID or path")
    mr_iid: int = Field(..., description="Merge request IID")


class ListMRsRequest(BaseModel):
    """Request to list and analyze merge requests."""

    project: str = Field(..., description="Project ID or path")
    state: str | None = Field(None, description="MR state (opened/merged/closed)")


class ReviewCodeRequest(BaseModel):
    """Request to review code."""

    project: str = Field(..., description="Project ID or path")
    file_path: str = Field(..., description="Path to file in repository")
    ref: str = Field(default="main", description="Branch or tag reference")


class AnalyzePipelinesRequest(BaseModel):
    """Request to analyze pipelines."""

    project: str = Field(..., description="Project ID or path")
    ref: str | None = Field(None, description="Filter by branch/tag")


class CreateIssueRequest(BaseModel):
    """Request to create an issue (requires approval)."""

    project: str = Field(..., description="Project ID or path")
    title: str = Field(..., description="Issue title")
    description: str | None = Field(None, description="Issue description")
    labels: list[str] | None = Field(None, description="Issue labels")


class ApprovalDecisionRequest(BaseModel):
    """Request to approve or reject an operation."""

    approval_id: str = Field(..., description="Approval request ID")
    approved: bool = Field(..., description="Whether to approve or reject")
    comment: str | None = Field(None, description="Optional comment")


class TaskStatusResponse(BaseModel):
    """Task status response."""

    task_id: str
    status: str
    result: dict[str, Any] | None = None
    error: str | None = None


# Health Check
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


# Open WebUI Tool Endpoints
@app.post("/api/analyze-project", tags=["Analysis"])
async def analyze_project(request: AnalyzeProjectRequest) -> TaskStatusResponse:
    """Analyze a GitLab project with AI insights."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.PROJECT_PLANNER,
            operation_type=OperationType.ANALYSIS,
            input_data={"project": request.project},
        )
        
        # Wait for completion
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to analyze project: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-issue", tags=["Analysis"])
async def analyze_issue(request: AnalyzeIssueRequest) -> TaskStatusResponse:
    """Analyze a specific GitLab issue."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.ISSUE_SUMMARIZER,
            operation_type=OperationType.ANALYSIS,
            input_data={"project": request.project, "issue_iid": request.issue_iid},
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to analyze issue: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/list-issues", tags=["Analysis"])
async def list_issues(request: ListIssuesRequest) -> TaskStatusResponse:
    """List and analyze issues in a project."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.ISSUE_SUMMARIZER,
            operation_type=OperationType.ANALYSIS,
            input_data={
                "project": request.project,
                "issues": True,
                "state": request.state,
                "labels": request.labels,
            },
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to list issues: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-mr", tags=["Analysis"])
async def analyze_mr(request: AnalyzeMRRequest) -> TaskStatusResponse:
    """Analyze a specific merge request."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.MR_ANALYZER,
            operation_type=OperationType.ANALYSIS,
            input_data={"project": request.project, "mr_iid": request.mr_iid},
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to analyze MR: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/list-mrs", tags=["Analysis"])
async def list_mrs(request: ListMRsRequest) -> TaskStatusResponse:
    """List and analyze merge requests in a project."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.MR_ANALYZER,
            operation_type=OperationType.ANALYSIS,
            input_data={
                "project": request.project,
                "merge_requests": True,
                "state": request.state,
            },
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to list MRs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/review-code", tags=["Analysis"])
async def review_code(request: ReviewCodeRequest) -> TaskStatusResponse:
    """Review code file with AI analysis."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.CODE_REVIEWER,
            operation_type=OperationType.ANALYSIS,
            input_data={
                "project": request.project,
                "file_path": request.file_path,
                "ref": request.ref,
            },
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to review code: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-pipelines", tags=["Analysis"])
async def analyze_pipelines(request: AnalyzePipelinesRequest) -> TaskStatusResponse:
    """Analyze CI/CD pipelines."""
    try:
        task = await orchestrator.submit_task(
            agent_role=AgentRole.PIPELINE_REVIEWER,
            operation_type=OperationType.ANALYSIS,
            input_data={"project": request.project, "ref": request.ref},
        )
        
        completed_task = await orchestrator.wait_for_task(task.id)
        
        return TaskStatusResponse(
            task_id=task.id,
            status=completed_task.status.value,
            result=completed_task.output_data,
            error=completed_task.error,
        )
    except Exception as e:
        logger.error("Failed to analyze pipelines: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-issue", tags=["Write Operations"])
async def create_issue(request: CreateIssueRequest) -> dict[str, Any]:
    """Create a new issue (requires human approval)."""
    if not settings.require_approval_for_writes:
        raise HTTPException(
            status_code=403,
            detail="Write operations are disabled. Enable require_approval_for_writes.",
        )
    
    try:
        # Create task that requires approval
        task = await orchestrator.submit_task(
            agent_role=AgentRole.ISSUE_SUMMARIZER,
            operation_type=OperationType.WRITE,
            input_data={
                "project": request.project,
                "title": request.title,
                "description": request.description,
                "labels": request.labels,
                "action": "create_issue",
            },
            requires_approval=True,
        )
        
        # Create approval request
        approval = await orchestrator.blackboard.request_approval(
            task_id=task.id,
            operation_type=OperationType.WRITE,
            description=f"Create issue: {request.title}",
            details={
                "project": request.project,
                "title": request.title,
                "description": request.description,
                "labels": request.labels,
            },
        )
        
        return {
            "task_id": task.id,
            "approval_id": approval.id,
            "status": "requires_approval",
            "message": "Issue creation requires human approval",
            "approval_endpoint": f"/api/approve/{approval.id}",
        }
    except Exception as e:
        logger.error("Failed to create issue: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/approve/{approval_id}", tags=["Human Approval"])
async def approve_operation(
    approval_id: str,
    decision: ApprovalDecisionRequest,
) -> dict[str, Any]:
    """Approve or reject a pending operation."""
    try:
        await orchestrator.approve_task(
            approval_id=decision.approval_id,
            approved=decision.approved,
            comment=decision.comment,
        )
        
        approval = orchestrator.blackboard.approval_requests.get(approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        
        task = await orchestrator.get_task_status(approval.task_id)
        
        return {
            "approval_id": approval_id,
            "status": approval.status.value,
            "task_id": approval.task_id,
            "task_status": task.status.value if task else "unknown",
        }
    except Exception as e:
        logger.error("Failed to process approval: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/approvals/pending", tags=["Human Approval"])
async def get_pending_approvals() -> dict[str, Any]:
    """Get all pending approval requests."""
    try:
        approvals = await orchestrator.get_pending_approvals()
        
        return {
            "total": len(approvals),
            "approvals": [
                {
                    "id": approval.id,
                    "task_id": approval.task_id,
                    "operation_type": approval.operation_type.value,
                    "description": approval.description,
                    "details": approval.details,
                    "created_at": approval.created_at.isoformat(),
                    "expires_at": approval.expires_at.isoformat(),
                }
                for approval in approvals
            ],
        }
    except Exception as e:
        logger.error("Failed to get pending approvals: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}", tags=["Tasks"])
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get status of a specific task."""
    try:
        task = await orchestrator.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskStatusResponse(
            task_id=task.id,
            status=task.status.value,
            result=task.output_data,
            error=task.error,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task status: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
