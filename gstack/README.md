# AIOS — Local AI Operating System

**gstack role-based agent workflows, powered by Ollama. No cloud. No API keys.**

---

## What this is

[gstack](https://github.com/garrytan/gstack) is Garry Tan's Claude Code skill system — a collection of role-based prompt templates (CEO, Staff Engineer, QA Lead, etc.) that run as slash commands inside Claude Code.

**AIOS extracts those role definitions and runs them locally via Ollama**, giving you the same structured, role-based analysis without Claude Code or Anthropic's API.

```
User Input → Router → gstack Skill → Ollama → Memory → Output
```

**Integration with main AIOS:** The gstack skills are now integrated into the main AIOS desktop application. You can access role-based workflows directly through the chat interface using commands like "plan a new feature as CEO" or "review this code as a staff engineer".

---

## Honest architecture note

gstack is **not** a TypeScript app with pluggable LLM providers. It is Markdown prompt files that Claude Code reads. There is no `providers/ollama.ts` to add to gstack itself.

What AIOS does instead: reads gstack's role personas and instructions, sends them to Ollama as system prompts, and stores the results in local JSON memory. The skills work identically — the LLM backend changes.

---

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) installed and running
- At least one model pulled

```bash
# Install Ollama, then:
ollama serve
ollama pull llama3
```

---

## Quick start

```bash
git clone <this-repo>
cd aios-gstack

# Run a task
python aios.py "build a NLP library for Hindi"

# Explicit skill command
python aios.py /plan-ceo-review "build BharatLang NLP library"
python aios.py /review "check the authentication module for security issues"
python aios.py /ship "pre-ship checklist for v1.0 release"
python aios.py /investigate "login fails for users with special characters in email"

# Stream output as it generates
python aios.py --stream /plan-ceo-review "build BharatLang"

# System status
python aios.py --status

# Recent history
python aios.py --history

# List all skills
python aios.py --list-skills
```

---

## Python API

```python
from aios_core import AIOS

aios = AIOS(model="llama3")

# Natural language — router picks the right skill
result = aios.run("build a NLP library for Hindi")

# Explicit skill
result = aios.plan("build BharatLang — a Python NLP library for Hindi/Indic languages")
result = aios.review("check the tokenizer module for correctness and edge cases")
result = aios.qa("verify the stemmer handles zero-length input")
result = aios.ship("pre-ship checklist for v0.1 release")
result = aios.investigate("stemmer crashes on empty string input")

print(result.output)
print(f"Skill: /{result.skill} | Model: {result.model} | ID: {result.task_id}")
```

---

## The `run_gstack()` convenience function

```python
from aios_gstack import run_gstack

# Matches the interface described in the original requirement
result = run_gstack("/plan-ceo-review", "Build BharatLang NLP library")
result = run_gstack("/review", "check auth module")
result = run_gstack("/ship", "v1.0 release")
result = run_gstack("/investigate", "login fails on edge case input")

print(result.output)
```

---

## Task router

Natural language → correct skill, automatically:

| Input | Routes to |
|-------|-----------|
| "build a NLP library" | `/plan-ceo-review` |
| "fix the auth bug" | `/investigate` |
| "deploy to production" | `/ship` |
| "test the login flow" | `/qa` |
| "review the PR" | `/review` |
| "I'm not sure what to build" | `/office-hours` |
| "architect the data model" | `/plan-eng-review` |

---

## Available skills

| Skill | Role | What it does |
|-------|------|-------------|
| `/plan-ceo-review` | CEO / Founder | Rethinks the problem. Finds the 10-star product. |
| `/plan-eng-review` | Engineering Manager | Architecture, data flow, test plan, edge cases. |
| `/review` | Staff Engineer | Production bugs, security holes, correctness. |
| `/qa` | QA Lead | Test plan, edge cases, regression risks. |
| `/ship` | Release Engineer | Pre-ship checklist: tests, coverage, rollback. |
| `/investigate` | Debugger | Systematic root-cause analysis. Iron Law: no fix without investigation. |
| `/office-hours` | YC Partner | Six forcing questions that reframe the product. |

---

## Project structure

```
aios-gstack/
├── aios.py              CLI entry point
├── aios_core.py         AIOS orchestrator (router + Ollama + memory)
├── aios_gstack.py       gstack Python wrapper + run_gstack()
│
├── core/
│   ├── ollama_client.py Ollama HTTP client (generate, stream, list_models)
│   ├── skills.py        gstack role definitions adapted for local execution
│   ├── router.py        Natural language → skill routing
│   └── memory.py        JSON task persistence (~/.aios-gstack/memory.json)
│
└── tests/
    └── test_core.py     20 unit tests (pure Python, no Ollama needed)
```

---

## Memory

All tasks are persisted to `~/.aios-gstack/memory.json`:

```json
{
  "tasks": [
    {
      "id": "a1b2c3d4",
      "skill": "plan-ceo-review",
      "input": "Build BharatLang NLP library",
      "output": "...",
      "model": "llama3",
      "ts_human": "2026-03-31 14:23:11"
    }
  ]
}
```

Access via Python:
```python
aios = AIOS()
history = aios.history(n=10)
for task in history:
    print(f"/{task['skill']}: {task['input'][:60]}")
```

---

## Native gstack mode (optional)

If you have Claude Code and gstack installed, AIOS can call them directly:

```python
from aios_gstack import GStackRunner

runner = GStackRunner(model="llama3", prefer_native=True)
print(runner.status())  # shows native vs direct mode

result = runner.run("/plan-ceo-review", "Build BharatLang")
```

Native mode uses Claude Code + Claude API. Direct mode uses Ollama.
Both expose the same interface.

---

## Running tests

```bash
python3 -m unittest tests/test_core.py -v
# 20 tests, no Ollama required
```

---

## What this does NOT do

- Does not modify gstack's SKILL.md files
- Does not add an Ollama provider to gstack's TypeScript codebase  
  (gstack has no TypeScript LLM provider system — it runs on Claude Code)
- Does not require gstack to be installed
- Does not require Claude Code or any Anthropic product

---

## License

MIT. Role prompt adaptations derived from [garrytan/gstack](https://github.com/garrytan/gstack) (MIT).
