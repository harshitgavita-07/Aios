<div align="center">

# 🤖 Aios — Local AI Desktop Assistant

### On-device intelligence. No cloud. No API keys. No data leaving your machine.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-black?style=for-the-badge)](https://ollama.ai)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20(Qt)-41CD52?style=for-the-badge)](https://doc.qt.io/qtforpython/)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-brightgreen?style=for-the-badge)]()

</div>

---

## 🔒 Why Aios?

Every AI assistant today sends your data to the cloud — your questions, your context, your private information. **Aios doesn't.**

It runs a full LLM inference engine locally via [Ollama](https://ollama.ai), sits as a floating bubble on your desktop, and responds to natural language queries entirely on your machine.

> Built before "local AI" was a buzzword.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔒 **100% Offline** | All inference runs locally via Ollama — zero network requests |
| 🫧 **Floating Bubble UI** | Always-on-top draggable bubble for instant access |
| 💬 **Streaming Chat** | Real-time token-by-token display with typing indicator |
| 🖥️ **Hardware-Aware** | Auto-detects GPU/VRAM and picks the best model for your machine |
| ⚡ **Non-blocking UI** | LLM runs in a background thread — the interface never freezes |
| ⚙️ **Settings Panel** | Switch models, download new ones, tune performance — all from the UI |
| 🧠 **Pluggable Brain** | Modular agent/router architecture — swap LLMs or add skills |
| 🔧 **Autotune** | Optional Ollama autotune and pyaccelerate integration for speed profiles |

---

## 🏗️ Architecture

```
User Input
    │
    ▼
bubble.py ──► ui.py (Chat UI + Streaming + Typing Indicator)
                │               ▲
                │               │ token_received / generation_finished
                ▼               │
           worker.py (QThread) ─┘
                │
                ▼
           brain.py (Logic)
                │
                ▼
           llm.py (Ollama SDK — chat + streaming)
                │
                ▼
         hardware.py (GPU/CPU detection + model recommendation)
                │
                ▼
         Local LLM via Ollama
         (runs on your GPU/CPU)

  ┌─────────────────────────────┐
  │  settings.py (⚙ Settings)  │
  │  • Auto/Manual model select │
  │  • Model catalog & download │
  │  • Performance profiles     │
  │  • pyaccelerate install     │
  └─────────────────────────────┘
```

**Files:**

| File | Purpose |
|------|---------|
| `app.py` | Entry point — launches QApplication, Bubble, and DesktopAssistant |
| `bubble.py` | Floating always-on-top draggable bubble widget |
| `ui.py` | Main chat window with streaming display, typing animation, and settings |
| `worker.py` | QThread wrapper — runs LLM inference without blocking the UI |
| `brain.py` | Input processing → LLM orchestration |
| `agent.py` | Router layer — future plugins (web search, calendar) plug in here |
| `llm.py` | Ollama SDK wrapper — `ollama.chat()` with streaming and model management |
| `hardware.py` | GPU/VRAM/CPU/RAM detection with model recommendation tiers |
| `settings.py` | Settings panel — model selector, download catalog, performance profiles |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- Any Ollama model pulled (e.g. `ollama pull llama3.2`)

### Install & Run

```bash
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt
python app.py
```

A floating bubble will appear on your desktop. Click it to open the assistant.

### Optional: Enhanced Hardware Profiling

```bash
pip install pyaccelerate
```

When installed, Aios uses pyaccelerate for richer GPU detection — architecture, CUDA cores, memory type, bandwidth, PCIe info, NVENC/NVDEC, and more.

---

## 🖥️ Hardware-Aware Model Selection

Aios automatically detects your hardware at startup and picks the best model from what you have installed:

| VRAM Budget | Recommended Models |
|-------------|-------------------|
| ≤ 4 GB | `llama3.2:1b`, `phi3:mini`, `gemma2:2b` |
| ≤ 6 GB | `llama3.2:3b`, `phi3:3.8b`, `qwen2.5:3b` |
| ≤ 10 GB | `llama3.1:8b`, `gemma3:12b`, `mistral:7b` |
| ≤ 16 GB | `llama3.1:8b`, `qwen2.5:14b`, `deepseek-r1:14b` |
| ≤ 24 GB | `qwen2.5:32b`, `deepseek-r1:32b` |
| 24+ GB | `llama3.1:70b`, `qwen2.5:72b` |

No GPU? Aios falls back to CPU-only mode with a small model.

---

## ⚙️ Settings Panel

Click the ⚙ gear icon in the chat window to access:

- **Model Mode** — Auto (hardware-detected) or Manual selection
- **Download Models** — Searchable catalog of 18+ popular models with installed/available icons
- **Performance Profiles** — speed, balanced, memory, multiuser (via Ollama autotune API)
- **pyaccelerate Install** — One-click install with approval dialog

---

## 🔮 Why This Matters

2025–2026 is the era of **on-device AI**:
- Apple Intelligence runs on-device
- Meta's LLaMA models run on consumer hardware
- Privacy regulations are getting stricter globally

Aios was built with this philosophy from day one: **your AI, your machine, your data.**

---

## 🛣️ Roadmap

- [ ] Voice input / TTS output
- [ ] System prompt customization via UI
- [ ] Plugin system for custom skills (web search, calendar, etc.)
- [ ] Hotkey to summon the assistant from anywhere
- [ ] Memory / conversation history persistence

---

<div align="center">

**Star ⭐ if you believe AI should stay on your machine.**

*Built by [Harshit Gavita](https://github.com/harshitgavita-07)*

</div>
