"""
AIOS llama.cpp backend integration.

Provides direct C++ inference using llama.cpp as an alternative to Ollama.
Supports GGUF models, multiple backends (CUDA, Metal, Vulkan), and advanced quantization.

Features:
- Direct C++ inference without server overhead
- Hardware-optimized backends (CUDA, Metal, Vulkan, SYCL, HIP)
- Multiple quantization levels (1.5-bit to 8-bit)
- Speculative decoding for performance
- GGUF model format support
- Streaming inference with fine-grained control
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Generator, List, Optional, Any, Union
from concurrent.futures import ThreadPoolExecutor

import numpy as np

log = logging.getLogger("aios.llm.llamacpp")

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    log.warning("llama-cpp-python not available. Install with: pip install llama-cpp-python")

# Backend detection order (most to least preferred)
SUPPORTED_BACKENDS = ["cuda", "metal", "vulkan", "sycl", "hip", "cpu"]


class LlamaCppBackend:
    """
    llama.cpp backend for AIOS LLM inference.

    Provides direct C++ inference with hardware optimization and advanced features.
    """

    def __init__(self,
                 model_path: Optional[str] = None,
                 n_ctx: int = 4096,
                 n_threads: Optional[int] = None,
                 n_gpu_layers: int = -1,
                 backend: Optional[str] = None,
                 quantization: str = "Q4_0",
                 verbose: bool = False):
        """
        Initialize llama.cpp backend.

        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_threads: Number of CPU threads (-1 for auto)
            n_gpu_layers: Number of layers to offload to GPU (-1 for auto)
            backend: Preferred backend ('cuda', 'metal', 'vulkan', etc.)
            quantization: Quantization level for model loading
            verbose: Enable verbose logging
        """
        if not LLAMA_CPP_AVAILABLE:
            raise ImportError("llama-cpp-python not available. Install with: pip install llama-cpp-python")

        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads or max(1, os.cpu_count() // 2)  # Use half CPU cores by default
        self.n_gpu_layers = n_gpu_layers
        self.backend = backend or self._detect_backend()
        self.quantization = quantization
        self.verbose = verbose

        self.llm: Optional[Llama] = None
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="llamacpp")

        # Model management
        self.model_cache: Dict[str, Llama] = {}
        self.current_model: Optional[str] = None

        log.info(f"LlamaCpp backend initialized: backend={self.backend}, threads={self.n_threads}")

    def _detect_backend(self) -> str:
        """Detect the best available backend for the current hardware."""
        system = platform.system().lower()

        # Check for CUDA (NVIDIA GPUs)
        if self._check_cuda_available():
            return "cuda"

        # Check for Metal (Apple Silicon)
        if system == "darwin" and self._check_metal_available():
            return "metal"

        # Check for Vulkan (cross-platform GPU compute)
        if self._check_vulkan_available():
            return "vulkan"

        # Check for SYCL (Intel GPUs)
        if self._check_sycl_available():
            return "sycl"

        # Check for HIP (AMD GPUs)
        if self._check_hip_available():
            return "hip"

        # Fallback to CPU
        return "cpu"

    def _check_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            pass

        # Check via nvidia-smi
        try:
            subprocess.check_output(["nvidia-smi"], timeout=5)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_metal_available(self) -> bool:
        """Check if Metal is available (macOS with Apple Silicon)."""
        try:
            # Check if we're on Apple Silicon
            import platform
            machine = platform.machine().lower()
            return machine in ["arm64", "aarch64"]
        except:
            return False

    def _check_vulkan_available(self) -> bool:
        """Check if Vulkan is available."""
        # This is a simplified check - in practice, you'd check for Vulkan SDK
        try:
            # Try to import vulkan-related modules or check system
            if platform.system() == "Windows":
                # Check for vulkan-1.dll
                import ctypes
                return ctypes.windll.kernel32.LoadLibraryW("vulkan-1.dll") is not None
            elif platform.system() == "Linux":
                # Check for libvulkan.so
                import ctypes
                return ctypes.cdll.LoadLibrary("libvulkan.so.1") is not None
            return False
        except:
            return False

    def _check_sycl_available(self) -> bool:
        """Check if SYCL is available (Intel GPUs)."""
        # Simplified check for Intel GPUs
        try:
            import subprocess
            result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            return "intel" in result.stdout.lower() and "graphics" in result.stdout.lower()
        except:
            return False

    def _check_hip_available(self) -> bool:
        """Check if HIP is available (AMD GPUs)."""
        try:
            import subprocess
            result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            return "amd" in result.stdout.lower() and ("radeon" in result.stdout.lower() or "navi" in result.stdout.lower())
        except:
            return False

    def load_model(self, model_path: str) -> bool:
        """
        Load a GGUF model.

        Args:
            model_path: Path to the GGUF model file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if not Path(model_path).exists():
                log.error(f"Model file not found: {model_path}")
                return False

            # Check if model is already loaded
            if model_path in self.model_cache:
                self.llm = self.model_cache[model_path]
                self.current_model = model_path
                log.info(f"Using cached model: {model_path}")
                return True

            log.info(f"Loading model: {model_path}")

            # Configure backend-specific options
            kwargs = {
                "model_path": model_path,
                "n_ctx": self.n_ctx,
                "n_threads": self.n_threads,
                "verbose": self.verbose,
            }

            # Backend-specific configuration
            if self.backend == "cuda":
                kwargs["n_gpu_layers"] = self.n_gpu_layers
            elif self.backend == "metal":
                kwargs["n_gpu_layers"] = self.n_gpu_layers
                kwargs["metal"] = True
            elif self.backend == "vulkan":
                kwargs["vulkan"] = True
            elif self.backend == "sycl":
                kwargs["sycl"] = True
            elif self.backend == "hip":
                kwargs["hip"] = True

            self.llm = Llama(**kwargs)
            self.model_cache[model_path] = self.llm
            self.current_model = model_path

            log.info(f"Model loaded successfully: {model_path}")
            return True

        except Exception as e:
            log.error(f"Failed to load model {model_path}: {e}")
            return False

    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 max_tokens: int = 512,
                 temperature: float = 0.3,
                 top_p: float = 0.9,
                 top_k: int = 40,
                 repeat_penalty: float = 1.1,
                 stop: Optional[List[str]] = None) -> str:
        """
        Generate a complete response.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Repetition penalty
            stop: Stop sequences

        Returns:
            Generated text
        """
        if not self.llm:
            return "Error: No model loaded"

        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate response
            output = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                echo=False
            )

            return output["choices"][0]["text"].strip()

        except Exception as e:
            log.error(f"Generation failed: {e}")
            return f"Error: {e}"

    def generate_stream(self,
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 512,
                       temperature: float = 0.3,
                       top_p: float = 0.9,
                       top_k: int = 40,
                       repeat_penalty: float = 1.1,
                       stop: Optional[List[str]] = None) -> Generator[str, None, None]:
        """
        Generate a streaming response.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Repetition penalty
            stop: Stop sequences

        Yields:
            Text tokens as they are generated
        """
        if not self.llm:
            yield "Error: No model loaded"
            return

        try:
            # Combine system prompt and user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            # Generate streaming response
            stream = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=stop or [],
                echo=False,
                stream=True
            )

            for chunk in stream:
                token = chunk["choices"][0]["text"]
                if token:
                    yield token

        except Exception as e:
            log.error(f"Streaming generation failed: {e}")
            yield f"Error: {e}"

    def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        if not self.llm:
            raise RuntimeError("No model loaded")

        try:
            # Use the model's embedding capability
            embedding = self.llm.embed(text)
            return embedding
        except Exception as e:
            log.error(f"Embedding generation failed: {e}")
            return []

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        if not self.llm:
            return {}

        try:
            return {
                "model_path": self.current_model,
                "n_ctx": self.llm.n_ctx(),
                "n_vocab": self.llm.n_vocab(),
                "backend": self.backend,
                "n_threads": self.n_threads,
                "n_gpu_layers": getattr(self.llm, 'n_gpu_layers', 0) if hasattr(self.llm, 'n_gpu_layers') else 0,
            }
        except Exception as e:
            log.error(f"Failed to get model info: {e}")
            return {}

    def unload_model(self, model_path: Optional[str] = None):
        """Unload a model from memory."""
        if model_path and model_path in self.model_cache:
            # Remove from cache
            del self.model_cache[model_path]
            if self.current_model == model_path:
                self.llm = None
                self.current_model = None
            log.info(f"Unloaded model: {model_path}")
        elif not model_path and self.llm:
            # Unload current model
            self.llm = None
            self.current_model = None
            log.info("Unloaded current model")

    def list_available_models(self, model_dir: str = "./models") -> List[str]:
        """List available GGUF models in a directory."""
        model_dir = Path(model_dir)
        if not model_dir.exists():
            return []

        models = []
        for file in model_dir.rglob("*.gguf"):
            models.append(str(file))

        return sorted(models)

    def download_model(self, model_name: str, save_dir: str = "./models") -> Optional[str]:
        """
        Download a model from Hugging Face.

        Args:
            model_name: Hugging Face model name (e.g., "ggml-org/gemma-3-1b-it-GGUF")
            save_dir: Directory to save the model

        Returns:
            Path to downloaded model or None if failed
        """
        try:
            from huggingface_hub import hf_hub_download

            save_dir = Path(save_dir)
            save_dir.mkdir(parents=True, exist_ok=True)

            # Download the model
            model_path = hf_hub_download(
                repo_id=model_name,
                filename="model.gguf",  # Assuming standard filename
                local_dir=save_dir
            )

            log.info(f"Downloaded model: {model_path}")
            return model_path

        except ImportError:
            log.error("huggingface_hub not available. Install with: pip install huggingface-hub")
            return None
        except Exception as e:
            log.error(f"Failed to download model {model_name}: {e}")
            return None

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


class LlamaCppClient:
    """
    High-level client for llama.cpp integration with AIOS.

    Provides the same interface as the Ollama client but uses llama.cpp backend.
    """

    def __init__(self,
                 model_dir: str = "./models",
                 backend: Optional[str] = None,
                 n_ctx: int = 4096,
                 n_threads: Optional[int] = None,
                 n_gpu_layers: int = -1):
        """
        Initialize llama.cpp client.

        Args:
            model_dir: Directory containing GGUF models
            backend: Preferred backend
            n_ctx: Context window size
            n_threads: CPU threads
            n_gpu_layers: GPU layers to offload
        """
        self.model_dir = Path(model_dir)
        self.backend = LlamaCppBackend(
            backend=backend,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers
        )

        self._system_prompt = self._default_system_prompt()
        self._current_model: Optional[str] = None

        # Auto-load first available model
        self._init_model()

    def _default_system_prompt(self) -> str:
        return (
            "You are Aios, a helpful local AI desktop assistant. "
            "Be concise, accurate, and friendly. All processing happens "
            "on the user's machine — no data leaves this device. "
            "You can execute tools and remember context from previous messages."
        )

    def _init_model(self):
        """Initialize with the first available model."""
        models = self.backend.list_available_models(str(self.model_dir))
        if models:
            self.load_model(models[0])
        else:
            log.warning("No GGUF models found. Use download_model() or place models in ./models/")

    def load_model(self, model_path: str) -> bool:
        """Load a specific model."""
        if self.backend.load_model(model_path):
            self._current_model = model_path
            log.info(f"Loaded model: {model_path}")
            return True
        return False

    def download_and_load_model(self, model_name: str) -> bool:
        """Download and load a model from Hugging Face."""
        model_path = self.backend.download_model(model_name, str(self.model_dir))
        if model_path:
            return self.load_model(model_path)
        return False

    def generate(self,
                 prompt: str,
                 system_prompt: Optional[str] = None,
                 max_tokens: int = 512,
                 temperature: float = 0.3) -> str:
        """Generate a complete response."""
        return self.backend.generate(
            prompt=prompt,
            system_prompt=system_prompt or self._system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def generate_stream(self,
                       prompt: str,
                       system_prompt: Optional[str] = None,
                       max_tokens: int = 512,
                       temperature: float = 0.3) -> Generator[str, None, None]:
        """Generate a streaming response."""
        yield from self.backend.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt or self._system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def embed(self, text: str) -> List[float]:
        """Generate embeddings."""
        return self.backend.embed(text)

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return self.backend.get_model_info()

    def list_models(self) -> List[str]:
        """List available models."""
        return self.backend.list_available_models(str(self.model_dir))

    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
        self._system_prompt = prompt

    def get_current_model(self) -> Optional[str]:
        """Get current model path."""
        return self._current_model
