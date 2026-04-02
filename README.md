<div align="center">

# Aios

**The AI-native desktop runtime.**

*Not an app that runs AI. The workspace where agents are the interface.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black?style=flat-square)](https://ollama.ai)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)
[![Vision](https://img.shields.io/badge/Read-VISION.md-orange?style=flat-square)](VISION.md)

</div>

---

**Every AI desktop tool in 2026 makes the same mistake: it treats AI as an application that runs on top of an OS designed for humans to click things.**

Aios is different. It is the workspace itself — a local AI runtime layer where agents, memory, and on-device intelligence are the primitive building blocks, not features bolted onto a chat window.

[**Read the full vision →**](VISION.md)

---

## What it does today

```
User Input → Agent Controller → SoulSync → Memory → Ollama → Streaming Response
```

- **Agent pipeline** — intent routing, emotion detection, memory-aware context, tool execution
- **Persistent memory** — SQLite at `~/.aios/memory.db`, survives sessions
- **SoulSync** — detects frustration, curiosity, anxiety, excitement and adapts tone in real time
- **gstack workflows** — `/plan`, `/review`, `/ship`, `/investigate` as local Ollama-powered roles
- **Hardware-aware** — detects GPU/VRAM, picks the best Ollama model automatically
- **Streaming UI** — token-by-token display, never blocks, emotion color indicator
- **No cloud** — 100% local, no API keys, no telemetry

---

## Quick start

```bash
# Prerequisites: Python 3.10+, Ollama running, one model pulled
ollama pull llama3.2

git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt
python app.py
```

A floating bubble appears on your desktop. Click to open the agent workspace.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AIOS RUNTIME                             │
│                                                             │
│  bubble.py ──► ui.py (streaming chat, emotion indicator)   │
│                  │                                          │
│              worker.py (QThread)                            │
│                  │                                          │
│           core/agent.py (orchestrator)                      │
│           ├── core/planner.py   (intent routing)            │
│           ├── core/soulsync.py  (emotion + tone)            │
│           ├── core/memory.py    (SQLite persistence)        │
│           └── gstack/           (role-based workflows)      │
│                  │                                          │
│              llm.py → Ollama (local inference)              │
│              hardware.py → GPU/VRAM detection               │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent commands (built-in)

| Say this | What happens |
|----------|-------------|
| Any question | Routes to LLM with full conversation history as context |
| `clear chat` | Wipes memory, starts fresh session |
| `list models` | Shows installed Ollama models |
| `show hardware` | GPU / VRAM / CPU info |
| `help` | Available commands |
| `/plan-ceo-review <task>` | gstack CEO role: rethinks the problem |
| `/review <task>` | gstack Staff Engineer: finds production bugs |
| `/ship <task>` | gstack Release Engineer: pre-ship checklist |
| `/investigate <bug>` | gstack Debugger: root-cause analysis |

---

## Roadmap

We are building toward an AI-native desktop in four phases.

| Phase | Status | What it is |
|-------|--------|-----------|
| 1 — Local AI Runtime | ✅ Shipped | Agent pipeline, memory, SoulSync, gstack |
| 2 — Multi-Agent Workspace | 🔧 Building | Multiple agents, tiling layout, task queue |
| 3 — OS Integration | 📐 Designed | COSMIC applet, systemd service, D-Bus IPC |
| 4 — AI-Native Primitives | 🔬 Research | Agent-as-process, memory-as-filesystem |

[**Full roadmap →**](ROADMAP.md)

---

## Adjacent ecosystem

Aios is designed to integrate with, not replace:

- **[Ollama](https://github.com/ollama/ollama)** — local LLM inference backbone
- **[COSMIC Desktop](https://github.com/pop-os/cosmic-epoch)** — Rust/Wayland compositor for Phase 3
- **[OpenClaw](https://github.com/openclaw/openclaw)** — skills ecosystem (OpenClaw skills as Aios tools)
- **[LocalAI](https://github.com/mudler/LocalAI)** — alternative local inference backend

---

## Contributing

Aios is early. The roadmap is ambitious. Contributions are welcome at every level.

**Good first issues:**
- Make the chat window resizable (PySide6)
- Add `aios memory export` CLI command
- Add `--no-bubble` launch flag
- Write systemd user service template
- Port emotion lexicon to configurable YAML

[**Contributing guide →**](CONTRIBUTING.md) | [**Open roadmap issues →**](https://github.com/harshitgavita-07/Aios/issues)

---

## Requirements

```
PySide6>=6.7.0
ollama>=0.4.0
```

Optional:
```bash
pip install pyaccelerate  # richer GPU detection
```

---

<div align="center">

Built by [Harshit Gavita](https://github.com/harshitgavita-07) · Pimpri-Chinchwad, India

*MIT License · Local · Private · Yours*

</div>
