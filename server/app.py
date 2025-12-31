"""FastAPI server exposing the GitLab Deepagents agent with a simple htmx UI."""

from __future__ import annotations

import functools
import json
import logging
import os
from html import escape
from typing import Any, Dict, Optional

import anyio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agents.gitlab_deepagent import run_once

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="GitLab Agent Server", version="1.0.0")
templates = Jinja2Templates(directory="server/templates")


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------
# Helpers
# -----------------


def _bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "y", "on"}:
        return True
    if s in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _defaults() -> Dict[str, Any]:
    return {
        "model": os.getenv("GITLAB_AGENT_MODEL", "ollama:gpt-4o"),
        "gitlab_url": os.getenv("GITLAB_URL", "https://gitlab.example.com"),
        "allow_writes": _bool(os.getenv("GITLAB_ALLOW_WRITES"), False),
        "compact_results": _bool(os.getenv("GITLAB_COMPACT_RESULTS"), True),
        "verify_ssl": _bool(os.getenv("GITLAB_VERIFY_SSL"), True),
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    }


def _detect_hx(request: Request) -> bool:
    return request.headers.get("HX-Request", "").lower() == "true"


def _float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _clean_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    message = (raw.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    return {
        "message": message,
        "model_name": raw.get("model") or raw.get("model_name") or _defaults()["model"],
        "ollama_base_url": raw.get("ollama_base_url") or raw.get("ollamaBaseUrl"),
        "gitlab_url": raw.get("gitlab_url") or raw.get("gitlabUrl") or _defaults()["gitlab_url"],
        "gitlab_token": raw.get("gitlab_token") or raw.get("gitlabToken"),
        "verify_ssl": _bool(raw.get("verify_ssl"), _defaults()["verify_ssl"]),
        "compact_results_default": _bool(raw.get("compact"), _defaults()["compact_results"]),
        "allow_repo_writes": _bool(raw.get("allow_writes"), _defaults()["allow_writes"]),
        "temperature": _float(raw.get("temperature")),
        "top_p": _float(raw.get("top_p")),
        "top_k": _int(raw.get("top_k")),
    }


def _fmt_result(result: Any) -> str:
    try:
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception:
        return str(result)


async def _parse_request_payload(request: Request) -> Dict[str, Any]:
    content_type = request.headers.get("content-type", "").lower()
    logger.debug(f"_parse_request_payload: content_type={content_type}")
    try:
        if "application/json" in content_type:
            data = await request.json()
            if not isinstance(data, dict):
                raise HTTPException(status_code=400, detail="JSON body must be an object")
            return _clean_payload(data)

        form = await request.form()
        form_dict = dict(form)
        logger.debug(f"Form data: {form_dict}")
        return _clean_payload(form_dict)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Error parsing request: {exc}")
        raise HTTPException(status_code=400, detail=f"Failed to parse request: {str(exc)}")


async def _invoke_agent(clean_payload: Dict[str, Any]) -> Any:
    try:
        logger.info(f"Invoking agent with message: {clean_payload['message'][:100]}")
        
        # Check for required GITLAB_TOKEN before invoking agent
        if not clean_payload.get("gitlab_token") and not os.getenv("GITLAB_TOKEN"):
            raise HTTPException(
                status_code=400,
                detail="GITLAB_TOKEN environment variable is required. Set it in server environment or provide gitlab_token in request."
            )
        
        # Use functools.partial to wrap run_once with keyword arguments
        run_with_args = functools.partial(
            run_once,
            clean_payload["message"],
            model_name=clean_payload.get("model_name"),
            ollama_base_url=clean_payload.get("ollama_base_url"),
            gitlab_url=clean_payload.get("gitlab_url"),
            gitlab_token=clean_payload.get("gitlab_token"),
            verify_ssl=clean_payload.get("verify_ssl"),
            compact_results_default=clean_payload.get("compact_results_default"),
            allow_repo_writes=clean_payload.get("allow_repo_writes"),
            temperature=clean_payload.get("temperature"),
            top_p=clean_payload.get("top_p"),
            top_k=clean_payload.get("top_k"),
        )
        
        result = await anyio.to_thread.run_sync(run_with_args)
        logger.info(f"Agent returned result: {str(result)[:100]}")
        return result
    except HTTPException:
        raise
    except ValueError as ve:
        logger.exception(f"ValueError from agent: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception(f"Error invoking agent: {exc}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")


# -----------------
# Open WebUI tool schema
# -----------------


class GitlabToolInput(BaseModel):
    message: str = Field(..., description="User request for the GitLab agent")


class GitlabToolOutput(BaseModel):
    content: Any


# Register exception handler for HTTPException (must be after helper functions are defined)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
    if _detect_hx(request):
        error_html = f'<div class="error"><strong>Error:</strong> {escape(str(exc.detail))}</div>'
        return HTMLResponse(error_html, status_code=exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# -----------------
# Routes
# -----------------


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
async def config() -> Dict[str, Any]:
    return _defaults()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "config": _defaults()})


@app.post("/chat")
async def chat(request: Request):
    logger.debug("POST /chat received")
    logger.debug(f"Request method: {request.method}, content-type: {request.headers.get('content-type')}")
    
    try:
        payload = await _parse_request_payload(request)
        logger.info(f"Parsed payload successfully")
        result = await _invoke_agent(payload)
        logger.info(f"Agent invocation successful")
    except HTTPException:
        # Let the custom exception handler deal with it
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"Unexpected exception in /chat: {exc}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")

    if _detect_hx(request):
        rendered = _fmt_result(result)
        logger.debug("Returning HTML response for htmx")
        return HTMLResponse(f"<div class=\"result\"><pre>{escape(rendered)}</pre></div>", status_code=200)

    logger.debug("Returning JSON response")
    return JSONResponse({"result": result})


# Open WebUI-compatible tool endpoint
@app.post("/gitlab-agent", response_model=GitlabToolOutput, summary="GitLab Deepagent Tool")
async def gitlab_tool(body: GitlabToolInput) -> GitlabToolOutput:
    payload = _clean_payload(body.model_dump())
    result = await _invoke_agent(payload)
    return GitlabToolOutput(content=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
