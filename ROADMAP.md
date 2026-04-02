# Aios Roadmap

Concrete milestones toward an AI-native desktop runtime.
See [VISION.md](VISION.md) for the full architectural philosophy.

---

## ✅ Phase 1 — Local AI Runtime (Complete)

These are shipped on `aios-v2-upgrade` and will merge to `main`:

- [x] Hardware-aware model selection (GPU/VRAM detection → Ollama model pick)
- [x] SQLite conversation memory (`core/memory.py`)
- [x] Emotion detection + tone adaptation (`core/soulsync.py` — 6 emotions, ~0ms)
- [x] Intent routing — chat / tool / system commands (`core/planner.py`)
- [x] Agent controller — full pipeline orchestrator (`core/agent.py`)
- [x] Streaming UI — token-by-token, never blocks (`worker.py` + `ui.py`)
- [x] gstack role-based workflows — plan / review / ship / investigate (`gstack/`)
- [x] Settings panel — model switch, download catalog, performance profiles
- [x] Floating desktop bubble (always-on-top, draggable)

---

## 🔧 Phase 2 — Multi-Agent Workspace (Q3 2026)

These are open. See issues for details.

### Core runtime
- [ ] **Named persistent agents** — `aios agents new --name "dev" --role engineer`
  Each agent has isolated memory, session history, and configurable system prompt.
  *Skill needed: Python, SQLite schema design*

- [ ] **Agent-to-agent delegation** — `aios run --agent dev "review this for security issues"`
  The primary agent can delegate a sub-task to a named specialist agent.
  *Skill needed: Python async, IPC design*

- [ ] **Background agent daemon** — `aios serve` starts a persistent background process
  Agents run independently of the UI. Tasks can be queued and processed async.
  *Skill needed: Python asyncio, systemd user services*

### UI layer
- [ ] **Tiling agent workspace** — split-pane layout (i3-style, not overlapping windows)
  Each pane shows a different agent's conversation and status.
  *Skill needed: PySide6, layout management*

- [ ] **Agent task queue panel** — sidebar showing pending / running / completed tasks
  Visual progress for long-running agent work.
  *Skill needed: PySide6, signals/slots*

- [ ] **Command palette** — `Ctrl+K` global hotkey, type a task, pick an agent
  *Skill needed: PySide6 global hotkeys, overlay widget*

- [ ] **Resizable window** — current UI is fixed 560×660, should be resizable
  *Good first issue — PySide6 layout, remove `setFixedSize`*

### Memory
- [ ] **Vector similarity search** — `core/memory.py` semantic search over past conversations
  Use sqlite-vec or chromadb. No cloud. Find "things I discussed about X" without exact keywords.
  *Skill needed: Python, embeddings, sqlite-vec*

- [ ] **Memory export/import** — `aios memory export --format json/markdown`
  *Good first issue*

---

## 🚀 Phase 3 — OS Integration Layer (Q4 2026)

### COSMIC Desktop integration
- [ ] **COSMIC applet** — agent status and quick-command in the COSMIC panel
  Rust + iced toolkit. Shows active agent, last task, and command input.
  *Skill needed: Rust, iced, COSMIC applet API*

- [ ] **COSMIC settings page** — Aios configuration inside COSMIC Settings
  Model selection, memory settings, agent management.
  *Skill needed: Rust, iced, COSMIC settings API*

### System integration
- [ ] **Systemd user service** — `aios.service` for auto-start on login
  `~/.config/systemd/user/aios.service`
  *Good first issue — systemd template, Python packaging*

- [ ] **D-Bus interface** — expose agent operations over D-Bus
  Any app on the system can send: `dbus-send --session ... aios.RunTask`
  *Skill needed: Python dbus-python or dbus-fast*

- [ ] **Unix socket IPC** — `~/.aios/aios.sock` for low-latency local communication
  Allows shell scripts and other processes to queue tasks without D-Bus overhead.
  *Skill needed: Python asyncio, unix sockets*

### Package distribution
- [ ] **AUR package** — `aios-git` for Arch Linux
  *Good first issue — PKGBUILD, Python packaging*

- [ ] **Flatpak manifest** — `ai.harshit.Aios.yml`
  *Skill needed: Flatpak, sandbox permissions*

- [ ] **Debian package** — for Pop!_OS / Ubuntu integration with COSMIC
  *Skill needed: Debian packaging*

---

## 🔬 Phase 4 — AI-Native Primitives (2027)

Longer-horizon, research-heavy. Contributions welcome at the design level.

- [ ] **Agent-as-process** — agents appear in `ps aux`, have PIDs, `kill` restarts them
- [ ] **Memory-as-filesystem** — FUSE mount at `~/.aios/memory/` (ls, grep, cat work)
- [ ] **Wayland protocol extension** — agent context carried through compositor to any app
- [ ] **Multi-device mesh** — agents on multiple machines form a coherent cluster

---

## Good First Issues

These are well-scoped, don't require deep knowledge of the codebase, and are genuinely useful:

| Issue | Skill | Estimated effort |
|-------|-------|-----------------|
| Make the chat window resizable | PySide6 | 30 min |
| Add `aios memory export` CLI command | Python | 1–2 hours |
| Write systemd user service template | systemd | 1 hour |
| Add AUR PKGBUILD | Packaging | 2–3 hours |
| Add `--no-bubble` flag to run without floating bubble | PySide6 / argparse | 1 hour |
| Port emotion lexicon to configurable YAML | Python / YAML | 1–2 hours |
| Add `ollama pull` progress bar to settings panel | PySide6, Ollama API | 2–3 hours |
| Write man page (`man aios`) | man/troff | 1 hour |

---

## How to Contribute

1. Pick an issue or open one describing what you want to build
2. Comment on the issue — we'll discuss scope and approach before you start
3. Fork, implement, open a PR against `main`
4. PRs should be focused — one concern per PR
5. No new heavy dependencies without discussion first

See [CONTRIBUTING.md](CONTRIBUTING.md) for full details.

---

## Release cadence

No fixed release schedule yet. We merge to `main` when things are stable and tested.
Every merge to `main` should leave Aios in a working state for end users.
