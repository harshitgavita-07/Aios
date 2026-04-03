"""
AIOS Configuration for LLM backends.

This file contains configuration settings for different LLM backends
and hardware-specific optimizations.
"""

from typing import Dict, Any

# LLM Backend Configuration
LLM_CONFIG = {
    "default_backend": "auto",  # 'auto', 'ollama', or 'llamacpp'
    "ollama": {
        "host": "http://localhost:11434",
        "timeout": 30,
        "retries": 3,
    },
    "llamacpp": {
        "model_dir": "./models",
        "default_quantization": "Q4_0",
        "n_ctx": 4096,
        "n_threads": None,  # Auto-detect
        "n_gpu_layers": -1,  # Auto-detect
        "verbose": False,
        "backend": None,  # Auto-detect
        "enable_embeddings": True,
    },
}

# Hardware-specific configurations
HARDWARE_CONFIG = {
    "cpu": {
        "n_threads": "auto",  # Use half of available cores
        "n_gpu_layers": 0,
        "memory_fraction": 0.3,  # Use 30% of RAM for model
    },
    "cuda": {
        "n_threads": 4,
        "n_gpu_layers": -1,  # All layers on GPU
        "memory_fraction": 0.8,  # Use 80% of VRAM
        "tensor_cores": True,
    },
    "metal": {
        "n_threads": 4,
        "n_gpu_layers": -1,
        "memory_fraction": 0.8,
    },
    "vulkan": {
        "n_threads": 4,
        "n_gpu_layers": -1,
        "memory_fraction": 0.7,
    },
}

# Model configurations for different backends
MODEL_CONFIG = {
    "ollama": {
        "fallback_model": "llama3.2:1b",
        "model_tiers": [
            (4.0, ["llama3.2:1b", "phi3:mini", "gemma2:2b"]),
            (6.0, ["llama3.2:3b", "phi3:3.8b"]),
            (10.0, ["llama3.1:8b", "gemma3:12b"]),
            (16.0, ["qwen2.5:14b", "deepseek-r1:14b"]),
            (24.0, ["qwen2.5:32b", "deepseek-r1:32b"]),
        ],
    },
    "llamacpp": {
        "fallback_model": "gemma-3-1b-it",
        "model_tiers": [
            (2.0, ["gemma-3-1b-it", "phi-3-mini-4k-instruct"]),
            (4.0, ["gemma-3-4b-it", "phi-3-medium-4k-instruct"]),
            (8.0, ["llama-3.2-3b-instruct", "mistral-7b-instruct-v0.1"]),
            (12.0, ["llama-3.1-8b-instruct", "gemma-3-12b-it"]),
            (24.0, ["qwen2.5-32b-instruct"]),
        ],
        "quantization_options": {
            "Q2_K": {"description": "2-bit quantization, smallest size", "quality": "low"},
            "Q3_K": {"description": "3-bit quantization, good balance", "quality": "medium"},
            "Q4_0": {"description": "4-bit quantization, recommended", "quality": "high"},
            "Q4_1": {"description": "4-bit quantization variant", "quality": "high"},
            "Q5_0": {"description": "5-bit quantization, high quality", "quality": "very_high"},
            "Q5_1": {"description": "5-bit quantization variant", "quality": "very_high"},
            "Q6_K": {"description": "6-bit quantization, very high quality", "quality": "ultra"},
            "Q8_0": {"description": "8-bit quantization, near lossless", "quality": "ultra"},
        },
    },
}

# Performance tuning
PERFORMANCE_CONFIG = {
    "caching": {
        "enabled": True,
        "max_cache_size": 100,
        "cache_ttl_seconds": 3600,  # 1 hour
    },
    "streaming": {
        "chunk_size": 50,
        "buffer_size": 1000,
    },
    "inference": {
        "default_temperature": 0.3,
        "default_max_tokens": 512,
        "repeat_penalty": 1.1,
        "top_p": 0.9,
        "top_k": 40,
    },
}

# Feature flags
FEATURE_FLAGS = {
    "llamacpp_backend": True,
    "speculative_decoding": False,  # Experimental
    "multimodal_support": False,    # Future feature
    "function_calling": True,
    "embeddings": True,
}

def get_llm_config(backend: str = "auto") -> Dict[str, Any]:
    """Get configuration for specified backend."""
    if backend == "auto":
        backend = LLM_CONFIG["default_backend"]

    config = LLM_CONFIG.copy()
    if backend in config:
        config.update(config[backend])

    return config

def get_hardware_config(backend: str) -> Dict[str, Any]:
    """Get hardware-specific configuration."""
    return HARDWARE_CONFIG.get(backend, HARDWARE_CONFIG["cpu"])

def get_model_config(backend: str) -> Dict[str, Any]:
    """Get model configuration for backend."""
    return MODEL_CONFIG.get(backend, MODEL_CONFIG["ollama"])

def get_performance_config() -> Dict[str, Any]:
    """Get performance configuration."""
    return PERFORMANCE_CONFIG

def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled."""
    return FEATURE_FLAGS.get(feature, False)
