# AIOS llama.cpp Integration

This document describes the integration of [llama.cpp](https://github.com/ggml-org/llama.cpp) features into AIOS, providing enhanced LLM inference capabilities.

## Overview

AIOS now supports multiple LLM backends:

1. **Ollama** (default) - Server-based inference with REST API
2. **llama.cpp** - Direct C++ inference for better performance and control

## Key Benefits of llama.cpp Integration

### 🚀 Performance Improvements
- **Direct C++ inference** without server overhead
- **Hardware-optimized backends**: CUDA, Metal, Vulkan, SYCL, HIP
- **Advanced quantization** (1.5-bit to 8-bit) for faster inference
- **Speculative decoding** for reduced latency

### 🎛️ Enhanced Control
- **Fine-grained inference parameters** (temperature, top-p, top-k, etc.)
- **Custom quantization levels** for memory/performance trade-offs
- **GGUF model format support** with standardized model files
- **Streaming control** with adjustable chunk sizes

### 💾 Memory Efficiency
- **Multiple quantization options** for different memory constraints
- **GPU memory optimization** with layer offloading
- **CPU memory management** for systems with limited RAM

### 🔧 Hardware Optimization
- **Automatic backend detection** (CUDA for NVIDIA, Metal for Apple, etc.)
- **Hardware-aware model selection** based on available resources
- **Multi-platform support** (Windows, macOS, Linux)

## Installation

### 1. Install llama-cpp-python

```bash
# Basic installation
pip install llama-cpp-python

# For CUDA support (NVIDIA GPUs)
pip install llama-cpp-python[cuBLAS]

# For Metal support (Apple Silicon)
pip install llama-cpp-python[metal]

# For Vulkan support (cross-platform)
pip install llama-cpp-python[vulkan]
```

### 2. Download GGUF Models

Download models from [Hugging Face](https://huggingface.co/models?library=gguf) or use the built-in downloader:

```python
from llm_unified import UnifiedLLMClient

client = UnifiedLLMClient()
client.download_llamacpp_model("ggml-org/gemma-3-1b-it-GGUF")
```

## Usage

### Basic Usage

```python
from llm_unified import UnifiedLLMClient

# Auto-select best backend
client = UnifiedLLMClient()

# Generate text
response = client.generate("Hello, how are you?")
print(response)

# Streaming generation
for token in client.generate_stream("Tell me a story"):
    print(token, end="", flush=True)
```

### Backend Selection

```python
# Force specific backend
ollama_client = UnifiedLLMClient(preferred_backend="ollama")
llamacpp_client = UnifiedLLMClient(preferred_backend="llamacpp")

# Switch backends at runtime
client.switch_backend("llamacpp")
```

### Model Management

```python
# List available models
models = client.list_available_models()
print("Ollama models:", models["ollama"])
print("llama.cpp models:", models["llamacpp"])

# Download and load a model
client.download_llamacpp_model("ggml-org/llama-3.2-3b-instruct-GGUF")
```

### Hardware-Aware Configuration

```python
from hardware import detect, get_llamacpp_config

hw_info = detect()
config = get_llamacpp_config(hw_info)

print(f"Recommended backend: {config['backend']}")
print(f"GPU layers: {config['n_gpu_layers']}")
print(f"Threads: {config['n_threads']}")
```

## Configuration

### LLM Configuration (`llm_config.py`)

```python
LLM_CONFIG = {
    "default_backend": "auto",  # 'auto', 'ollama', or 'llamacpp'
    "llamacpp": {
        "model_dir": "./models",
        "n_ctx": 4096,
        "n_gpu_layers": -1,
        "backend": None,  # Auto-detect
    },
}
```

### Model Recommendations

The system automatically recommends models based on your hardware:

- **CPU-only systems**: Smaller models like Gemma 1B/4B
- **GPU systems**: Larger models with GPU acceleration
- **High-end GPUs**: Full precision models with all layers on GPU

## Advanced Features

### Quantization Options

```python
# Available quantization levels
quantizations = {
    "Q2_K": "2-bit (smallest, lowest quality)",
    "Q4_0": "4-bit (recommended balance)",
    "Q8_0": "8-bit (high quality, larger size)",
}
```

### Custom Inference Parameters

```python
response = client.generate(
    prompt="Explain quantum computing",
    temperature=0.7,      # Creativity
    top_p=0.9,           # Diversity
    top_k=50,            # Token selection
    max_tokens=1000,     # Response length
    repeat_penalty=1.1,  # Reduce repetition
)
```

### Embeddings Support

```python
# Generate embeddings (llama.cpp backend only)
embeddings = client.embed("Hello world")
print(f"Embedding dimension: {len(embeddings)}")
```

## Performance Comparison

| Backend | Latency | Memory Usage | Control | Setup Complexity |
|---------|---------|--------------|---------|------------------|
| Ollama | Medium | Medium | Limited | Low |
| llama.cpp | Low | Optimized | Full | Medium |

## Troubleshooting

### Common Issues

1. **"llama-cpp-python not installed"**
   ```bash
   pip install llama-cpp-python
   ```

2. **CUDA not detected**
   ```bash
   pip install llama-cpp-python[cuBLAS]
   # Ensure CUDA toolkit is installed
   ```

3. **No GGUF models found**
   ```python
   client.download_llamacpp_model("ggml-org/gemma-3-1b-it-GGUF")
   ```

4. **Out of memory**
   - Use smaller quantization (Q2_K, Q3_K)
   - Reduce n_ctx (context window)
   - Use CPU backend for large models

### Performance Tuning

```python
# For low-memory systems
config = {
    "n_ctx": 2048,        # Smaller context
    "quantization": "Q2_K",  # Aggressive quantization
    "n_threads": 2,       # Fewer threads
}

# For high-performance GPUs
config = {
    "n_gpu_layers": -1,   # All layers on GPU
    "quantization": "Q8_0",  # High quality
    "backend": "cuda",
}
```

## Testing

Run the integration test:

```bash
python test_llamacpp_integration.py
```

This will validate:
- Hardware detection
- Backend availability
- Model recommendation
- Basic inference

## API Reference

### UnifiedLLMClient

- `generate(prompt, **kwargs)` - Generate complete response
- `generate_stream(prompt, **kwargs)` - Generate streaming response
- `switch_backend(backend)` - Switch between backends
- `download_llamacpp_model(model_name)` - Download GGUF model
- `list_available_models()` - List models for all backends
- `get_model_info()` - Get current model information

### LlamaCppBackend

- `load_model(model_path)` - Load GGUF model
- `generate(...)` - Direct generation
- `generate_stream(...)` - Direct streaming
- `embed(text)` - Generate embeddings
- `get_model_info()` - Model metadata

## Contributing

When adding new features:

1. Update `llm_config.py` for new configuration options
2. Add tests to `test_llamacpp_integration.py`
3. Update this documentation
4. Test on multiple hardware configurations

## Future Enhancements

- **Speculative decoding** for faster inference
- **Multimodal support** (vision models)
- **Function calling** with structured outputs
- **Model quantization** tools
- **Performance benchmarking** suite

---

For more information, see the [llama.cpp documentation](https://github.com/ggml-org/llama.cpp) and [AIOS repository](https://github.com/your-repo/aios).</content>
<parameter name="filePath">c:\Users\HARSHIT\Aios\LLAMACPP_INTEGRATION.md