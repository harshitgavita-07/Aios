# AIOS v2.0 — Setup Guide

## Prerequisites

### 1. Install Ollama

Download and install Ollama for your OS from https://ollama.ai

Then pull a model (recommended for most hardware):
```
ollama pull qwen2.5:7b
```

Low-RAM alternative:
```
ollama pull llama3.2:3b
```

### 2. Python environment (3.10+)

```bash
# From the repo root
pip install -r requirements.txt
```

### 3. Run AIOS

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

---

## Project structure
```
aios/
├── app.py              ← Entry point. Always run from here.
├── hardware.py         ← Hardware detection (must be at repo root)
├── requirements.txt    ← pip dependencies
├── core/               ← Agent, memory, emotion, LLM client
├── ui/                 ← Qt chat window + floating bubble
├── tools/              ← Tool executor and system tools
├── rag/                ← FAISS vector store + web search
└── gstack/             ← Ollama integration layer
```
