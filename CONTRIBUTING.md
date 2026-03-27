# Contributing to Aios

Aios is an open-source local AI desktop assistant. Contributions are welcome!

## Project Structure

```
Aios/
├── app.py           # Entry point (QApplication + Bubble + DesktopAssistant)
├── bubble.py        # Floating always-on-top widget
├── ui.py            # Chat UI — streaming tokens, typing animation, settings
├── worker.py        # QThread wrapper for non-blocking LLM inference
├── brain.py         # Input processing → LLM
├── agent.py         # Router (future: plugins for web search, calendar, etc.)
├── llm.py           # Ollama SDK wrapper — chat, streaming, model management
├── hardware.py      # GPU/CPU/VRAM detection + model recommendation
├── settings.py      # Settings panel — model catalog, download, performance
├── requirements.txt # Runtime dependencies (PySide6 + ollama)
└── requirements-dev.txt
```

## Key Design Decisions

- **Ollama SDK** (`ollama.chat()`) instead of subprocess — cleaner, faster, proper error handling
- **Streaming** — tokens display in real time via `QThread` + Qt signals
- **Hardware-aware** — auto-detects VRAM and picks the best model from installed ones
- **pyaccelerate (optional)** — provides extended GPU info (architecture, CUDA cores, memory type, bandwidth)
- **Non-blocking UI** — all LLM calls run in `worker.py` on a background thread
- **Settings panel** — searchable model catalog with download, performance profiles, dependency management

## Ideas for Contribution

- 🎤 **Voice I/O** — Add speech-to-text input and TTS output
- 🔌 **Plugin system** — Allow custom skill modules in `agent.py` (web search, calendar, etc.)
- ⌨️ **Global hotkey** — Summon the assistant from anywhere on the desktop
- 💾 **Conversation memory** — Persist chat history across sessions
- 🎨 **UI themes** — Light mode, custom color schemes
- 📎 **File/image input** — Drag and drop files for context
- 📊 **Token usage display** — Show tokens/sec and context window usage

## Setup

```bash
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt
python app.py
```

### Optional: Enhanced Hardware Profiling

```bash
pip install pyaccelerate
```

## PR Guidelines

- Keep changes focused and minimal
- Test with at least one Ollama model before submitting
- Use the Ollama SDK (`ollama.chat()`, `ollama.list()`, `ollama.pull()`) — no subprocess
- Keep the UI responsive — run blocking work in `QThread` (see `worker.py`)
- Update README if your change affects usage or adds features
