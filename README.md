# AIOS v3.0 — AI-Native Operating Environment

**The next evolution of AIOS: from AI assistant to AI-native operating system.**

```
┌─────────────────────────────────────────────────────────────┐
│  Your machine. Your agents. Your workflows. Your AI.         │
│  No cloud. No API keys. No compromises.                      │
└─────────────────────────────────────────────────────────────┘
```

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

> **AIOS v3.0 transforms your desktop into an AI-native operating environment where agents are applications, workflows are UI, and on-device intelligence is the core paradigm.**

---

## What It Does

AIOS v3.0 reimagines computing where AI becomes the operating system:

| Paradigm Shift | What You Can Do |
|----------------|-----------------|
| **Agents as Applications** | Agents replace traditional desktop apps — spawn, coordinate, and manage them |
| **Workflows as UI** | Complex tasks orchestrated through natural language workflows |
| **Intent-Driven Computing** | User intents automatically spawn agents and coordinate workflows |
| **Context-Aware Environment** | The system adapts to your environment, history, and preferences |
| **Multi-Agent Collaboration** | Agents communicate and collaborate autonomously via the agent mesh |
| **Hardware Optimization** | Automatic backend selection (CPU/GPU/Cloud) with GGUF model support |
| **Real-Time Orchestration** | Live workflow monitoring with step-by-step progress tracking |
| **Natural Language Commands** | "Create a presentation about AI trends" spawns a workflow automatically |
| **Persistent Agent State** | Agents maintain context across sessions and system restarts |
| **On-Device Intelligence** | Everything runs locally — your data never leaves your machine |

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements-v3.txt

# Launch AI-native workspace (default)
python app_v3.py

# Or launch legacy chat interface
python app_v3.py --mode legacy
```

The AI-native workspace appears, where agents are your applications and workflows are your interface.

---

## Architecture

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

---

## Core Components

### AIOS Runtime Layer
The foundational operating environment for AI-native computing:

- **Agent Mesh**: Inter-agent communication and collaboration system
- **Workflow Engine**: Complex task orchestration with dependency management
- **Intent Engine**: Natural language processing for user intent recognition
- **Context Engine**: Environment awareness and state management
- **Resource Manager**: Hardware and software resource allocation

### AI-Native Workspace
The desktop environment where agents are the primary interface:

- **Agent Widgets**: Visual representations of running agents
- **Workflow Panels**: Real-time workflow monitoring and control
- **Intent Interface**: Natural language command input
- **Context Display**: Environment and system state visualization
- **System Tray Integration**: Background operation management

### Enhanced LLM Integration
- **Unified Client**: Seamless switching between Ollama, llama.cpp, and other backends
- **Hardware Optimization**: Automatic detection and optimization for CUDA, Metal, Vulkan
- **GGUF Model Support**: Direct support for optimized model formats
- **Streaming Inference**: Real-time response generation with streaming support

---

## Project Structure

```
Aios/
├── app_v3.py              # Main AIOS v3.0 application (workspace + legacy modes)
├── app.py                 # Legacy chat interface (backward compatibility)
├── README-v3.md           # AIOS v3.0 documentation
├── requirements-v3.txt    # Dependencies for AI-native architecture
│
├── runtime/               # AIOS runtime layer
│   └── aios_runtime.py    # Core runtime with agent mesh, workflow engine, etc.
│
├── ui/                    # User interface components
│   ├── workspace.py       # AI-native workspace manager
│   ├── chat_ui.py         # Legacy chat interface
│   └── bubble.py          # Floating desktop bubble
│
├── core/                  # Core AIOS components
│   ├── agent.py           # Orchestrator — memory + soulsync + planner + LLM
│   ├── memory.py          # SQLite conversation store + user profile
│   ├── soulsync.py        # Emotion detection + tone adaptation
│   ├── planner.py         # Intent detection (chat / tool / system)
│   └── mode_controller.py # Legacy mode management
│
├── rag/                   # Retrieval-augmented generation
│   ├── embedder.py        # Text embedding generation
│   ├── pipeline.py        # RAG processing pipeline
│   ├── processor.py       # Document processing
│   ├── retriever.py       # Context retrieval
│   └── vector_store.py    # Vector storage and search
│
├── tools/                 # Tool and skill system
│   ├── registry.py        # Whitelist-only tool registry
│   ├── executor.py        # Tool execution engine
│   ├── system_tools.py    # Built-in system tools
│   └── think_tool.py      # Structured reasoning scratchpad
│
├── llm_*.py              # LLM backend implementations
│   ├── llm.py            # Ollama SDK wrapper
│   ├── llm_llamacpp.py   # Direct llama.cpp backend
│   └── llm_unified.py    # Unified client for multiple backends
│
└── hardware.py           # Hardware detection and optimization
```

---

## What AIOS v3.0 Understands

| Input Type | What Happens |
|------------|-------------|
| **Natural Language Tasks** | "Create a presentation about AI trends" → spawns workflow with research, writing, and formatting agents |
| **Complex Workflows** | "Analyze my codebase and suggest improvements" → coordinates code analysis, testing, and documentation agents |
| **Multi-Step Processes** | "Plan my week and set up reminders" → creates planning agent, calendar integration, and notification system |
| **Agent Management** | "Show me running agents" → displays agent mesh status and resource usage |
| **Workflow Monitoring** | "What's the status of my research project?" → shows workflow progress with step-by-step details |
| **Context Queries** | "What was I working on yesterday?" → retrieves from persistent context engine |
| **Resource Requests** | "I need more GPU memory for this task" → resource manager reallocates hardware |
| **System Commands** | "Clear all workflows" or "Restart agent mesh" → direct runtime control |

---

## Agent Mesh

Agents communicate and collaborate autonomously:

- **Inter-Agent Communication**: Async message passing between agents
- **Dynamic Agent Creation**: New agents spawn based on user needs
- **Agent Persistence**: Agents maintain state across sessions
- **Resource Sharing**: Agents coordinate hardware and data access
- **Failure Recovery**: Automatic agent restart and workflow rerouting

---

## Workflow Engine

Complex task orchestration with intelligent dependency management:

- **Natural Language Parsing**: Convert requests into executable workflows
- **Dependency Resolution**: Automatic task sequencing and parallelization
- **Progress Tracking**: Real-time workflow monitoring and status updates
- **Error Handling**: Intelligent retry and escalation strategies
- **Template System**: Reusable workflow patterns for common tasks

---

## Memory & Context

Enhanced persistence and context awareness:

- **SQLite Storage**: Conversation history and agent states
- **Context Engine**: Environment awareness and preference learning
- **Cross-Session Continuity**: Agents remember user patterns and preferences
- **Emotion Integration**: SoulSync emotion detection for adaptive responses
- **Profile Management**: User preferences and behavior patterns

---

## Hardware Optimization

Intelligent backend selection and resource management:

- **Multi-Backend LLM**: Automatic selection (CPU/GPU/Cloud)
- **GGUF Model Support**: Optimized model formats for faster inference
- **Hardware Detection**: Real-time detection of CUDA, Metal, Vulkan, etc.
- **Resource Allocation**: Dynamic hardware assignment based on task requirements
- **Performance Monitoring**: Real-time resource usage and optimization suggestions

---

## Requirements

**Core Dependencies:**
```
Python>=3.10
PySide6>=6.5.0
asyncio-mqtt>=0.13.0
numpy>=1.24.0
faiss-cpu>=1.7.0
```

**LLM Backends:**
```
llama-cpp-python>=0.2.0
ollama>=0.2.0
httpx>=0.25.0
```

**Optional (GPU acceleration):**
```
torch>=2.0.0
pyaccelerate>=0.20.0
```

---

## Roadmap

- [ ] Voice input and output integration
- [ ] Advanced agent marketplace and sharing
- [ ] Workflow template marketplace
- [ ] Multi-device agent synchronization
- [ ] Advanced intent recognition with ML
- [ ] Plugin API for third-party agents
- [ ] Persistent user profile learning
- [ ] Hotkey and gesture integration
- [ ] Advanced workflow visualization
- [ ] Agent performance analytics

---

## Contributing

Contributions welcome! The AI-native OS paradigm opens many exciting possibilities:

1. **Agent Development**: Create specialized agents for specific domains
2. **Workflow Templates**: Design reusable workflow patterns
3. **UI Components**: Build new workspace widgets and interfaces
4. **Backend Integration**: Add support for new LLM providers
5. **Hardware Optimization**: Improve resource management and detection

**Guidelines:**
- Keep changes focused — one concern per PR
- New agents must integrate with the agent mesh
- UI changes must not block the main thread
- Hardware optimizations should benefit all users
- Documentation updates required for new features


See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.


## AIOS — Local AI Runtime [WIP]

**Status:** Core architecture working (SQLite memory, SoulSync emotion engine, agent orchestration). 
UI needs polish. Seeking contributors.

**Why this matters:** The same local-first AI memory architecture has been 
adopted by Y Combinator's president in GBrain. We're building the open-source 
alternative.

**Contributing:** See [CONTRIBUTING.md] for good first issues.

 
---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**AIOS v3.0** — Where AI becomes the operating system, and agents are your applications. 🤖✨

---

## Why AIOS?

| Cloud AI | AIOS |
|----------|------|
| Sends your data to servers | Everything stays local |
| Knowledge cutoff dates | Real-time web research |
| Monthly subscriptions | Free, open source |
| "Trust us" with privacy | Your machine, your control |

---

## Components

**Core (`core/`)**
- `agent.py` — Main orchestrator
- `memory.py` — SQLite persistence
- `soulsync.py` — Emotional intelligence
- `planner.py` — Intent detection
- `llm.py` — Ollama client
- `context_manager.py` — Smart context window
- `mode_controller.py` — Mode detection
- `confidence.py` — Quality scoring

**RAG (`rag/`)**
- `web_search.py` — Searx integration
- `web_fetch.py` — Content extraction
- `processor.py` — Clean + chunk
- `embedder.py` — Local embeddings
- `vector_store.py` — FAISS storage
- `retriever.py` — Smart retrieval
- `pipeline.py` — End-to-end RAG

**Tools (`tools/`)**
- `executor.py` — Sandboxed execution
- `system_tools.py` — File, calc, system

**UI (`ui/`)**
- `chat_ui.py` — Agent-first interface
- `bubble.py` — Floating access

---

## Usage

### Chat Mode

```
You: What's the weather like?
AIOS: I don't have real-time weather data, but I can help you find
      it if you'd like me to search the web.
```

### Research Mode

```
You: Latest developments in AI
AIOS: [Thinking...]
      🔍 Searching web...
      📄 Found 8 relevant sources
      [Provides summary with citations]
```

### Execute Mode

```
You: Calculate 15% of 2847
AIOS: [Using calculator tool]
      427.05
```

---

## Features

- **Streaming responses** — Tokens appear in real-time
- **Thinking indicators** — See what's happening
- **Source citations** — Web results linked
- **Confidence scores** — Know when to trust
- **Emotion adaptation** — Tone matches your mood
- **Persistent memory** — Conversations remembered
- **Knowledge caching** — 24hr freshness
- **Hardware-aware** — Auto-optimizes for your GPU

---

## Roadmap

- [x] Agent system with mode detection
- [x] Persistent memory (SQLite)
- [x] Emotional intelligence (SoulSync)
- [x] Tool execution
- [x] Modern UI with thinking steps
- [x] Web RAG (Searx-based)
- [x] Confidence scoring
- [ ] Voice input/output
- [ ] Custom tool API
- [ ] Plugin system
- [ ] Multi-agent collaboration

---

## Contributing

**Principles:**

1. **Modular** — Each component is self-contained
2. **Clear** — Code explains itself
3. **Extensible** — Easy to add features
4. **Local-first** — No cloud dependencies

See `CONTRIBUTING.md` for guidelines.

---

## License

MIT

---

<div align="center">

Built by [Harshit Gavita](https://github.com/harshitgavita-07)

***Your AI. Your machine. Your data.***
=======
**Built for the local AI future.**

</div>
