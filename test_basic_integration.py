#!/usr/bin/env python3
"""Basic smoke tests for llama.cpp integration components."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    """Test basic imports."""
    print("Testing imports...")

    try:
        import hardware  # noqa: F401

        print("[OK] hardware import successful")
    except Exception as e:
        print(f"[FAIL] hardware import failed: {e}")
        return False

    try:
        import llm_config  # noqa: F401

        print("[OK] llm_config import successful")
    except Exception as e:
        print(f"[FAIL] llm_config import failed: {e}")
        return False

    return True


def test_hardware():
    """Test hardware detection."""
    print("\nTesting hardware detection...")

    try:
        import hardware

        hw = hardware.detect()
        print("[OK] Hardware detection successful")
        print(f"   CPU cores: {hw.get('cpu_cores')}")
        print(f"   RAM: {hw.get('ram_gb')} GB")
        print(f"   GPU: {hw.get('gpu_name', 'None')}")
        print(f"   llama.cpp backends: {hw.get('llamacpp_backends', [])}")
        return True
    except Exception as e:
        print(f"[FAIL] Hardware detection failed: {e}")
        return False


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")

    try:
        import llm_config

        config = llm_config.get_llm_config()
        print("[OK] Configuration loaded")
        print(f"   Default backend: {config.get('default_backend')}")
        return True
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False


def main():
    """Run tests."""
    print("AIOS llama.cpp Integration - Basic Tests")
    print("=" * 50)

    checks = [test_imports, test_hardware, test_config]
    passed = 0

    for check in checks:
        if check():
            passed += 1

    print(f"\nResults: {passed}/{len(checks)} tests passed")

    if passed == len(checks):
        print("[OK] Basic integration test passed.")
        print("\nNext steps:")
        print("1. Install llama-cpp-python: pip install llama-cpp-python")
        print("2. Download a GGUF model from Hugging Face")
        print("3. Run full integration tests")
    else:
        print("[FAIL] Some tests failed")

    return passed == len(checks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
