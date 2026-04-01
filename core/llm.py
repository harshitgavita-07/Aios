"""
LLM Client — Enhanced Ollama wrapper with streaming and caching
"""

import logging
from typing import Generator, Optional, List, Dict, Any
from pathlib import Path
import json
import hashlib
import time

import ollama
from ollama import ResponseError

import sys as _sys
import os as _os
# hardware.py lives at the repo root, not inside a package.
# Add the repo root to sys.path so it can be imported regardless of the
# working directory the user launches AIOS from (fixes Windows CWD issues).
_repo_root = str(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if _repo_root not in _sys.path:
    _sys.path.insert(0, _repo_root)

try:
    from hardware import detect, recommend_model
    _HARDWARE_AVAILABLE = True
except ImportError:
    _HARDWARE_AVAILABLE = False
    def detect() -> dict:
        return {"cpu_cores": _os.cpu_count() or 4, "ram_gb": 8.0,
                "gpu_name": "", "vram_gb": 0.0, "backend": "cpu"}
    def recommend_model(hw: dict, available: list) -> str:
        preferred = ["qwen2.5:7b", "llama3.2:3b", "mistral:7b", "phi3:mini"]
        for m in preferred:
            if m in available:
                return m
        return available[0] if available else "llama3.2:3b"

log = logging.getLogger("aios.llm")


class LLMClient:
    """
    Enhanced LLM client with caching and performance optimizations.
    
    Features:
    - Response caching for common queries
    - Model warm-up on initialization
    - Hardware-aware model selection
    - Streaming support
    
    Change: Enhanced LLM client with caching
    Why:
    - Repeated queries waste tokens
    - Cold start causes delay on first use
    Impact:
    - Faster response times
    - Better resource utilization
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._selected_model: Optional[str] = None
        self._hw_info: Optional[dict] = None
        self._system_prompt: str = self._default_system_prompt()
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True
        self._max_cache_size = 100
        
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "cache"
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
        
        Change: Model warm-up on init
        Why:
        - First query is slow due to model loading
        - Pre-loading improves UX
        Impact:
        - Faster first response
        - Better user experience
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
        
        Change: Unified generation interface with caching
        Why:
        - Simpler API for callers
        - Caching reduces redundant calls
        Impact:
        - Consistent response generation
        - Better performance
        """
        messages = []
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
        
        Change: Streaming generation with proper error handling
        Why:
        - UI needs streaming for responsiveness
        - Better user experience with real-time tokens
        Impact:
        - Non-blocking UI updates
        - Real-time feedback
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

    def clear_cache(self):
        """Clear response cache."""
        self._cache.clear()
        log.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get client statistics."""
        return {
            "model": self._selected_model,
            "cache_size": len(self._cache),
            "cache_enabled": self._cache_enabled,
            "hardware": self._hw_info
        }
