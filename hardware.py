"""
Aios hardware detection & model recommendation.

Detects GPU VRAM, CPU cores, total RAM and recommends the best
Ollama model from the locally available models.

Optional: uses pyaccelerate (v0.9+) for richer hardware profiling.
Also supports llama.cpp backend detection for direct C++ inference.
"""

import logging
import platform
import subprocess

log = logging.getLogger("aios.hardware")

# ── Hardware data ─────────────────────────────────────────────────────────


def detect() -> dict:
    """Return a dict with cpu_cores, ram_gb, gpu_name, vram_gb, and v10 extras."""
    info = {
        "cpu_cores": _cpu_cores(),
        "ram_gb": _ram_gb(),
        "gpu_name": "",
        "vram_gb": 0.0,
        "shared_vram_gb": 0.0,
        "backend": "cpu",
        # v10 extended GPU fields
        "architecture": "",
        "cuda_cores": 0,
        "tensor_cores": 0,
        "has_tensor": False,
        "has_hw_encode": False,
        "has_hw_decode": False,
        "memory_type": "",
        "memory_bandwidth_gbps": 0.0,
        "boost_clock_mhz": 0,
        "pcie_gen": 0,
        "driver_version": "",
        "features": [],
        # llama.cpp backend detection
        "llamacpp_backends": _detect_llamacpp_backends(),
        "recommended_llamacpp_backend": "",
    }

    # Try pyaccelerate first (richer data)
    try:
        from pyaccelerate.gpu import detect_all, best_gpu

        gpus = detect_all()
        if gpus:
            top = best_gpu()
            info["gpu_name"] = top.name
            info["vram_gb"] = round(top.memory_gb, 1)
            info["shared_vram_gb"] = round(top.shared_memory_gb, 1)
            info["backend"] = top.backend
            # v10 extended fields
            info["architecture"] = getattr(top, "architecture", "")
            info["cuda_cores"] = getattr(top, "cuda_cores", 0)
            info["tensor_cores"] = getattr(top, "tensor_cores", 0)
            info["has_tensor"] = getattr(top, "has_tensor", False)
            info["has_hw_encode"] = getattr(top, "has_nvenc", False)
            info["has_hw_decode"] = getattr(top, "has_nvdec", False)
            info["memory_type"] = getattr(top, "memory_type", "")
            info["memory_bandwidth_gbps"] = getattr(top, "memory_bandwidth_gbps", 0.0)
            info["boost_clock_mhz"] = getattr(top, "boost_clock_mhz", 0)
            info["pcie_gen"] = getattr(top, "pcie_gen", 0)
            info["driver_version"] = getattr(top, "driver_version", "")
            info["features"] = getattr(top, "features", [])
            return info
    except Exception:
        pass

    # Fallback: nvidia-smi
    gpu_name, vram = _nvidia_smi()
    if gpu_name:
        info["gpu_name"] = gpu_name
        info["vram_gb"] = vram
        info["backend"] = "cuda"

    # Set recommended llama.cpp backend
    info["recommended_llamacpp_backend"] = _get_recommended_llamacpp_backend(info)

    return info


# ── Model recommendation ─────────────────────────────────────────────────

# (max_vram_gb, preferred_models)  — first match wins
_MODEL_TIERS: list[tuple[float, list[str]]] = [
    (4.0, ["llama3.2:1b", "phi3:mini", "gemma2:2b", "qwen2.5:1.5b"]),
    (6.0, ["llama3.2:3b", "phi3:3.8b", "gemma2:2b", "qwen2.5:3b"]),
    (10.0, ["llama3.1:8b", "gemma3:12b", "qwen2.5:7b", "mistral:7b"]),
    (16.0, ["llama3.1:8b", "gemma3:12b", "qwen2.5:14b", "deepseek-r1:14b"]),
    (24.0, ["qwen2.5:32b", "deepseek-r1:32b", "llama3.1:8b"]),
    (999.0, ["llama3.1:70b", "qwen2.5:72b", "deepseek-r1:70b", "llama3.1:8b"]),
]

# GGUF model tiers for llama.cpp (model_size_gb, preferred_gguf_models)
_GGUF_MODEL_TIERS: list[tuple[float, list[str]]] = [
    (2.0, ["gemma-3-1b-it", "phi-3-mini-4k-instruct", "qwen2.5-1.5b-instruct"]),
    (4.0, ["gemma-3-4b-it", "phi-3-medium-4k-instruct", "qwen2.5-3b-instruct"]),
    (8.0, ["llama-3.2-3b-instruct", "mistral-7b-instruct-v0.1", "qwen2.5-7b-instruct"]),
    (12.0, ["llama-3.1-8b-instruct", "gemma-3-12b-it", "qwen2.5-14b-instruct"]),
    (24.0, ["qwen2.5-32b-instruct", "llama-3.1-8b-instruct"]),
    (999.0, ["qwen2.5-72b-instruct", "llama-3.1-70b-instruct"]),
]

_FALLBACK_MODEL = "llama3.2:1b"
_FALLBACK_GGUF_MODEL = "gemma-3-1b-it"


def recommend_model(hw: dict, available_models: list[str]) -> str:
    """Pick the best model from *available_models* for the detected hardware."""
    if not available_models:
        return _FALLBACK_MODEL

    vram = hw.get("vram_gb", 0.0)
    # No GPU → treat as 2 GB budget (CPU-only, small model)
    budget = vram if vram > 0 else min(hw.get("ram_gb", 4.0) / 4, 4.0)

    for max_vram, preferred in _MODEL_TIERS:
        if budget <= max_vram:
            for tag in preferred:
                if tag in available_models:
                    return tag
            break

    # Nothing matched the tier — return the smallest available model
    return available_models[0] if available_models else _FALLBACK_MODEL


def recommend_gguf_model(hw: dict, available_models: list[str], backend: str = "cpu") -> str:
    """
    Pick the best GGUF model from *available_models* for the detected hardware and backend.

    Args:
        hw: Hardware info dict from detect()
        available_models: List of available GGUF model names
        backend: llama.cpp backend ('cuda', 'cpu', etc.)

    Returns:
        Recommended model name
    """
    if not available_models:
        return _FALLBACK_GGUF_MODEL

    # Adjust memory budget based on backend
    vram = hw.get("vram_gb", 0.0)
    ram = hw.get("ram_gb", 8.0)

    if backend == "cuda" and vram > 0:
        # For CUDA, we can use VRAM for model layers
        budget = vram
    elif backend in ["metal", "vulkan", "sycl", "hip"]:
        # For other GPU backends, use combination of VRAM and RAM
        budget = min(vram + ram * 0.5, ram) if vram > 0 else ram * 0.5
    else:
        # CPU-only: use RAM with conservative estimate
        budget = ram * 0.3  # Conservative: use 30% of RAM for model

    # Ensure minimum budget
    budget = max(budget, 2.0)

    for max_memory, preferred in _GGUF_MODEL_TIERS:
        if budget >= max_memory:
            for model_name in preferred:
                if model_name in available_models:
                    return model_name
            break

    # Nothing matched the tier — return the smallest available model
    return available_models[0] if available_models else _FALLBACK_GGUF_MODEL


def get_llamacpp_config(hw: dict, backend: str) -> dict:
    """
    Get recommended llama.cpp configuration based on hardware and backend.

    Args:
        hw: Hardware info dict from detect()
        backend: llama.cpp backend

    Returns:
        Configuration dict with n_threads, n_gpu_layers, etc.
    """
    config = {
        "n_ctx": 4096,
        "n_threads": hw.get("cpu_cores", 4),
        "n_gpu_layers": -1,  # Auto-detect
        "backend": backend,
    }

    if backend == "cuda":
        # CUDA-specific optimizations
        vram_gb = hw.get("vram_gb", 0.0)
        if vram_gb >= 8:
            config["n_gpu_layers"] = -1  # All layers on GPU
        elif vram_gb >= 4:
            config["n_gpu_layers"] = 20  # Partial offloading
        else:
            config["n_gpu_layers"] = 10  # Minimal offloading

    elif backend == "cpu":
        # CPU optimizations
        cpu_cores = hw.get("cpu_cores", 4)
        config["n_threads"] = max(1, cpu_cores // 2)  # Use half cores for better responsiveness

    return config


# ── Private helpers ───────────────────────────────────────────────────────

def _cpu_cores() -> int:
    import os
    return os.cpu_count() or 4


def _ram_gb() -> float:
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024**3), 1)
    except ImportError:
        pass
    # Windows fallback
    if platform.system() == "Windows":
        try:
            out = subprocess.check_output(
                ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
                text=True, timeout=5,
            )
            for line in out.strip().splitlines():
                line = line.strip()
                if line.isdigit():
                    return round(int(line) / (1024**3), 1)
        except Exception:
            pass
    return 8.0  # safe default


def _nvidia_smi() -> tuple[str, float]:
    """Query nvidia-smi for GPU name and total VRAM in GB."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            text=True, timeout=5,
        )
        line = out.strip().splitlines()[0]
        name, mem_mb = line.split(",", 1)
        return name.strip(), round(float(mem_mb.strip()) / 1024, 1)
    except Exception:
        return "", 0.0


# ── llama.cpp Backend Detection ───────────────────────────────────────────

def _detect_llamacpp_backends() -> list[str]:
    """Detect available llama.cpp backends for the current hardware."""
    backends = []

    # Check CUDA (NVIDIA GPUs)
    if _check_cuda_available():
        backends.append("cuda")

    # Check Metal (Apple Silicon)
    if _check_metal_available():
        backends.append("metal")

    # Check Vulkan (cross-platform GPU compute)
    if _check_vulkan_available():
        backends.append("vulkan")

    # Check SYCL (Intel GPUs)
    if _check_sycl_available():
        backends.append("sycl")

    # Check HIP (AMD GPUs)
    if _check_hip_available():
        backends.append("hip")

    # CPU is always available as fallback
    backends.append("cpu")

    return backends


def _get_recommended_llamacpp_backend(hw_info: dict) -> str:
    """Get the recommended llama.cpp backend based on hardware."""
    backends = hw_info.get("llamacpp_backends", [])

    # Priority order: cuda > metal > vulkan > sycl > hip > cpu
    priority_backends = ["cuda", "metal", "vulkan", "sycl", "hip", "cpu"]

    for backend in priority_backends:
        if backend in backends:
            return backend

    return "cpu"


def _check_cuda_available() -> bool:
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


def _check_metal_available() -> bool:
    """Check if Metal is available (macOS with Apple Silicon)."""
    try:
        # Check if we're on Apple Silicon
        machine = platform.machine().lower()
        return machine in ["arm64", "aarch64"] and platform.system() == "Darwin"
    except:
        return False


def _check_vulkan_available() -> bool:
    """Check if Vulkan is available."""
    try:
        if platform.system() == "Windows":
            # Check for vulkan-1.dll
            import ctypes
            return ctypes.windll.kernel32.LoadLibraryW("vulkan-1.dll") is not None
        elif platform.system() == "Linux":
            # Check for libvulkan.so
            import ctypes
            try:
                return ctypes.cdll.LoadLibrary("libvulkan.so.1") is not None
            except:
                return False
        return False
    except:
        return False


def _check_sycl_available() -> bool:
    """Check if SYCL is available (Intel GPUs)."""
    try:
        # Check for Intel integrated graphics
        if platform.system() == "Windows":
            result = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"],
                                  capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            return "intel" in output and ("uhd" in output or "iris" in output or "hd graphics" in output)
        elif platform.system() == "Linux":
            result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            return "intel" in output and "graphics" in output
        return False
    except:
        return False


def _check_hip_available() -> bool:
    """Check if HIP is available (AMD GPUs)."""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["wmic", "path", "win32_videocontroller", "get", "name"],
                                  capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            return "amd" in output or "radeon" in output
        elif platform.system() == "Linux":
            result = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5)
            output = result.stdout.lower()
            return "amd" in output and ("radeon" in output or "navi" in output)
        return False
    except:
        return False
