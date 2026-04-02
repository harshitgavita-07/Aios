"""
Unified LLM interface for AIOS.

Supports multiple backends: Ollama (default) and llama.cpp for enhanced performance.
Automatically selects the best backend based on hardware and available models.
"""

import logging
from typing import Dict, List, Optional, Generator, Any, Union
from pathlib import Path

from .hardware import detect, recommend_model, recommend_gguf_model, get_llamacpp_config

log = logging.getLogger("aios.llm_unified")

# Try to import backends
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    log.warning("Ollama not available. Install with: pip install ollama")

try:
    from .llm_llamacpp import LlamaCppClient
    LLAMACPP_AVAILABLE = True
except ImportError:
    LLAMACPP_AVAILABLE = False
    log.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")


class UnifiedLLMClient:
    """
    Unified LLM client that supports multiple backends.

    Features:
    - Automatic backend selection based on hardware and available models
    - Seamless switching between Ollama and llama.cpp
    - Hardware-aware model selection
    - Unified API for all operations
    """

    def __init__(self,
                 preferred_backend: Optional[str] = None,
                 model_dir: str = "./models",
                 ollama_host: str = "http://localhost:8080"):
        """
        Initialize unified LLM client.

        Args:
            preferred_backend: Preferred backend ('ollama', 'llamacpp', or 'auto')
            model_dir: Directory for GGUF models
            ollama_host: Ollama server host
        """
        self.preferred_backend = preferred_backend or "auto"
        self.model_dir = Path(model_dir)
        self.ollama_host = ollama_host

        # Backend clients
        self.ollama_client = None
        self.llamacpp_client = None

        # Current backend and model
        self.current_backend: Optional[str] = None
        self.current_model: Optional[str] = None

        # Hardware info
        self.hw_info = detect()

        # System prompt
        self._system_prompt = self._default_system_prompt()

        # Initialize backends
        self._init_backends()

        log.info(f"UnifiedLLM initialized: backend={self.current_backend}, model={self.current_model}")

    def _default_system_prompt(self) -> str:
        return (
            "You are Aios, a helpful local AI desktop assistant. "
            "Be concise, accurate, and friendly. All processing happens "
            "on the user's machine — no data leaves this device. "
            "You can execute tools and remember context from previous messages."
        )

    def _init_backends(self):
        """Initialize available backends and select the best one."""
        available_backends = []

        # Initialize Ollama if available
        if OLLAMA_AVAILABLE:
            try:
                # Test Ollama connection
                ollama.list()
                self.ollama_client = ollama
                available_backends.append("ollama")
                log.info("Ollama backend available")
            except Exception as e:
                log.warning(f"Ollama not available: {e}")

        # Initialize llama.cpp if available
        if LLAMACPP_AVAILABLE:
            try:
                self.llamacpp_client = LlamaCppClient(
                    model_dir=str(self.model_dir),
                    backend=self.hw_info.get("recommended_llamacpp_backend", "cpu")
                )
                available_backends.append("llamacpp")
                log.info("llama.cpp backend available")
            except Exception as e:
                log.warning(f"llama.cpp initialization failed: {e}")

        if not available_backends:
            raise RuntimeError("No LLM backends available. Install Ollama or llama-cpp-python.")

        # Select backend
        self.current_backend = self._select_backend(available_backends)

        # Select model
        self.current_model = self._select_model()

        log.info(f"Selected backend: {self.current_backend}, model: {self.current_model}")

    def _select_backend(self, available_backends: List[str]) -> str:
        """Select the best backend based on preferences and availability."""
        if self.preferred_backend == "auto":
            # Auto-selection logic
            if "llamacpp" in available_backends and self.hw_info.get("vram_gb", 0) > 2:
                # Prefer llama.cpp for systems with decent GPU memory
                return "llamacpp"
            elif "ollama" in available_backends:
                # Fallback to Ollama
                return "ollama"
            else:
                # Use first available
                return available_backends[0]
        else:
            # Use preferred backend if available
            if self.preferred_backend in available_backends:
                return self.preferred_backend
            else:
                log.warning(f"Preferred backend '{self.preferred_backend}' not available, using {available_backends[0]}")
                return available_backends[0]

    def _select_model(self) -> Optional[str]:
        """Select the best model for the current backend."""
        if self.current_backend == "ollama":
            available_models = self._list_ollama_models()
            return recommend_model(self.hw_info, available_models)
        elif self.current_backend == "llamacpp":
            available_models = self._list_llamacpp_models()
            backend = self.hw_info.get("recommended_llamacpp_backend", "cpu")
            recommended = recommend_gguf_model(self.hw_info, available_models, backend)
            # Try to load the recommended model
            if self.llamacpp_client and available_models:
                model_path = self._find_gguf_model(recommended)
                if model_path and self.llamacpp_client.load_model(model_path):
                    return model_path
                # Fallback to first available
                elif available_models:
                    model_path = self._find_gguf_model(available_models[0])
                    if model_path:
                        self.llamacpp_client.load_model(model_path)
                        return model_path
        return None

    def _list_ollama_models(self) -> List[str]:
        """List available Ollama models."""
        if not self.ollama_client:
            return []
        try:
            resp = self.ollama_client.list()
            return [m.model for m in resp.models] if resp.models else []
        except Exception as e:
            log.warning(f"Failed to list Ollama models: {e}")
            return []

    def _list_llamacpp_models(self) -> List[str]:
        """List available llama.cpp models (GGUF files)."""
        if not self.llamacpp_client:
            return []

        models = []
        for file in self.model_dir.rglob("*.gguf"):
            # Extract model name from filename
            name = file.stem
            # Remove common suffixes
            for suffix in ["-q4_0", "-q4_1", "-q5_0", "-q5_1", "-q8_0", "-f16", "-f32"]:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            models.append(name)

        return list(set(models))  # Remove duplicates

    def _find_gguf_model(self, model_name: str) -> Optional[str]:
        """Find the GGUF file for a model name."""
        # Look for exact matches first
        for file in self.model_dir.rglob("*.gguf"):
            if file.stem == model_name or file.stem.startswith(model_name + "-"):
                return str(file)

        # Look for partial matches
        for file in self.model_dir.rglob("*.gguf"):
            if model_name in file.stem:
                return str(file)

        return None

    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 max_tokens: int = 512,
                 temperature: float = 0.3,
                 **kwargs) -> str:
        """
        Generate a complete response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional backend-specific parameters

        Returns:
            Generated text
        """
        system_prompt = system_prompt or self._system_prompt

        if self.current_backend == "ollama":
            return self._generate_ollama(prompt, system_prompt, max_tokens, temperature, **kwargs)
        elif self.current_backend == "llamacpp":
            return self._generate_llamacpp(prompt, system_prompt, max_tokens, temperature, **kwargs)
        else:
            raise RuntimeError(f"Unsupported backend: {self.current_backend}")

    def generate_stream(self,
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 512,
                       temperature: float = 0.3,
                       **kwargs) -> Generator[str, None, None]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional backend-specific parameters

        Yields:
            Text tokens as they are generated
        """
        system_prompt = system_prompt or self._system_prompt

        if self.current_backend == "ollama":
            yield from self._generate_ollama_stream(prompt, system_prompt, max_tokens, temperature, **kwargs)
        elif self.current_backend == "llamacpp":
            yield from self._generate_llamacpp_stream(prompt, system_prompt, max_tokens, temperature, **kwargs)
        else:
            yield f"Error: Unsupported backend: {self.current_backend}"

    def _generate_ollama(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Generate using Ollama backend."""
        if not self.ollama_client or not self.current_model:
            return "Error: Ollama backend not available"

        try:
            response = self.ollama_client.chat(
                model=self.current_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **kwargs
                }
            )
            return response.message.content or "Empty response."
        except Exception as e:
            return f"Ollama error: {e}"

    def _generate_llamacpp(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float, **kwargs) -> str:
        """Generate using llama.cpp backend."""
        if not self.llamacpp_client:
            return "Error: llama.cpp backend not available"

        return self.llamacpp_client.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def _generate_ollama_stream(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float, **kwargs) -> Generator[str, None, None]:
        """Generate streaming response using Ollama."""
        if not self.ollama_client or not self.current_model:
            yield "Error: Ollama backend not available"
            return

        try:
            stream = self.ollama_client.chat(
                model=self.current_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **kwargs
                }
            )
            for chunk in stream:
                token = chunk.message.content
                if token:
                    yield token
        except Exception as e:
            yield f"Ollama error: {e}"

    def _generate_llamacpp_stream(self, prompt: str, system_prompt: str, max_tokens: int, temperature: float, **kwargs) -> Generator[str, None, None]:
        """Generate streaming response using llama.cpp."""
        if not self.llamacpp_client:
            yield "Error: llama.cpp backend not available"
            return

        yield from self.llamacpp_client.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        if self.current_backend == "llamacpp" and self.llamacpp_client:
            return self.llamacpp_client.embed(text)
        else:
            # Ollama doesn't have built-in embeddings, return empty
            log.warning("Embeddings not supported in current backend")
            return []

    def switch_backend(self, backend: str) -> bool:
        """
        Switch to a different backend.

        Args:
            backend: Backend to switch to ('ollama' or 'llamacpp')

        Returns:
            True if successful, False otherwise
        """
        if backend not in ["ollama", "llamacpp"]:
            log.error(f"Unsupported backend: {backend}")
            return False

        if backend == "ollama" and not self.ollama_client:
            log.error("Ollama backend not available")
            return False

        if backend == "llamacpp" and not self.llamacpp_client:
            log.error("llama.cpp backend not available")
            return False

        self.current_backend = backend
        self.current_model = self._select_model()

        log.info(f"Switched to backend: {backend}, model: {self.current_model}")
        return True

    def download_llamacpp_model(self, model_name: str) -> bool:
        """
        Download a GGUF model for llama.cpp.

        Args:
            model_name: Hugging Face model name (e.g., "ggml-org/gemma-3-1b-it-GGUF")

        Returns:
            True if successful, False otherwise
        """
        if not self.llamacpp_client:
            log.error("llama.cpp backend not available")
            return False

        return self.llamacpp_client.download_and_load_model(model_name)

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model and backend."""
        info = {
            "backend": self.current_backend,
            "model": self.current_model,
            "hardware": self.hw_info,
        }

        if self.current_backend == "llamacpp" and self.llamacpp_client:
            info["llamacpp_info"] = self.llamacpp_client.get_model_info()

        return info

    def list_available_models(self) -> Dict[str, List[str]]:
        """List available models for all backends."""
        return {
            "ollama": self._list_ollama_models(),
            "llamacpp": self._list_llamacpp_models(),
        }

    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
        self._system_prompt = prompt

    def get_current_backend(self) -> Optional[str]:
        """Get current backend."""
        return self.current_backend

    def get_current_model(self) -> Optional[str]:
        """Get current model."""
        return self.current_model</content>
<parameter name="filePath">c:\Users\HARSHIT\Aios\llm_unified.py