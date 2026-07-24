<div align="center">

<h1 style="font-size: 96px; margin-bottom: 0; line-height: 1;">🧠 AIOS</h1>

<sub>

### The AI-Native Operating System for People Who Are Done Babysitting Their Tools

**Stop prompting. Start delegating.**

[![Version](https://img.shields.io/badge/version-v1.0.0--beta-6366f1?style=flat-square)](https://github.com/harshitgavita-07/Aios)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-ec4899?style=flat-square)](CONTRIBUTING.md)




**[🚀 Quick Start](#-quick-start)** • **[🏗 Architecture](#-architecture)** • **[💡 Examples](#-usage-examples)** • **[🛣 Roadmap](#-roadmap)** • **[🤝 Contribute](#-contributing)**

</sub>

</div>

---

## 😤 The Problem

You don't need another chat window that "helps" you write code you then have to babysit line by line.

You need a teammate that:
- Actually **understands** what you meant, not just what you typed
- **Plans** the whole workflow instead of one shaky step at a time
- **Executes** — real files, real terminals, real git, real browsers
- **Checks its own work** before it dares tell you "done ✅"
- **Tells you when it's stuck** instead of quietly hallucinating success

That's not a chatbot. That's a **digital coworker**. That's AIOS.

---

## 🔥 What Makes AIOS Different

> **AIOS is NOT another desktop assistant.** It's the missing operating layer between "I have an idea" and "it shipped."

| Everyone else | AIOS |
|---|---|
| Generates a code snippet | Plans → executes → **verifies** → reports |
| Trusts its own output | Never claims success without independent verification |
| One-shot answers | Multi-step engineering workflows, end to end |
| You copy-paste into terminal | It runs the terminal, git, filesystem, browser — for you |
| Silent failures | Automatic retry + rollback + human approval gates |

---

## 🏗️ Architecture

```
                        Human
                          ↓
                    Bubble (UI)
                          ↓
              🧠 Coworker Engine (AIOS)
                ├── Intent Engine
                ├── Planning Engine
                ├── Verification Engine
                └── Plugin Dispatcher
                          ↓
        ⚙️  SCR Runtime (@scr-runtime/runtime)
                ├── Browser Automation
                ├── Filesystem Operations
                ├── Terminal Commands
                ├── Git / GitHub Actions
                └── Desktop Automation
                          ↓
        🔍 Desktop Studio (Debugger / Inspector)
```

**Three layers. Zero guesswork.**

1. **AIOS coordinates** — intent parsing, planning, decision-making, memory
2. **SCR Runtime executes** — every real-world action, actually performed
3. **Desktop Studio observes** — replay, metrics, timelines, execution graphs

---

## ✨ Feature Drop

### 🧭 Digital Coworker Core
- **Intent Understanding** — natural language → domain-classified action
- **Workflow Planning** — template-driven plans for real engineering tasks
- **Verification-First** — success is *proven*, not assumed
- **Recovery Strategies** — auto-retry, auto-rollback, zero drama
- **Approval Gates** — human-in-the-loop for anything high-stakes

### ⚙️ Engineering Superpowers
- 📦 **Repo Ops** — clone, branch, merge, resolve conflicts
- 🔀 **Git Workflows** — commit, push, pull, diff, tag, release
- 🧪 **Dev Loop** — test, lint, format, build, run dev server
- 📥 **Package Management** — install, update, audit, publish (npm, pip)
- 🐙 **GitHub Native** — PRs, issues, releases, changelogs, all automated
- 📝 **Docs on Autopilot** — API docs, README updates, change summaries
- 🚢 **Ship It** — build, package, deploy, verify, roll back if it breaks

### 🔌 A Real Plugin Platform
Browser automation (Playwright) · Filesystem · Terminal · Git/GitHub · Docker/Kubernetes · Email · Calendar · Slack · Notion · Linear — and it's built to grow.

---

## 📦 Quick Start

### Requirements
- Python 3.10+
- Node.js 18+ (for SCR Runtime)
- Playwright browsers

### Get running in under 60 seconds

```bash
# Clone the repository
git clone https://github.com/harshitgavita-07/Aios.git
cd Aios

# Install Python dependencies
pip install -r requirements.txt

# Install SCR Runtime
npm install @scr-runtime/runtime

# Install Playwright browsers
playwright install chromium

# Launch AIOS
python app.py
```

That's it. Welcome to your new coworker.

---

## 💡 Usage Examples

### The Basics

```python
from src import IntentEngine, PlanningEngine, VerificationEngine

# Initialize engines
intent_engine = IntentEngine()
planning_engine = PlanningEngine()
verification_engine = VerificationEngine()

# Parse user intent
intent = intent_engine.parse("Open github.com")
print(f"Domain: {intent.domain}")            # IntentDomain.BROWSER
print(f"Plugins: {intent.required_plugins}") # ['browser']

# Create execution plan
plan = planning_engine.create_plan(intent)
print(f"Steps: {len(plan.steps)}")           # 1

# Execute and verify (via SCR Runtime)
# result = await runtime.execute(plan)
# verification = verification_engine.verify(result, expected={...})
```

### Real Engineering, Fully Delegated

**"Publish SCR Runtime to npm"**
```
AIOS Plan:
1. Check Git status
2. Run npm install
3. Run npm test
4. Run npm run build
5. Publish to npm
6. Verify package is available
7. Create GitHub Release
8. Generate changelog
9. Notify user
```

**"Clone my project from GitHub"**
```
AIOS Plan:
1. Extract repository URL
2. Clone to workspace directory
3. Verify directory exists
4. Check git remote configuration
5. Report success
```

No copy-pasting. No "did it actually work?" No babysitting.

---

## 🧪 Testing

```bash
pytest tests/                          # unit tests
pytest tests/test_integration.py       # integration tests
pytest --cov=src tests/                # with coverage
```

---

## 📁 Project Structure

```
Aios/
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── src/
│   ├── shared/types.py         # Core data models
│   ├── orchestrator/
│   │   ├── intent_engine.py        # Natural language parsing
│   │   ├── planning_engine.py      # Workflow planning
│   │   └── verification_engine.py  # Result verification
│   ├── adapters/                # Runtime/browser adapters
│   ├── controllers/             # Application controllers
│   ├── services/                # Business logic services
│   ├── storage/                 # Persistence layer
│   └── ui/                      # User interface components
└── tests/                       # Test suite
```

---

## 🔌 Build Your Own Plugin

```python
from src.shared.types import PluginManifest

class MyPlugin:
    manifest = PluginManifest(
        name="my-plugin",
        version="1.0.0",
        description="My custom plugin",
        capabilities=["custom_action"],
        permissions=["filesystem"],
    )

    async def execute(self, action: str, params: dict) -> dict:
        # Implement your action logic
        return {"success": True, "data": {...}}
```

---

## 🛣️ Roadmap

**Phase 1 — v1.0.0-beta** ✅ *Shipped*
- [x] Intent Engine
- [x] Planning Engine
- [x] Verification Engine
- [x] Core type system
- [x] Workflow templates

**Phase 2 — v1.1.0** 🚧 *In progress*
- [ ] Memory & Context Engine
- [ ] Workspace & Session Manager
- [ ] Multi-Agent Coordination
- [ ] Proactive Coworker features

**Phase 3 — v1.2.0** 🔮 *Coming up*
- [ ] Plugin Marketplace
- [ ] Automation Library
- [ ] Advanced Decision Engine
- [ ] Production hardening

---

## 🤝 Contributing

Found a bug? Got an idea? Want to build a plugin? PRs are genuinely welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
pip install -r requirements-dev.txt   # dev dependencies

ruff check src/                       # lint
black --check src/                    # format check
mypy src/                             # type check
pytest                                # tests
```

---

## 🆘 Support

- 📚 **Docs** — see `/docs`
- 🐛 **Issues** — [github.com/harshitgavita-07/Aios/issues](https://github.com/harshitgavita-07/Aios/issues)
- 💬 **Discussions** — [github.com/harshitgavita-07/Aios/discussions](https://github.com/harshitgavita-07/Aios/discussions)

---

<div align="center">

### 📄 MIT Licensed

**AIOS** — *Your Desktop-Native Digital Coworker.*
**Stop prompting. Start delegating.**

⭐ **Star the repo if a verified "done" sounds better than a hopeful one.**

</div>
