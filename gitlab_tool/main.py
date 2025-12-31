"""Main FastAPI application for GitLab tool server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gitlab_tool.agents import (
    CodeReviewAgent,
    IssueSummarizationAgent,
    MergeRequestSummarizationAgent,
    PipelineTriageAgent,
    RepositoryOperationsAgent,
)
from gitlab_tool.artifacts import (
    ApprovalResponse,
    CodeReview,
    GetFileRequest,
    IssueSummary,
    ListProjectsRequest,
    MergeRequestSummary,
    PipelineAnalysis,
    ReviewMergeRequestRequest,
    SummarizeIssueRequest,
    SummarizeMergeRequestRequest,
    TriagePipelineRequest,
)
from gitlab_tool.client import GitLabClient, get_ollama_client
from gitlab_tool.config import get_settings
from gitlab_tool.utils import get_approval_manager, get_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    settings = get_settings()
    
    # Validate configuration
    errors = settings.validate_config()
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError("Invalid configuration")
    
    logger.info("GitLab Tool Server starting...")
    logger.info(f"GitLab URL: {settings.gitlab_url}")
    logger.info(f"Ollama URL: {settings.ollama_base_url}")
    logger.info(f"Max concurrent requests: {settings.max_concurrent_requests}")
    
    # Check Ollama health
    try:
        ollama_client = get_ollama_client()
        await ollama_client.health_check()
        logger.info(f"Ollama health check passed (model: {settings.ollama_model})")
    except Exception as e:
        logger.warning(f"Ollama health check failed: {e}")
        logger.warning("Server will start but LLM features may not work")
    
    yield
    
    logger.info("GitLab Tool Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="GitLab Multi-Agent Tool",
    description="Multi-agent GitLab tool for Open WebUI powered by flock-core",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for Open WebUI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    limiter = get_limiter()
    
    # Check Ollama
    ollama_status = "unknown"
    try:
        ollama_client = get_ollama_client()
        await ollama_client.health_check()
        ollama_status = "healthy"
    except Exception as e:
        ollama_status = f"unhealthy: {str(e)[:100]}"
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "gitlab_url": settings.gitlab_url,
        "ollama_url": settings.ollama_base_url,
        "ollama_status": ollama_status,
        "concurrency": {
            "max": limiter.max_concurrent,
            "available": limiter.available,
        },
    }


# List projects endpoint
@app.post("/projects/list", response_model=list, tags=["Projects"])
async def list_projects(request: ListProjectsRequest):
    """List GitLab projects."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        projects = await client.list_projects(
            search=request.search,
            membership=request.membership,
            page=request.page,
            per_page=request.per_page,
        )
        
        return projects
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Summarize issue endpoint
@app.post("/issues/summarize", response_model=IssueSummary, tags=["Issues"])
async def summarize_issue(request: SummarizeIssueRequest):
    """Summarize a GitLab issue using AI agent."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        # Create and invoke agent
        agent = IssueSummarizationAgent(
            settings=settings,
            gitlab_client=client,
        )
        
        summary = await agent.invoke(request)
        return summary
    except Exception as e:
        logger.error(f"Error summarizing issue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Summarize merge request endpoint
@app.post("/merge-requests/summarize", response_model=MergeRequestSummary, tags=["Merge Requests"])
async def summarize_merge_request(request: SummarizeMergeRequestRequest):
    """Summarize a GitLab merge request using AI agent."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        agent = MergeRequestSummarizationAgent(
            settings=settings,
            gitlab_client=client,
        )
        
        summary = await agent.invoke(request)
        return summary
    except Exception as e:
        logger.error(f"Error summarizing MR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Review merge request endpoint
@app.post("/merge-requests/review", response_model=CodeReview, tags=["Merge Requests"])
async def review_merge_request(request: ReviewMergeRequestRequest):
    """Perform automated code review on a merge request."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        agent = CodeReviewAgent(
            settings=settings,
            gitlab_client=client,
        )
        
        review = await agent.invoke(request)
        return review
    except Exception as e:
        logger.error(f"Error reviewing MR: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Triage pipeline endpoint
@app.post("/pipelines/triage", response_model=PipelineAnalysis, tags=["Pipelines"])
async def triage_pipeline(request: TriagePipelineRequest):
    """Analyze a failed pipeline and identify root cause."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        # Create and invoke agent
        agent = PipelineTriageAgent(
            settings=settings,
            gitlab_client=client,
        )
        
        analysis = await agent.invoke(request)
        return analysis
    except Exception as e:
        logger.error(f"Error triaging pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Get repository file endpoint
@app.post("/repository/files/get", response_model=dict, tags=["Repository"])
async def get_repository_file(request: GetFileRequest):
    """Get a file from repository."""
    try:
        settings = get_settings()
        client = GitLabClient(settings)
        
        agent = RepositoryOperationsAgent(
            settings=settings,
            gitlab_client=client,
        )
        
        result = await agent.invoke(request)
        return result
    except Exception as e:
        logger.error(f"Error getting file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Approval endpoints
@app.get("/approvals/pending", response_model=list, tags=["Approvals"])
async def list_pending_approvals():
    """List pending approval requests."""
    try:
        manager = get_approval_manager()
        pending = manager.list_pending()
        return [req.model_dump() for req in pending]
    except Exception as e:
        logger.error(f"Error listing approvals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/approvals/{request_id}/approve", response_model=ApprovalResponse, tags=["Approvals"])
async def approve_request(request_id: str, message: str = None):
    """Approve a pending request."""
    try:
        manager = get_approval_manager()
        request = manager.approve(request_id)
        
        return ApprovalResponse(
            request_id=request.request_id,
            approved=True,
            message=message,
            timestamp=request.approved_at.isoformat() if request.approved_at else "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error approving request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.post("/approvals/{request_id}/reject", response_model=ApprovalResponse, tags=["Approvals"])
async def reject_request(request_id: str, reason: str = None):
    """Reject a pending request."""
    try:
        manager = get_approval_manager()
        request = manager.reject(request_id, reason)
        
        return ApprovalResponse(
            request_id=request.request_id,
            approved=False,
            message=reason,
            timestamp=request.created_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error rejecting request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "gitlab_tool.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
