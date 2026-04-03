#!/usr/bin/env python3
"""
AIOS llama.cpp Integration Test

This script demonstrates and tests the llama.cpp integration features.
Run this to validate that llama.cpp backend works correctly.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
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
        print("✅ Hardware detection working")
        return True
    except Exception as e:
        print(f"❌ Hardware detection failed: {e}")
        return False

def test_llamacpp_backend():
    """Test llama.cpp backend initialization."""
    print("\n=== Testing llama.cpp Backend ===")

    try:
        from llm_llamacpp import LlamaCppClient

        # Create client (will fail gracefully if llama-cpp-python not installed)
        client = LlamaCppClient(model_dir="./models")

        print("✅ llama.cpp client initialized")
        print(f"Available models: {len(client.list_models())}")

        # Test model info
        info = client.get_model_info()
        print(f"Model info: {info}")

        return True
    except ImportError as e:
        print(f"⚠️  llama-cpp-python not installed: {e}")
        print("   Install with: pip install llama-cpp-python")
        return False
    except Exception as e:
        print(f"❌ llama.cpp backend test failed: {e}")
        return False

def test_unified_client():
    """Test unified LLM client."""
    print("\n=== Testing Unified LLM Client ===")

    try:
        from llm_unified import UnifiedLLMClient

        # Test with auto backend selection
        client = UnifiedLLMClient(preferred_backend="auto")

        print(f"Current backend: {client.get_current_backend()}")
        print(f"Current model: {client.get_current_model()}")

        # Test model listing
        models = client.list_available_models()
        print(f"Available Ollama models: {len(models.get('ollama', []))}")
        print(f"Available llama.cpp models: {len(models.get('llamacpp', []))}")

        # Test simple generation (if backend available)
        try:
            response = client.generate("Hello, what is 2+2?", max_tokens=50)
            print(f"Test response: {response[:100]}...")
            print("✅ Unified client generation working")
        except Exception as e:
            print(f"⚠️  Generation test failed (expected if no models): {e}")

        return True
    except Exception as e:
        print(f"❌ Unified client test failed: {e}")
        return False

def test_model_recommendation():
    """Test model recommendation for both backends."""
    print("\n=== Testing Model Recommendation ===")

    try:
        from hardware import detect, recommend_model, recommend_gguf_model

        hw = detect()

        # Test Ollama model recommendation
        ollama_models = ["llama3.2:1b", "llama3.2:3b", "llama3.1:8b"]
        recommended_ollama = recommend_model(hw, ollama_models)
        print(f"Recommended Ollama model: {recommended_ollama}")

        # Test GGUF model recommendation
        gguf_models = ["gemma-3-1b-it", "llama-3.2-3b-instruct", "llama-3.1-8b-instruct"]
        backend = hw.get("recommended_llamacpp_backend", "cpu")
        recommended_gguf = recommend_gguf_model(hw, gguf_models, backend)
        print(f"Recommended GGUF model for {backend}: {recommended_gguf}")

        print("✅ Model recommendation working")
        return True
    except Exception as e:
        print(f"❌ Model recommendation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("AIOS llama.cpp Integration Test Suite")
    print("=" * 50)

    tests = [
        test_hardware_detection,
        test_model_recommendation,
        test_llamacpp_backend,
        test_unified_client,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! llama.cpp integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\nTo install llama-cpp-python:")
        print("  pip install llama-cpp-python")
        print("  # For CUDA support: pip install llama-cpp-python[cuBLAS]")
        print("  # For Metal support (macOS): pip install llama-cpp-python[metal]")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
