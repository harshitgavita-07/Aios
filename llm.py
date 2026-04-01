"""
Aios LLM wrapper — Ollama SDK with streaming and hardware-aware model selection.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

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


class LLMClient:
    """
    Enhanced LLM client with caching and performance optimizations.
    
    Features:
    - Response caching for common queries
    - Model warm-up on initialization
    - Hardware-aware model selection
    - Streaming support
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._selected_model: Optional[str] = None
        self._hw_info: Optional[dict] = None
        self._system_prompt: str = self._default_system_prompt()
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True
        self._max_cache_size = 100
        
        self.cache_dir = cache_dir or Path(__file__).parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize hardware and model
        self._init_hardware()
        
        log.info(f"LLMClient initialized: model={self._selected_model}")

    def _default_system_prompt(self) -> str:
        return (
            "You are Aios, a helpful local AI desktop assistant. "
            "Be concise, accurate, and friendly. All processing happens "
            "on the user's machine — no data leaves this device. "
            "You can execute tools and remember context from previous messages."
        )

    def _init_hardware(self):
        """Detect hardware and select optimal model."""
        self._hw_info = detect()
        available = self._list_models()
        self._selected_model = recommend_model(self._hw_info, available)
        
        log.info(f"Hardware: {self._hw_info.get('gpu_name', 'CPU')}, "
                 f"VRAM: {self._hw_info.get('vram_gb', 0):.1f}GB")
        
        # Warm up the model
        self._warmup()

    def _warmup(self):
        """
        Warm up the model with a simple query.
        """
        try:
            log.info(f"Warming up model: {self._selected_model}")
            # Simple warm-up query
            ollama.chat(
                model=self._selected_model,
                messages=[{"role": "user", "content": "Hi"}],
                options={"temperature": 0}
            )
            log.info("Model warm-up complete")
        except Exception as e:
            log.warning(f"Model warm-up failed: {e}")

    def _list_models(self) -> List[str]:
        """List available models."""
        try:
            resp = ollama.list()
            return [m.model for m in resp.models] if resp.models else []
        except Exception as e:
            log.warning(f"Could not list models: {e}")
            return []

    def _get_cache_key(self, messages: List[Dict], model: str) -> str:
        """Generate cache key from messages."""
        content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[str]:
        """Get cached response if available."""
        if not self._cache_enabled:
            return None
        
        if key in self._cache:
            entry = self._cache[key]
            # Cache valid for 1 hour
            if time.time() - entry["timestamp"] < 3600:
                log.debug("Cache hit")
                return entry["response"]
            else:
                del self._cache[key]
        
        return None

    def _set_cached(self, key: str, response: str):
        """Cache a response."""
        if not self._cache_enabled:
            return
        
        # Limit cache size
        if len(self._cache) >= self._max_cache_size:
            # Remove oldest entry
            oldest = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest]
        
        self._cache[key] = {
            "response": response,
            "timestamp": time.time()
        }

    def generate(self, 
                 prompt: str, 
                 system_prompt: Optional[str] = None,
                 context: Optional[List[Dict]] = None) -> str:
        """
        Generate a complete response (non-streaming).
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        
        # Check cache
        cache_key = self._get_cache_key(messages, self._selected_model)
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            response = ollama.chat(
                model=self._selected_model,
                messages=messages,
                options={"temperature": 0.7}
            )
            result = response.message.content or ""
            
            # Cache the result
            self._set_cached(cache_key, result)
            
            return result
        except ResponseError as e:
            if e.status_code == 404:
                return f"Model '{self._selected_model}' not found. Run: ollama pull {self._selected_model}"
            return f"Ollama error: {e.error}"
        except Exception as e:
            return f"LLM Error: {e}"

    def generate_stream(self, 
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       context: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """
        Generate a streaming response.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = ollama.chat(
                model=self._selected_model,
                messages=messages,
                stream=True,
                options={"temperature": 0.7}
            )
            
            for chunk in stream:
                token = chunk.message.content
                if token:
                    yield token
                    
        except ResponseError as e:
            if e.status_code == 404:
                yield f"Model '{self._selected_model}' not found. Run: ollama pull {self._selected_model}"
            else:
                yield f"Ollama error: {e.error}"
        except Exception as e:
            yield f"LLM Error: {e}"

    def get_model(self) -> str:
        """Get currently selected model."""
        return self._selected_model

    def set_model(self, model: str):
        """Set active model."""
        self._selected_model = model
        log.info(f"Model changed to: {model}")
        self._warmup()

    def get_hardware_info(self) -> Dict:
        """Get hardware information."""
        return self._hw_info or {}

    def list_available_models(self) -> List[str]:
        """List all available models."""
        return self._list_models()