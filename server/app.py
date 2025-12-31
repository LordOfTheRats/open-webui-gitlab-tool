"""FastAPI server exposing the GitLab Deepagents agent with a simple htmx UI."""

from __future__ import annotations

import json
import os
from html import escape
from typing import Any, Dict, Optional

import anyio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from agents.gitlab_deepagent import run_once

app = FastAPI(title="GitLab Agent Server", version="1.0.0")
templates = Jinja2Templates(directory="server/templates")


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
        "model": os.getenv("GITLAB_AGENT_MODEL", "openai:gpt-4o"),
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
    if "application/json" in content_type:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="JSON body must be an object")
        return _clean_payload(data)

    form = await request.form()
    return _clean_payload(dict(form))


async def _invoke_agent(clean_payload: Dict[str, Any]) -> Any:
    return await anyio.to_thread.run_sync(
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
    payload = await _parse_request_payload(request)
    try:
        result = await _invoke_agent(payload)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc))

    if _detect_hx(request):
        rendered = _fmt_result(result)
        return HTMLResponse(f"<div class=\"result\"><pre>{escape(rendered)}</pre></div>")

    return JSONResponse({"result": result})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )
