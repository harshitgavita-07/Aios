# Aios — Vision: The AI-Native Desktop

> *Windows gave us the application. Linux gave us the process. Aios gives you the agent.*

---

## The Problem With Every Current Approach

Every "AI desktop tool" built in 2025–2026 makes the same mistake: it treats AI as an application that runs on top of an operating system designed for humans to manually click things.

OpenClaw is brilliant — but it is fundamentally a messaging bot that your OS hosts.
Open WebUI is brilliant — but it is a browser tab.
Claude Code is brilliant — but it is a terminal process.

None of them are the *environment itself*.

The question nobody has answered: **what does a desktop look like when agents are the first-class citizens, not applications?**

---

## What We Are Building

Aios is not an app. It is a **local AI runtime layer** — the workspace itself, where agents, memory, and intelligence are the primitive building blocks of how you interact with your machine.

The analogy is precise:

| Era | Paradigm | Primitive |
|-----|----------|-----------|
| 1980s | Command line | Commands |
| 1990s | Desktop (Windows/macOS) | Applications |
| 2000s | Web | Documents/URLs |
| 2010s | Mobile | Apps/touch |
| **2026+** | **AI-native desktop** | **Agents** |

We are building for the 2026+ row.

---

## The Three Principles

**1. Agents, not apps.**
The thing you launch should not be "the AI app." The entire workspace should be AI-aware. Every surface — your file manager, your task switcher, your notification system — understands agent context.

**2. Local, always.**
Your data, your models, your memory. Ollama on your GPU, SQLite on your disk. No cloud dependency for core operation. Privacy is not a feature — it is the architecture.

**3. Composable, not monolithic.**
Aios is a runtime layer, not a locked product. COSMIC provides the compositor. Ollama provides inference. Aios provides the agent orchestration that connects them. Every piece is replaceable.

---

## The Architecture We Are Building Toward

```
┌─────────────────────────────────────────────────────────────────┐
│                    AIOS RUNTIME LAYER                           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Agent Shell  │  │ Memory Layer │  │   Tool Executor      │  │
│  │ (workspace)  │  │ (SQLite/vec) │  │   (sandboxed)        │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│  ┌──────▼─────────────────▼──────────────────────▼───────────┐  │
│  │              Agent Orchestrator (core/agent.py)           │  │
│  │         Intent → Plan → Execute → Reflect → Memory       │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                   LLM Runtime (Ollama)                    │  │
│  │              Local models · Hardware-aware                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐    │
│  │  PySide6 UI │  │COSMIC applet│  │  CLI / headless      │    │
│  │  (current)  │  │ (roadmap)   │  │  (roadmap)           │    │
│  └─────────────┘  └─────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Phases

### Phase 1 — Local AI Runtime (now)
**Status: shipped on `aios-v2-upgrade`**

The foundation is working:
- Hardware-aware model selection (Ollama)
- SQLite memory with session persistence
- Emotion detection + tone adaptation (SoulSync)
- Intent routing (chat / tool / system)
- Streaming UI that never blocks
- gstack role-based workflows (plan / review / ship / investigate)

This is a working local AI agent you can use today.

### Phase 2 — Multi-Agent Workspace
**Target: Q3 2026**

The workspace becomes agent-native:
- Multiple named agents running concurrently (each with isolated memory)
- Agent-to-agent messaging (one agent delegates to another)
- Persistent agent roles: you summon "my dev agent" or "my research agent"
- Tiling workspace: agents in a split-pane layout like i3 / tmux, not overlapping windows
- Agent task queue with status indicators

### Phase 3 — OS Integration Layer
**Target: Q4 2026**

Aios stops being a PySide6 app and starts being infrastructure:
- **COSMIC applet**: native agent status bar + command palette for COSMIC desktop
- **Wayland protocol extension**: agent context passed to any window (agents know what you're looking at)
- **File system bridge**: `~/.aios/agents/` as a real directory agents read/write directly
- **Systemd user service**: agents run as persistent background processes, not just when the UI is open
- **IPC socket**: any process on your machine can send tasks to an Aios agent

### Phase 4 — AI-Native Primitives
**Target: 2027**

This is the real vision. The OS itself becomes agent-aware:
- **Agent-as-process**: agents have PIDs, show up in `ps`, can be `kill`-ed and restarted
- **Memory-as-filesystem**: agent memory is a FUSE filesystem you can `ls`, `grep`, `cat`
- **Intent-aware compositor**: the window manager routes input based on agent context, not just focus
- **Multi-device agent mesh**: your agents on laptop, desktop, and server form a coherent cluster

---

## Why This Is Different

| Tool | Paradigm | Where agents live |
|------|----------|------------------|
| OpenClaw | Messaging bot on your OS | Inside WhatsApp/Telegram |
| Open WebUI | Browser tab | Inside Chrome |
| Claude Code | Terminal process | Inside your shell |
| Aios | The workspace itself | **Aios is the desktop layer** |

OpenClaw asks: *"How do I reach the user through their existing apps?"*
Aios asks: *"What if the desktop was designed for agents from the start?"*

These are compatible, not competing. Aios can run OpenClaw as a tool. The difference is architectural ambition.

---

## Adjacent Projects We Want to Collaborate With

### Ollama
- Aios is built on Ollama for local inference
- Target: Aios as a reference integration for Ollama's agent workflow
- Collaboration: hardware detection improvements, model routing, streaming protocol
- Contact: github.com/ollama/ollama

### COSMIC Desktop (System76)
- COSMIC is the first serious Wayland-native, Rust-first desktop — modular by design
- Their Epoch 2 roadmap has no AI integration
- Target: Aios COSMIC applet (agent status, command palette, workspace awareness)
- This is the right compositor for an AI-native desktop layer
- Contact: github.com/pop-os/cosmic-epoch

### LocalAI / LocalAGI
- LocalAI provides a drop-in OpenAI-compatible local backend
- Aios can use LocalAI as an alternative inference backend (not just Ollama)
- Collaboration: shared hardware detection, common agent protocol
- Contact: github.com/mudler/LocalAI

### OpenClaw
- OpenClaw is a skills-based agent runtime with 247K stars
- Aios can host OpenClaw skills as first-class tools
- Target: `aios run /openclaw-skill` — use OpenClaw's skill ecosystem from Aios
- Contact: github.com/openclaw/openclaw

---

## What We Need

### Code contributors
- Python / PySide6 for Phase 2 multi-agent workspace
- Rust for Phase 3 COSMIC integration (iced toolkit)
- Systems background for Phase 3 IPC, systemd service
- UI/UX for the agent workspace layout

### Research contributors
- Agent memory architectures (episodic vs semantic vs procedural)
- Intent detection beyond keyword matching (small classification models)
- Privacy-preserving agent telemetry

### Ecosystem contributors
- Package maintainers (Flatpak, AUR, Debian)
- Hardware testing (AMD, Apple Silicon, low-VRAM devices)
- Translations

---

## The One Sentence

**Aios is what happens when you design a desktop from the assumption that intelligence is local, agents are processes, and memory is infrastructure — not features bolted onto an app.**

---

*Built by [Harshit Gavita](https://github.com/harshitgavita-07) in Pimpri-Chinchwad, India.*
*MIT License. Fork it. Break it. Make it yours.*
