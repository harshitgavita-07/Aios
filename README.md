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
| **Streaming UI** | Token-by-token display. UI never blocks. |
| **Hardware-aware** | Auto-selects the best model for your GPU/CPU. |
| **Execute** | Run calculations, file operations, system commands |
| **Reason** | Complex analysis with step-by-step thinking |

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
│   └── planner.py       Intent detection (chat / tool / system)
│
└── tools/
    ├── registry.py      Whitelist-only tool registry
    └── think_tool.py    Structured reasoning scratchpad
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

- `think_tool` — structured reasoning scratchpad

To add a tool: implement a `run(payload: str) -> str` function, add the name to `_WHITELIST`, and register it in `ToolRegistry._register_defaults()`.

---

## Requirements

```
PySide6>=6.7.0
ollama>=0.4.0
```

Optional (richer GPU profiling):
```
pip install pyaccelerate
```

---

## Roadmap

- [ ] Voice input (Whisper via Ollama)
- [ ] Per-session system prompt customisation
- [ ] File context — drag a file into chat
- [ ] Plugin API for third-party tools
- [ ] Persistent user profile from conversation patterns
- [ ] Hotkey to summon from anywhere

---

## Contributing

Contributions welcome. Before opening a PR:

1. Keep changes focused — one concern per PR
2. No new heavy dependencies
3. New tools must go through the whitelist system
4. UI changes must not block the main thread

##### See[CONTRIBUTING.md] (CONTRIBUTING.md).

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
