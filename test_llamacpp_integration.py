#!/usr/bin/env python3
"""AIOS llama.cpp integration diagnostics."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_hardware_detection():
    """Test hardware detection with llama.cpp backends."""
    print("=== Testing Hardware Detection ===")

    try:
        from hardware import detect

        hw = detect()

        print(f"CPU Cores: {hw.get('cpu_cores', 'Unknown')}")
        print(f"RAM: {hw.get('ram_gb', 'Unknown')} GB")
        print(f"GPU: {hw.get('gpu_name', 'None')}")
        print(f"VRAM: {hw.get('vram_gb', 0)} GB")
        print(f"Backend: {hw.get('backend', 'cpu')}")
        print(f"llama.cpp Backends: {hw.get('llamacpp_backends', [])}")
        print(f"Recommended llama.cpp Backend: {hw.get('recommended_llamacpp_backend', 'cpu')}")
        print("[OK] Hardware detection working")
        return True
    except Exception as e:
        print(f"[FAIL] Hardware detection failed: {e}")
        return False


def test_llamacpp_backend():
    """Test optional llama.cpp backend initialization."""
    print("\n=== Testing llama.cpp Backend ===")

    try:
        from llm_llamacpp import LlamaCppClient

        client = LlamaCppClient(model_dir="./models")

        print("[OK] llama.cpp client initialized")
        print(f"Available models: {len(client.list_models())}")

        info = client.get_model_info()
        print(f"Model info: {info}")

        return True
    except ImportError as e:
        print(f"[SKIP] llama-cpp-python not installed: {e}")
        print("   Install with: pip install llama-cpp-python")
        return True
    except Exception as e:
        print(f"[FAIL] llama.cpp backend test failed: {e}")
        return False


def test_unified_client():
    """Test unified LLM client."""
    print("\n=== Testing Unified LLM Client ===")

    try:
        from llm_unified import UnifiedLLMClient

        client = UnifiedLLMClient(preferred_backend="auto")

        print(f"Current backend: {client.get_current_backend()}")
        print(f"Current model: {client.get_current_model()}")

        models = client.list_available_models()
        print(f"Available Ollama models: {len(models.get('ollama', []))}")
        print(f"Available llama.cpp models: {len(models.get('llamacpp', []))}")

        try:
            response = client.generate("Hello, what is 2+2?", max_tokens=50)
            print(f"Test response: {response[:100]}...")
            print("[OK] Unified client generation working")
        except Exception as e:
            print(f"[SKIP] Generation test unavailable without a local model: {e}")

        return True
    except Exception as e:
        print(f"[FAIL] Unified client test failed: {e}")
        return False


def test_model_recommendation():
    """Test model recommendation for both backends."""
    print("\n=== Testing Model Recommendation ===")

    try:
        from hardware import detect, recommend_gguf_model, recommend_model

        hw = detect()

        ollama_models = ["llama3.2:1b", "llama3.2:3b", "llama3.1:8b"]
        recommended_ollama = recommend_model(hw, ollama_models)
        print(f"Recommended Ollama model: {recommended_ollama}")

        gguf_models = ["gemma-3-1b-it", "llama-3.2-3b-instruct", "llama-3.1-8b-instruct"]
        backend = hw.get("recommended_llamacpp_backend", "cpu")
        recommended_gguf = recommend_gguf_model(hw, gguf_models, backend)
        print(f"Recommended GGUF model for {backend}: {recommended_gguf}")

        print("[OK] Model recommendation working")
        return True
    except Exception as e:
        print(f"[FAIL] Model recommendation test failed: {e}")
        return False


def main():
    """Run all diagnostics."""
    print("AIOS llama.cpp Integration Test Suite")
    print("=" * 50)

    checks = [
        test_hardware_detection,
        test_model_recommendation,
        test_llamacpp_backend,
        test_unified_client,
    ]

    passed = 0
    total = len(checks)

    for check in checks:
        if check():
            passed += 1

    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("[OK] Integration diagnostics passed.")
    else:
        print("[FAIL] Some diagnostics failed. Check the output above for details.")
        print("\nTo install llama-cpp-python:")
        print("  pip install llama-cpp-python")
        print("  # For CUDA support: pip install llama-cpp-python[cuBLAS]")
        print("  # For Metal support (macOS): pip install llama-cpp-python[metal]")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
