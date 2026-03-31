"""
core/ollama_client.py

Direct Ollama HTTP client.
Endpoint: http://localhost:11434/api/generate
Supports streaming and blocking generation.
"""

from __future__ import annotations

import json
import logging
from typing import Generator, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

log = logging.getLogger("aios.ollama")

OLLAMA_BASE = "http://localhost:11434"


def generate(
    prompt: str,
    model: str = "llama3",
    system: str = "",
    stream: bool = False,
    temperature: float = 0.7,
    timeout: int = 120,
) -> str:
    """
    Blocking generation via Ollama /api/generate.
    Returns the full response string.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": temperature},
    }
    body = json.dumps(payload).encode()
    req = Request(
        f"{OLLAMA_BASE}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data.get("response", "").strip()
    except URLError as e:
        raise ConnectionError(
            f"Ollama not reachable at {OLLAMA_BASE}. "
            "Is Ollama running? Try: ollama serve"
        ) from e


def generate_stream(
    prompt: str,
    model: str = "llama3",
    system: str = "",
    temperature: float = 0.7,
    timeout: int = 120,
) -> Generator[str, None, None]:
    """
    Streaming generation via Ollama /api/generate.
    Yields tokens as they arrive.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": True,
        "options": {"temperature": temperature},
    }
    body = json.dumps(payload).encode()
    req = Request(
        f"{OLLAMA_BASE}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue
    except URLError as e:
        raise ConnectionError(
            f"Ollama not reachable at {OLLAMA_BASE}. "
            "Is Ollama running? Try: ollama serve"
        ) from e


def list_models() -> list[str]:
    """Return names of locally installed Ollama models."""
    req = Request(f"{OLLAMA_BASE}/api/tags", method="GET")
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return [m["name"] for m in data.get("models", [])]
    except URLError:
        return []


def health_check() -> bool:
    """Return True if Ollama is running and reachable."""
    try:
        with urlopen(f"{OLLAMA_BASE}/api/tags", timeout=5):
            return True
    except URLError:
        return False
