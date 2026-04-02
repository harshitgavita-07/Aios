#!/usr/bin/env python3
"""
Simple test for llama.cpp integration components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test basic imports."""
    print("Testing imports...")

    try:
        import hardware
        print("✅ hardware import successful")
    except Exception as e:
        print(f"❌ hardware import failed: {e}")
        return False

    try:
        import llm_config
        print("✅ llm_config import successful")
    except Exception as e:
        print(f"❌ llm_config import failed: {e}")
        return False

    return True

def test_hardware():
    """Test hardware detection."""
    print("\nTesting hardware detection...")

    try:
        import hardware
        hw = hardware.detect()
        print(f"✅ Hardware detection successful")
        print(f"   CPU cores: {hw.get('cpu_cores')}")
        print(f"   RAM: {hw.get('ram_gb')} GB")
        print(f"   GPU: {hw.get('gpu_name', 'None')}")
        print(f"   llama.cpp backends: {hw.get('llamacpp_backends', [])}")
        return True
    except Exception as e:
        print(f"❌ Hardware detection failed: {e}")
        return False

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")

    try:
        import llm_config
        config = llm_config.get_llm_config()
        print(f"✅ Configuration loaded")
        print(f"   Default backend: {config.get('default_backend')}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run tests."""
    print("AIOS llama.cpp Integration - Basic Tests")
    print("=" * 50)

    tests = [test_imports, test_hardware, test_config]
    passed = 0

    for test in tests:
        if test():
            passed += 1

    print(f"\nResults: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 Basic integration test passed!")
        print("\nNext steps:")
        print("1. Install llama-cpp-python: pip install llama-cpp-python")
        print("2. Download a GGUF model from Hugging Face")
        print("3. Run full integration tests")
    else:
        print("❌ Some tests failed")

    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)</content>
<parameter name="filePath">c:\Users\HARSHIT\Aios\test_basic_integration.py