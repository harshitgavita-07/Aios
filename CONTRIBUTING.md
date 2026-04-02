# Contributing to Aios

Aios is building toward an AI-native desktop runtime. Contributions are welcome at every layer — from fixing a typo to implementing D-Bus IPC.

---

## Before you start

Read [VISION.md](VISION.md) to understand where we are going.
Read [ROADMAP.md](ROADMAP.md) to find what is open.

If your change is small (bug fix, typo, resizing a widget), just open a PR.
If your change is significant (new module, architectural change), open an issue first and discuss scope.

---

## Setup

```bash
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios
pip install -r requirements.txt

# Requires Ollama running with at least one model
ollama serve &
ollama pull llama3.2

python app.py
```

---

## Project structure

```
Aios/
├── app.py           Entry point
├── bubble.py        Floating desktop bubble
├── ui.py            Chat window (PySide6)
├── worker.py        QThread — routes through agent pipeline
├── llm.py           Ollama SDK wrapper
├── hardware.py      GPU/CPU detection
├── settings.py      Model manager panel
│
├── core/
│   ├── agent.py     Orchestrator — the central controller
│   ├── memory.py    SQLite conversation store
│   ├── soulsync.py  Emotion detection + tone adaptation
│   └── planner.py   Intent routing
│
├── gstack/          Role-based agent workflows (plan/review/ship)
└── tools/           Tool registry (whitelist-only)
```

---

## Constraints

- **No new heavy dependencies** without discussion. Current stack: PySide6, ollama SDK, stdlib only.
- **UI changes must not block the main thread.** All LLM/agent work goes through `worker.py` (QThread).
- **New tools must go through the whitelist** in `tools/registry.py`. Security by default.
- **PRs should be focused.** One concern per PR. Makes review tractable.
- **Tests for core/ modules.** `core/` logic should have corresponding tests. UI changes don't require tests.

---

## Running tests

```bash
# Core logic tests (no Ollama needed)
python -m unittest discover -s tests -v

# gstack integration tests
python -m unittest gstack/tests/test_core.py -v
```

---

## Code style

- Python 3.10+ type hints where it adds clarity
- Docstrings on public functions/classes
- `logging` not `print` for debug output (users can set `--verbose`)
- Line length: 100 chars (not strict, use judgment)
- No auto-formatter enforced yet — match the style of the file you're editing

---

## Good first issues

If you are new to the codebase, start here:

- **Make the chat window resizable** — `ui.py`, remove `setFixedSize(560, 660)`, test that layout stays correct
- **Add `aios memory export` CLI** — `app.py` argparse, `core/memory.py` export function
- **Add `--no-bubble` flag** — launch Aios without the floating bubble for keyboard-only workflows
- **Systemd user service template** — `aios.service` file so Aios auto-starts on login
- **Port emotion lexicon to YAML** — make `core/soulsync.py` keywords configurable without code changes

---

## Larger contributions

If you want to work on something in [ROADMAP.md](ROADMAP.md), open an issue with:

1. Which roadmap item you want to tackle
2. Your proposed approach (a few sentences is fine)
3. Any questions or blockers

We will discuss before you spend significant time coding.

---

## Collaboration with adjacent projects

Aios wants to integrate with:
- **Ollama** — local LLM backbone
- **COSMIC desktop** — Wayland-native compositor for Phase 3 applet
- **OpenClaw** — skills ecosystem (OpenClaw skills as Aios tools)
- **LocalAI** — alternative inference backend

If you have experience with any of these, mention it in your issue — it helps prioritize.

---

## License

MIT. All contributions are MIT licensed.

By contributing, you agree your code may be distributed under the MIT License.
