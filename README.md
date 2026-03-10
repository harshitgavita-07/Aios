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
| 💬 **Natural Language Chat** | Full chat UI built with PySide6/Qt |
| 🧠 **Pluggable Brain** | Modular agent/router architecture — swap LLMs or add skills |
| ⚡ **Graceful Fallbacks** | Works even if model or brain is temporarily unavailable |
| 🔧 **Configurable** | Change the LLM model in one line in `llm.py` |

---

## 🏗️ Architecture

```
User Input
    │
    ▼
bubble.py ──► ui.py (Chat UI)
                │
                ▼
           agent.py (Router)
                │
                ▼
           brain.py (Logic + Safeguards)
                │
                ▼
           llm.py (Ollama wrapper)
                │
                ▼
         Local LLM Model
         (runs on your GPU/CPU)
```

**Files:**
- `app.py` — Entry point, starts the Qt app
- `bubble.py` — Always-on-top floating bubble widget
- `ui.py` — Main chat interface
- `agent.py` — Routes user input to the brain
- `brain.py` — Input sanitization + LLM calls
- `llm.py` — Thin Ollama wrapper

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

---

## 🔮 Why This Matters

2025 is the year of **on-device AI**:
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
