"""
Aios hardware detection & model recommendation.

Detects GPU VRAM, CPU cores, total RAM and recommends the best
Ollama model from the locally available models.

Optional: uses pyaccelerate (v0.9+) for richer hardware profiling.
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

_FALLBACK_MODEL = "llama3.2:1b"


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
