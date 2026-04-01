"""
Aios LLM wrapper — Ollama SDK with streaming and hardware-aware model selection.
"""

import logging
from typing import Generator, Optional

import ollama
from ollama import ResponseError

from hardware import detect, recommend_model

log = logging.getLogger("aios.llm")

_selected_model: Optional[str] = None
_hw_info: Optional[dict] = None
_system_prompt: str = (
    "You are Aios, a helpful local AI desktop assistant. "
    "Be concise, accurate, and friendly. All processing happens "
    "on the user's machine — no data leaves this device."
)


def init() -> dict:
    """Detect hardware, pick the best model, return status dict."""
    global _selected_model, _hw_info

    _hw_info = detect()
    available = _list_models()
    _selected_model = recommend_model(_hw_info, available)

    status = {
        "model": _selected_model,
        "available_models": available,
        **_hw_info,
    }
    log.info("Aios LLM init: model=%s  gpu=%s  vram=%.1fGB",
             _selected_model, _hw_info.get("gpu_name", "none"),
             _hw_info.get("vram_gb", 0))
    return status


def get_model() -> str:
    if _selected_model is None:
        init()
    return _selected_model  # type: ignore[return-value]


def get_hw_info() -> dict:
    if _hw_info is None:
        init()
    return _hw_info  # type: ignore[return-value]


def set_model(model: str) -> None:
    global _selected_model
    _selected_model = model


def ask_llm(prompt: str) -> str:
    """Blocking call — returns the full response (backward-compatible)."""
    try:
        response = ollama.chat(
            model=get_model(),
            messages=[
                {"role": "system", "content": _system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        return response.message.content or "Empty response."
    except ResponseError as e:
        if e.status_code == 404:
            return f"Model '{get_model()}' not found. Run: ollama pull {get_model()}"
        return f"Ollama error: {e.error}"
    except Exception as e:
        return f"LLM Error: {e}"


def ask_llm_stream(prompt: str) -> Generator[str, None, None]:
    """Streaming call — yields tokens as they arrive."""
    try:
        stream = ollama.chat(
            model=get_model(),
            messages=[
                {"role": "system", "content": _system_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            token = chunk.message.content
            if token:
                yield token
    except ResponseError as e:
        if e.status_code == 404:
            yield f"Model '{get_model()}' not found. Run: ollama pull {get_model()}"
        else:
            yield f"Ollama error: {e.error}"
    except Exception as e:
        yield f"LLM Error: {e}"



def stream_with_history(
    system_prompt: str,
    history: list[dict],
    user_input: str,
) -> Generator[str, None, None]:
    """
    Stream a response using full conversation history for context.

    *history* is a list of {role, content} dicts in chronological order.
    The current user message is appended automatically.
    """
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_input})

    try:
        stream = ollama.chat(
            model=get_model(),
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            token = chunk.message.content
            if token:
                yield token
    except ResponseError as e:
        if e.status_code == 404:
            yield f"Model '{get_model()}' not found. Run: ollama pull {get_model()}"
        else:
            yield f"Ollama error: {e.error}"
    except Exception as e:
        yield f"LLM Error: {e}"


def list_models() -> list[str]:
    return _list_models()


def _list_models() -> list[str]:
    try:
        resp = ollama.list()
        return [m.model for m in resp.models] if resp.models else []
    except Exception as e:
        log.warning("Could not list models: %s", e)
        return []