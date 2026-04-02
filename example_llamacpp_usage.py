#!/usr/bin/env python3
"""
AIOS llama.cpp Example Usage

This script demonstrates how to use the new llama.cpp integration
in AIOS for enhanced LLM inference.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def example_basic_usage():
    """Basic usage example."""
    print("=== Basic Usage Example ===")

    try:
        from llm_unified import UnifiedLLMClient

        # Create client with auto backend selection
        client = UnifiedLLMClient()

        print(f"Using backend: {client.get_current_backend()}")
        print(f"Current model: {client.get_current_model()}")

        # Simple generation
        prompt = "Explain what AI is in one sentence."
        response = client.generate(prompt, max_tokens=100)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")

    except Exception as e:
        print(f"Error: {e}")

def example_streaming():
    """Streaming generation example."""
    print("\n=== Streaming Example ===")

    try:
        from llm_unified import UnifiedLLMClient

        client = UnifiedLLMClient()

        prompt = "Write a short poem about technology."
        print(f"Prompt: {prompt}")
        print("Response: ", end="", flush=True)

        for token in client.generate_stream(prompt, max_tokens=150):
            print(token, end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"Error: {e}")

def example_backend_switching():
    """Backend switching example."""
    print("\n=== Backend Switching Example ===")

    try:
        from llm_unified import UnifiedLLMClient

        client = UnifiedLLMClient()

        # Show available models
        models = client.list_available_models()
        print("Available models:")
        print(f"  Ollama: {models['ollama']}")
        print(f"  llama.cpp: {models['llamacpp']}")

        # Try switching to llama.cpp if available
        if client.switch_backend("llamacpp"):
            print("Successfully switched to llama.cpp backend")
            print(f"Current model: {client.get_current_model()}")

            # Test generation
            response = client.generate("What is the capital of France?", max_tokens=50)
            print(f"Response: {response}")
        else:
            print("llama.cpp backend not available")

    except Exception as e:
        print(f"Error: {e}")

def example_model_download():
    """Model download example."""
    print("\n=== Model Download Example ===")

    try:
        from llm_unified import UnifiedLLMClient

        client = UnifiedLLMClient()

        print("Downloading a small model for demonstration...")
        print("Note: This may take a few minutes depending on your internet connection")

        # Download a small model
        success = client.download_llamacpp_model("ggml-org/gemma-3-1b-it-GGUF")

        if success:
            print("Model downloaded and loaded successfully!")

            # Test the model
            response = client.generate("Say hello in French.", max_tokens=50)
            print(f"Test response: {response}")
        else:
            print("Model download failed")

    except Exception as e:
        print(f"Error: {e}")

def example_hardware_info():
    """Hardware information example."""
    print("\n=== Hardware Information ===")

    try:
        from hardware import detect, get_llamacpp_config

        hw = detect()

        print("Hardware Detection Results:")
        print(f"  CPU Cores: {hw.get('cpu_cores')}")
        print(f"  RAM: {hw.get('ram_gb')} GB")
        print(f"  GPU: {hw.get('gpu_name', 'None')}")
        print(f"  VRAM: {hw.get('vram_gb', 0)} GB")
        print(f"  Primary Backend: {hw.get('backend')}")
        print(f"  llama.cpp Backends: {hw.get('llamacpp_backends')}")
        print(f"  Recommended llama.cpp Backend: {hw.get('recommended_llamacpp_backend')}")

        # Show recommended config
        backend = hw.get('recommended_llamacpp_backend')
        config = get_llamacpp_config(hw, backend)
        print(f"\nRecommended llama.cpp config for {backend}:")
        for key, value in config.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all examples."""
    print("AIOS llama.cpp Integration Examples")
    print("=" * 50)

    examples = [
        example_hardware_info,
        example_basic_usage,
        example_streaming,
        example_backend_switching,
        # example_model_download,  # Commented out as it downloads models
    ]

    for example in examples:
        try:
            example()
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            break
        except Exception as e:
            print(f"Example failed: {e}")

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo try model downloading, uncomment example_model_download() in the code.")
    print("For more information, see LLAMACPP_INTEGRATION.md")

if __name__ == "__main__":
    main()</content>
<parameter name="filePath">c:\Users\HARSHIT\Aios\example_llamacpp_usage.py