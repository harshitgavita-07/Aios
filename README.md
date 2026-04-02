# AIOS

**A local-first AI runtime with reasoning, memory, and research capabilities.**

```
┌─────────────────────────────────────────────┐
│  Your machine. Your data. Your AI.           │
│  No cloud. No API keys. No compromises.      │
└─────────────────────────────────────────────┘
```

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black?style=flat-square)](https://ollama.ai)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## 📚 Documentation

All documentation is available right here on the homepage:

### 🚀 [Quick Start & Setup](https://github.com/harshitgavita-07/Aios#setup--installation)
Complete installation guide with prerequisites, dependencies, and troubleshooting

### 🛠️ [Contributing Guidelines](https://github.com/harshitgavita-07/Aios#contributing)
How to contribute to AIOS development

### 🤖 [gstack Integration](https://github.com/harshitgavita-07/Aios#gstack-integration--role-based-agent-workflows)
Role-based agent workflows (CEO, Engineer, QA, etc.) powered by Ollama

### 📖 [Full Documentation Index](#)
- [Setup Guide](https://github.com/harshitgavita-07/Aios#setup--installation)
- [Troubleshooting](https://github.com/harshitgavita-07/Aios#troubleshooting)
- [Architecture](https://github.com/harshitgavita-07/Aios#architecture)
- [Tool System](https://github.com/harshitgavita-07/Aios#tool-system)
- [gstack Skills](https://github.com/harshitgavita-07/Aios#available-skills)
- [Contributing](https://github.com/harshitgavita-07/Aios#contributing)

---

## What It Does

AIOS transforms your desktop into an intelligent agent system:

| Capability | What You Can Do |
|------------|-----------------|
| **Chat** | Natural conversations with persistent memory |
| **Research** | "What's the latest news about..." — real-time web search + RAG |
| **Memory** | SQLite conversation history. Context survives restarts. |
| **Emotion awareness** | Detects frustration, curiosity, excitement and adapts tone. |
| **Intent routing** | Distinguishes chat, tool execution, and system commands. |
| **Tool execution** | Whitelist-only tool registry. Safe by default. |
| **Computer control** | Run commands, open apps, take screenshots, monitor processes, control windows |
| **Streaming UI** | Token-by-token display. UI never blocks. |
| **Hardware-aware** | Auto-selects the best model for your GPU/CPU. |
| **Execute** | Run calculations, file operations, system commands |
| **Reason** | Complex analysis with step-by-step thinking |
| **gstack integration** | Role-based agent workflows (CEO, Engineer, QA, etc.) |
| **Professional prompts** | Claude Code, Desktop Code, and Sonnet 4.6 system prompt patterns |

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt

# Run
python app.py
```

A floating bubble appears. Click to open.

---

## Architecture

```
User Input
     │
     ▼
 Planner ─────────────────────────────────┐
 (intent: chat | tool | system)           │
     │                                    │
     ▼                                    ▼
 SoulSync                         System Handler
 (emotion + tone)                 (clear memory, list models, ...)
     │
     ▼
 Memory.history()
 (last N messages)
     │
     ▼
 LLM (Ollama — streaming)
     │
     ▼
 Memory.save()  ──►  UI token stream
```

---

## Project structure

```
Aios/
├── app.py               Entry point
├── bubble.py            Floating desktop bubble (always-on-top)
├── ui.py                Chat window (streaming, emotion indicator, clear button)
├── worker.py            QThread — routes through agent, never blocks UI
├── llm.py               Ollama SDK wrapper (streaming + history)
├── hardware.py          GPU/CPU detection + model recommendation
├── settings.py          Model selector, download catalog, performance profiles
│
├── core/
│   ├── agent.py         Orchestrator — memory + soulsync + planner + LLM
│   ├── memory.py        SQLite conversation store + user profile
│   ├── soulsync.py      Emotion detection + tone adaptation
│   ├── planner.py       Intent detection (chat / tool / system)
│   ├── confidence.py    Confidence scoring for responses
│   ├── context_manager.py Context management and session handling
│   └── mode_controller.py Mode switching and behavior adaptation
│
├── tools/
│   ├── registry.py      Whitelist-only tool registry
│   ├── system_tools.py  Computer control tools (run commands, screenshots, etc.)
│   ├── executor.py      Tool execution engine
│   └── think_tool.py    Structured reasoning scratchpad
│
├── rag/
│   ├── embedder.py      SentenceTransformers integration
│   ├── pipeline.py      RAG processing pipeline
│   ├── processor.py     Document processing and chunking
│   ├── retriever.py     Vector similarity search
│   ├── vector_store.py  FAISS vector database
│   └── web_search.py    Real-time web search integration
│
├── gstack/
│   ├── aios.py          CLI entry point for gstack workflows
│   ├── aios_core.py     AIOS orchestrator (router + Ollama + memory)
│   ├── aios_gstack.py   gstack Python wrapper + Claude Code integration
│   └── core/            gstack core components
│
└── data/
    └── embeddings/
        └── faiss_index/ FAISS vector database storage
```

---

## Quick start

```bash
# Prerequisites: Python 3.10+, Ollama running, at least one model pulled
ollama pull llama3.2

git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt
python app.py
```

A floating bubble appears on your desktop. Click it to open the assistant.

---

## What Aios understands natively

| Input | What happens |
|-------|-------------|
| Any question | Routes to LLM with conversation history as context |
| `clear chat` / `new chat` | Wipes memory, starts fresh session |
| `list models` | Shows installed Ollama models |
| `show hardware` | Displays GPU/VRAM/CPU info |
| `think about X` | Runs structured reasoning step via ThinkTool |
| `run command X` | Executes system command safely |
| `open application Y` | Launches application or opens file |
| `take screenshot` | Captures screen and saves to Documents |
| `show processes` | Lists running processes with CPU/memory usage |
| `control window X` | Minimize/maximize/close/focus windows |
| `calculate X` | Safe mathematical evaluation |
| `read file X` | Reads file contents (sandboxed to Documents/Downloads/Desktop) |
| `write file X` | Writes content to file (sandboxed directories) |
| `list directory X` | Lists directory contents (sandboxed) |
| Frustration keywords | Switches to calm, direct tone |
| Curiosity keywords | Switches to thorough, explanatory tone |

---

## Memory

Conversations are stored in `~/.aios/memory.db` (SQLite).

- The last 20 messages are included in every LLM request as context
- Emotion tags are stored per message for future analytics
- User preferences persist in a `profile` table
- `clear chat` wipes the current session and starts a new one

---

## SoulSync

Rule-based, zero-latency emotion detection (no ML model, no extra dependencies).

Detects: `neutral` `curious` `frustrated` `anxious` `happy` `excited`

Each emotion maps to a different system prompt tone. The mood is visible in the bottom-left of the chat window as a color-coded indicator.

---

## Tool system

Tools are whitelisted explicitly in `tools/registry.py`. Nothing runs unless it is on the whitelist. Currently registered:

**System Tools:**
- `think_tool` — structured reasoning scratchpad
- `calculator` — safe mathematical evaluation
- `file_read` — read files from sandboxed directories
- `file_write` — write files to sandboxed directories
- `list_directory` — browse directory contents (sandboxed)
- `system_info` — get system information and resource usage
- `run_command` — execute system commands safely (dangerous commands blocked)
- `open_application` — launch applications or open files
- `take_screenshot` — capture screen and save to Documents
- `get_running_processes` — monitor running processes with CPU/memory stats
- `control_window` — control application windows (minimize/maximize/close/focus)

**Security:** All file operations are restricted to Documents, Downloads, and Desktop directories. Dangerous system commands are automatically blocked.

To add a tool: implement a `run(payload: str) -> str` function, add the name to `_WHITELIST`, and register it in `ToolRegistry._register_defaults()`.

---

## Requirements

```
PySide6>=6.7.0
ollama>=0.4.0
psutil>=5.9.0
pillow>=10.0.0
pygetwindow>=0.0.9
sentence-transformers>=2.2.0
faiss-cpu>=1.7.0
numpy>=1.24.0
```

Optional (richer GPU profiling):
```
pip install pyaccelerate
```

**New in v2.0:**
- `psutil` — system monitoring and process management
- `pillow` — screenshot capture and image handling
- `pygetwindow` — cross-platform window control
- `sentence-transformers` + `faiss-cpu` — RAG vector search and embeddings

---

## Roadmap

- [x] Computer control tools (run commands, screenshots, window management)
- [x] Enhanced RAG with web search and vector storage
- [x] gstack role-based agent workflows
- [x] Professional Claude system prompt integration
- [x] Cricket expertise and domain knowledge
- [ ] Voice input (Whisper via Ollama)
- [ ] Per-session system prompt customisation
- [ ] File context — drag a file into chat
- [ ] Plugin API for third-party tools
- [ ] Persistent user profile from conversation patterns
- [ ] Hotkey to summon from anywhere

---

## 🤝 Contributing to AIOS

AIOS is an open-source local AI desktop assistant. Contributions are welcome!

### Key Design Decisions
- **Ollama SDK** — cleaner, faster, proper error handling
- **Streaming** — tokens display in real time via QThread + Qt signals
- **Hardware-aware** — auto-detects VRAM and picks the best model
- **Non-blocking UI** — all LLM calls run in background threads
- **Settings panel** — searchable model catalog with download and performance profiles

### Ideas for Contribution
- 🎤 **Voice I/O** — Add speech-to-text input and TTS output
- 🔌 **Plugin system** — Allow custom skill modules
- ⌨️ **Global hotkey** — Summon the assistant from anywhere
- 💾 **Conversation memory** — Persist chat history across sessions
- 🎨 **UI themes** — Light mode, custom color schemes
- 📎 **File/image input** — Drag and drop files for context
- 📊 **Token usage display** — Show tokens/sec and context window usage

### Development Setup
```bash
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt
python app.py
```

---

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Setup & Installation

### Prerequisites

#### 1. Install Ollama

Download and install Ollama for your OS from https://ollama.ai

Then pull a model (recommended for most hardware):
```
ollama pull qwen2.5:7b
```

Low-RAM alternative:
```
ollama pull llama3.2:3b
```

#### 2. Python environment (3.10+)

```bash
# From the repo root
pip install -r requirements.txt
```

**New dependencies for v2.0:**
- `psutil` — system monitoring (processes, CPU, memory)
- `pillow` — screenshot capture
- `pygetwindow` — window control
- `sentence-transformers` — text embeddings for RAG
- `faiss-cpu` — vector search database

#### 3. Run AIOS

**Always run from the repo root directory:**
```bash
# Windows
cd C:\Users\HARSHIT\aios
python app.py

# macOS / Linux
cd ~/aios
python app.py
```

> **Important:** AIOS must be launched from the repo root.
> `hardware.py` lives at the root and is imported by the LLM client.
> Running `python aios/app.py` from a parent directory will fail.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'hardware'`
You are running `app.py` from the wrong directory.
Fix: `cd` into the repo root first, then run `python app.py`.

### `Failed to initialize agent: cannot commit transaction — SQL statements in progress`
This was a SQLite bug fixed in v2.0.1. Pull the latest code:
```bash
git pull origin main
```

### `ollama.ResponseError: model not found`
Run `ollama list` to see what models you have installed, then:
```bash
ollama pull qwen2.5:7b
```

### `ImportError: No module named 'sentence_transformers'`
RAG dependencies are required. Install them:
```bash
pip install sentence-transformers faiss-cpu numpy
```

### Agent initialises but responses are blank / UI freezes
Make sure Ollama is running. Open a terminal and run:
```bash
ollama serve
```
Then restart AIOS.

### Computer control tools not working
Some computer control features require additional permissions or may not work on all systems:

**Screenshots:** Requires `pillow` (PIL) package. May require additional permissions on some Linux systems.

**Window control:** Requires `pygetwindow` package. May have limited functionality on Linux (X11 vs Wayland).

**Process monitoring:** Requires `psutil` package. May require elevated permissions on some systems.

**System commands:** Some commands may be blocked for security. Check the logs for blocked command messages.

### RAG features not working
Make sure vector search dependencies are installed:
```bash
pip install sentence-transformers faiss-cpu numpy
```

If you get import errors, try:
```bash
pip install --upgrade pip
pip install sentence-transformers faiss-cpu numpy
```

---

## gstack Integration — Role-Based Agent Workflows

[gstack](https://github.com/garrytan/gstack) is Garry Tan's Claude Code skill system — a collection of role-based prompt templates (CEO, Staff Engineer, QA Lead, etc.) that run as slash commands inside Claude Code.

**AIOS extracts those role definitions and runs them locally via Ollama**, giving you the same structured, role-based analysis without Claude Code or Anthropic's API.

```
User Input → Router → gstack Skill → Ollama → Memory → Output
```

**Integration with main AIOS:** The gstack skills are now integrated into the main AIOS desktop application. You can access role-based workflows directly through the chat interface using commands like "plan a new feature as CEO" or "review this code as a staff engineer".

### Available Skills

| Skill | Role | What it does |
|-------|------|-------------|
| `/plan-ceo-review` | CEO / Founder | Rethinks the problem. Finds the 10-star product. |
| `/plan-eng-review` | Engineering Manager | Architecture, data flow, test plan, edge cases. |
| `/review` | Staff Engineer | Production bugs, security holes, correctness. |
| `/qa` | QA Lead | Test plan, edge cases, regression risks. |
| `/ship` | Release Engineer | Pre-ship checklist: tests, coverage, rollback. |
| `/investigate` | Debugger | Systematic root-cause analysis. Iron Law: no fix without investigation. |
| `/office-hours` | YC Partner | Six forcing questions that reframe the product. |

### Task Router

Natural language → correct skill, automatically:

| Input | Routes to |
|-------|-----------|
| "build a NLP library" | `/plan-ceo-review` |
| "fix the auth bug" | `/investigate` |
| "deploy to production" | `/ship` |
| "test the login flow" | `/qa` |
| "review the PR" | `/review` |
| "I'm not sure what to build" | `/office-hours` |
| "architect the data model" | `/plan-eng-review` |

### Python API for gstack

```python
from aios_core import AIOS

aios = AIOS(model="llama3")

# Natural language — router picks the right skill
result = aios.run("build a NLP library for Hindi")

# Explicit skill
result = aios.plan("build BharatLang — a Python NLP library for Hindi/Indic languages")
result = aios.review("check the tokenizer module for correctness and edge cases")
result = aios.qa("verify the stemmer handles zero-length input")
result = aios.ship("pre-ship checklist for v0.1 release")
result = aios.investigate("stemmer crashes on empty string input")

print(result.output)
print(f"Skill: /{result.skill} | Model: {result.model} | ID: {result.task_id}")
```

### CLI Usage

```bash
# Run a task
python aios.py "build a NLP library for Hindi"

# Explicit skill command
python aios.py /plan-ceo-review "build BharatLang NLP library"
python aios.py /review "check the authentication module for security issues"
python aios.py /ship "pre-ship checklist for v1.0 release"
python aios.py /investigate "login fails for users with special characters in email"

# Stream output as it generates
python aios.py --stream /plan-ceo-review "build BharatLang"

# System status
python aios.py --status

# Recent history
python aios.py --history

# List all skills
python aios.py --list-skills
```

### gstack Memory

All tasks are persisted to `~/.aios-gstack/memory.json`:

```json
{
  "tasks": [
    {
      "id": "a1b2c3d4",
      "skill": "plan-ceo-review",
      "input": "Build BharatLang NLP library",
      "output": "...",
      "model": "llama3",
      "ts_human": "2026-03-31 14:23:11"
    }
  ]
}
```

Access via Python:
```python
aios = AIOS()
history = aios.history(n=10)
for task in history:
    print(f"/{task['skill']}: {task['input'][:60]}")
```

---

## 📖 Documentation Index

All AIOS documentation is available right here on the homepage:

### 🚀 Getting Started
- **[Quick Start](#quick-start)** — Get AIOS running in 5 minutes
- **[Setup & Installation](#setup--installation)** — Complete installation guide
- **[Prerequisites](#prerequisites)** — What you need before installing
- **[Troubleshooting](#troubleshooting)** — Solutions to common issues

### 🏗️ Architecture & Development
- **[Architecture](#architecture)** — How AIOS works internally
- **[Project Structure](#project-structure)** — Code organization
- **[Tool System](#tool-system)** — Available tools and security
- **[Memory System](#memory)** — Conversation persistence
- **[SoulSync](#soulsync)** — Emotion detection and adaptation

### 🤖 Advanced Features
- **[gstack Integration](#gstack-integration--role-based-agent-workflows)** — Role-based agent workflows
- **[Available Skills](#available-skills)** — CEO, Engineer, QA, and more
- **[RAG Features](#troubleshooting)** — Web search and vector storage
- **[Computer Control](#what-aiOS-understands-natively)** — System automation tools

### 📝 Development & Contribution
- **[Contributing to AIOS](#-contributing-to-aiOS)** — How to contribute
- **[Development Setup](#development-setup)** — For contributors
- **[Roadmap](#roadmap)** — Future features and plans
- **[Requirements](#requirements)** — Dependencies and versions

### 📄 Documentation Files
- **[README.md](https://github.com/harshitgavita-07/Aios/blob/main/README.md)** — This main documentation
- **[CONTRIBUTING.md](https://github.com/harshitgavita-07/Aios/blob/main/CONTRIBUTING.md)** — Contribution guidelines
- **[SETUP.md](https://github.com/harshitgavita-07/Aios/blob/main/SETUP.md)** — Detailed setup instructions
- **[gstack/README.md](https://github.com/harshitgavita-07/Aios/blob/main/gstack/README.md)** — gstack integration docs

---

## Contributing

Contributions welcome. Before opening a PR:

1. Keep changes focused — one concern per PR
2. No new heavy dependencies
3. New tools must go through the whitelist system
4. UI changes must not block the main thread

<<<<<<< HEAD
See [CONTRIBUTING.md](CONTRIBUTING.md).
           └──────┬──────┘
                  │
                  ▼
            Streaming Response
```
=======
##### See[https://github.com/harshitgavita-07/Aios/edit/main/CONTRIBUTING.md] (CONTRIBUTING.md).
>>>>>>> b16e19e598d43e6ae966ec65a3a306a0021919a9

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
