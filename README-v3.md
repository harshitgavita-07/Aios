# AIOS v3.0 — AI-Native Operating Environment

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **The next evolution of AIOS: from AI assistant to AI-native operating system.**

AIOS v3.0 transforms AIOS from a traditional AI assistant application into an **AI-native desktop/runtime layer** where agents, workflows, and on-device intelligence are the core UI paradigm.

## 🚀 What's New in v3.0

### AI-Native Architecture
- **Agents as Applications**: Agents replace traditional desktop applications
- **Workflows as UI**: Complex tasks are orchestrated through natural language workflows
- **Intent-Driven Computing**: User intents automatically spawn and coordinate agents
- **Context-Aware Environment**: The system adapts to user context and environment

### Core Components
- **AIOS Runtime Layer**: The core operating environment for AI-native computing
- **Agent Mesh**: Inter-agent communication and collaboration system
- **Workflow Engine**: Complex task orchestration with dependency management
- **Intent Engine**: Natural language processing for user intent recognition
- **Context Engine**: Environment awareness and state management
- **Resource Manager**: Hardware and software resource allocation

### Enhanced LLM Integration
- **Unified LLM Client**: Seamless switching between Ollama, llama.cpp, and other backends
- **Hardware Optimization**: Automatic detection and optimization for CUDA, Metal, Vulkan, etc.
- **GGUF Model Support**: Direct support for optimized GGUF model formats
- **Streaming Inference**: Real-time response generation with streaming support

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AIOS Workspace                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Agent Widgets │ Workflow Panels │ Intent Interface     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
           ┌──────────▼──────────┐
           │   AIOS Runtime     │
           │                    │
           │  ┌──────────────┐  │
           │  │ Agent Mesh   │  │
           │  └──────────────┘  │
           │                    │
           │  ┌──────────────┐  │
           │  │ Workflow     │  │
           │  │ Engine       │  │
           │  └──────────────┘  │
           │                    │
           │  ┌──────────────┐  │
           │  │ Intent       │  │
           │  │ Engine       │  │
           │  └──────────────┘  │
           │                    │
           │  ┌──────────────┐  │
           │  │ Context      │  │
           │  │ Engine       │  │
           │  └──────────────┘  │
           │                    │
           │  ┌──────────────┐  │
           │  │ Resource     │  │
           │  │ Manager      │  │
           │  └──────────────┘  │
           └────────────────────┘
                      │
           ┌──────────▼──────────┐
           │   LLM Backends      │
           │                     │
           │  • Ollama           │
           │  • llama.cpp        │
           │  • Transformers     │
           │  • Custom APIs      │
           └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PySide6 (Qt6)
- llama-cpp-python (for local inference)
- Ollama (optional, for additional models)

### Installation

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-org/aios.git
   cd aios
   pip install -r requirements-v3.txt
   ```

2. **Install Ollama (optional):**
   ```bash
   # On macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Pull a model
   ollama pull llama2:7b
   ```

3. **Run AIOS v3.0:**
   ```bash
   python app_v3.py
   ```

   This launches the AI-native workspace. For legacy mode:
   ```bash
   python app_v3.py --mode legacy
   ```

## 🎯 Key Features

### Agent-Centric Computing
- **Agent Mesh**: Agents communicate and collaborate autonomously
- **Dynamic Agent Creation**: New agents spawn based on user needs
- **Agent Persistence**: Agents maintain state across sessions
- **Agent Marketplace**: Share and discover agent capabilities

### Workflow Orchestration
- **Natural Language Workflows**: Describe complex tasks in plain English
- **Dependency Management**: Automatic task sequencing and parallelization
- **Error Handling**: Intelligent retry and escalation strategies
- **Workflow Templates**: Reusable workflow patterns

### Intent-Driven Interface
- **Natural Language Commands**: "Create a presentation about AI trends"
- **Context Awareness**: System adapts to user environment and history
- **Proactive Assistance**: System anticipates user needs
- **Multi-Modal Input**: Voice, text, gesture, and sensor inputs

### Hardware Optimization
- **Multi-Backend LLM**: Automatic backend selection (CPU/GPU/Cloud)
- **GGUF Model Support**: Optimized model formats for faster inference
- **Hardware Detection**: Automatic detection of CUDA, Metal, Vulkan, etc.
- **Resource Management**: Intelligent resource allocation and scaling

## 🔧 Development

### Project Structure
```
aios/
├── app_v3.py              # Main AIOS v3.0 application
├── runtime/               # AIOS runtime layer
│   └── aios_runtime.py    # Core runtime implementation
├── ui/                    # User interface components
│   └── workspace.py       # AI-native workspace manager
├── core/                  # Core AIOS components
├── rag/                   # Retrieval-augmented generation
├── tools/                 # Tool and skill system
├── llm_*.py              # LLM backend implementations
├── hardware.py           # Hardware detection and optimization
└── requirements-v3.txt   # Dependencies
```

### Running Tests
```bash
pytest tests/
```

### Building for Distribution
```bash
# Create executable
pyinstaller app_v3.spec

# Or use the provided spec
pyinstaller SysAIOS.spec
```

## 📚 Documentation

- [Architecture Guide](docs/architecture.md)
- [Agent Development](docs/agent-development.md)
- [Workflow Creation](docs/workflow-creation.md)
- [API Reference](docs/api-reference.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linting
flake8 .

# Run type checking
mypy .

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggml-org/llama.cpp) for the amazing C++ inference engine
- [Ollama](https://ollama.ai) for the excellent model serving platform
- [PySide6](https://wiki.qt.io/Qt_for_Python) for the Qt Python bindings
- The open-source AI community for inspiration and tools

---

**AIOS v3.0** — Where AI becomes the operating system, and agents are your applications.