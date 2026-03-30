# AIOS

**A local-first AI runtime with reasoning, memory, and research capabilities.**

```
┌─────────────────────────────────────────────┐
│  Your machine. Your data. Your AI.           │
│  No cloud. No API keys. No compromises.      │
└─────────────────────────────────────────────┘
```

---

## What It Does

AIOS transforms your desktop into an intelligent agent system:

| Capability | What You Can Do |
|------------|-----------------|
| **Chat** | Natural conversations with persistent memory |
| **Research** | "What's the latest news about..." — real-time web search + RAG |
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
┌─────────────────┐
│  Mode Controller│  → Detect: Chat / Research / Execute / Reason
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────┐
    ▼         ▼          ▼         ▼
┌──────┐  ┌──────┐  ┌─────────┐ ┌──────┐
│Memory│  │ RAG  │  │ Web-RAG │ │Tools │
│Store │  │Vector│  │Search   │ │Exec  │
└──┬───┘  │Store │  │Fetch    │ └──┬───┘
   │      └──────┘  └────┬────┘    │
   │                     │         │
   └─────────────────────┴─────────┘
                    │
                    ▼
           ┌─────────────┐
           │Context Mgr  │  → Build optimal context window
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │ SoulSync    │  → Emotion detection + Tone adaptation
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │ LLM (Ollama)│  → Local inference
           └──────┬──────┘
                  │
                  ▼
           ┌─────────────┐
           │ Confidence  │  → Quality scoring + Fallback
           └──────┬──────┘
                  │
                  ▼
            Streaming Response
```

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

**Built for the local AI future.**

</div>
