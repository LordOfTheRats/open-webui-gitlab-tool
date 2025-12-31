"""Shared model initialization utilities for agents."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from langchain.chat_models import init_chat_model

try:  # Optional import; only needed when using Ollama.
    from langchain_ollama import ChatOllama  # type: ignore
except ImportError:  # pragma: no cover - handled at runtime
    ChatOllama = None  # type: ignore


def model_options(
    *,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
) -> Dict[str, Any]:
    """Collect model kwargs, omitting unset values."""

    opts: Dict[str, Any] = {}
    if temperature is not None:
        opts["temperature"] = temperature
    if top_p is not None:
        opts["top_p"] = top_p
    if top_k is not None:
        opts["top_k"] = top_k
    return opts


def make_model(model_name: str, ollama_base_url: Optional[str], **model_kwargs: Any):
    """Return a LangChain chat model, supporting Ollama via the `ollama:` prefix."""

    if model_name.startswith("ollama:"):
        if ChatOllama is None:
            raise ImportError(
                "Install langchain-ollama to use Ollama models (pip install langchain-ollama)."
            )

        ollama_model = model_name.split("ollama:", 1)[1] or "llama3"
        base_url = ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return ChatOllama(model=ollama_model, base_url=base_url, **model_kwargs)

    return init_chat_model(model_name, **model_kwargs)


def resolve_model_override(
    *,
    base_model_name: str,
    base_model: Any,
    ollama_base_url: Optional[str],
    override: Optional[Any],
):
    """Resolve a model given an optional override value.

    - None -> reuse base_model
    - str -> treat as model name
    - dict -> look for "model"/"model_name" plus any model kwargs
    """

    if override is None:
        return base_model

    if isinstance(override, str):
        return make_model(override, ollama_base_url)

    if isinstance(override, dict):
        override_name = override.get("model") or override.get("model_name") or base_model_name
        model_opts = {k: v for k, v in override.items() if k not in {"model", "model_name"}}
        return make_model(override_name, ollama_base_url, **model_opts)

    return base_model
