# 🤖 AIOS v2.0 — Local AI Runtime

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-000000?style=flat)](https://ollama.ai)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](LICENSE)

**Your personal AI runtime. Agent system, memory, emotion, and tool execution — entirely on your machine.**

</div>

---

## ✨ What is AIOS?

AIOS is a **local-first AI runtime** that transforms your desktop into an intelligent agent system. Unlike cloud-based assistants, AIOS runs entirely on your machine — your data never leaves your computer.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🧠 **Agent System** | Intent detection, planning, and task execution |
| 💾 **Persistent Memory** | SQLite-based conversation history across sessions |
| 😊 **SoulSync** | Emotional intelligence and tone adaptation |
| 🔧 **Tool Execution** | Whitelist-based system tools (calculator, files, system info) |
| ⚡ **Streaming** | Real-time token-by-token response display |
| 🖥️ **Hardware-Aware** | Auto-detects GPU/VRAM, optimizes model selection |

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌─────────────────┐
│  AgentController│ ← Main orchestrator
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ▼         ▼        ▼        ▼
┌──────┐  ┌──────┐ ┌──────┐ ┌──────┐
│Memory │  │SoulSync│ │Planner│ │ Tools │
│Store  │  │(Emotion)│ │       │ │       │
└──┬───┘  └───────┘ └───┬───┘ └───┬───┘
   │                    │         │
   └────────────────────┴─────────┘
                      │
                      ▼
               ┌──────────┐
               │  LLM     │ ← Ollama (local)
               │  Client  │
               └────┬─────┘
                    │
                    ▼
            Streaming Response
                    │
                    ▼
              ┌──────────┐
              │  Chat UI │ ← PySide6 (modern dark theme)
              │ (bubble) │
              └──────────┘
```

### Module Breakdown

| Module | Purpose |
|--------|---------|
| `core/agent.py` | AgentController — main orchestrator |
| `core/memory.py` | SQLite conversation persistence |
| `core/soulsync.py` | Emotion detection & tone adaptation |
| `core/planner.py` | Intent detection & task planning |
| `core/llm.py` | Ollama client with caching |
| `tools/executor.py` | Whitelist-based tool execution |
| `tools/system_tools.py` | Built-in system tools |
| `ui/chat_ui.py` | Modern PySide6 interface |
| `ui/bubble.py` | Floating quick-access bubble |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.ai)** installed and running
- Any Ollama model pulled (e.g., `ollama pull llama3.2`)

### Installation

```bash
# Clone the repository
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios

# Install dependencies
pip install -r requirements.txt

# Run AIOS
python app.py
```

A floating bubble will appear on your desktop. Click it to open the assistant window.

---

## 💻 Usage

### Chat Interface

The main window features:
- **Left Panel**: Conversation history and thread management
- **Center Panel**: Chat display with streaming responses
- **Right Panel**: System status and quick actions
- **Bottom**: Input field with command support

### Commands

Type `/help` in the chat for available commands:

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear current conversation |
| `/status` | Show system status |
| `/memory` | Show memory statistics |

### Floating Bubble

- **Click**: Open chat window
- **Drag**: Reposition anywhere on screen
- **Always on top**: Access from any application

---

## 🖥️ Hardware-Aware Model Selection

AIOS automatically detects your hardware and recommends the optimal model:

| VRAM | Recommended Models |
|------|-------------------|
| ≤ 4 GB | `llama3.2:1b`, `phi3:mini`, `gemma2:2b` |
| ≤ 6 GB | `llama3.2:3b`, `phi3:3.8b`, `qwen2.5:3b` |
| ≤ 10 GB | `llama3.1:8b`, `mistral:7b`, `qwen2.5:7b` |
| ≤ 16 GB | `qwen2.5:14b`, `deepseek-r1:14b` |
| ≤ 24 GB | `qwen2.5:32b`, `deepseek-r1:32b` |
| 24+ GB | `llama3.1:70b`, `qwen2.5:72b` |

---

## 🔧 Tool System

AIOS includes sandboxed tools for safe system interaction:

| Tool | Description |
|------|-------------|
| `think` | Structured reasoning step |
| `calculator` | Safe mathematical evaluation |
| `file_read` | Read files (restricted directories) |
| `file_write` | Write files (restricted directories) |
| `list_directory` | Browse directories |
| `system_info` | Hardware and system information |

**Security**: All tools are **whitelisted** — only registered, approved tools can execute. File operations are restricted to `~/Documents`, `~/Downloads`, and `~/Desktop`.

---

## 🧠 SoulSync (Emotional Intelligence)

SoulSync analyzes your messages for emotional content and adapts the AI's tone:

**Detected Emotions**: joy, anger, sadness, fear, surprise, confusion, urgency, neutral

**Tone Adaptations**:
- **Joy** → Enthusiastic, casual
- **Anger** → Calm, soothing
- **Confusion** → Patient, technical
- **Urgency** → Direct, concise

Your emotional patterns and user profile persist across sessions in `data/user_profile.json`.

---

## 🗂️ Memory System

Conversations are stored in `data/aios_memory.db`:

- **Persistent threads**: Multiple conversation contexts
- **Message history**: Last 20 messages in context window
- **Metadata tracking**: Tool calls, emotions, timestamps
- **Searchable**: Query past conversations

---

## 🛣️ Roadmap

- [x] Agent system with intent detection
- [x] Persistent memory (SQLite)
- [x] Emotional intelligence (SoulSync)
- [x] Tool execution system
- [x] Modern PySide6 UI
- [ ] Voice input / TTS output
- [ ] Custom tool creation API
- [ ] Plugin/extension system
- [ ] Hotkey activation
- [ ] Model fine-tuning support
- [ ] Multi-agent collaboration

---

## 🤝 Contributing

We welcome contributions! Areas of interest:

- **New tools**: File operations, web scraping (local), API integrations
- **UI improvements**: Themes, accessibility, animations
- **Core features**: Multi-agent, tool creation API
- **Documentation**: Tutorials, examples, architecture guides

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the local AI community**

*Star ⭐ if you believe AI should stay on your machine*

</div>
