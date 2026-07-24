# AIOS

**Version:** v1.0.0-beta

AIOS (AI Native Operating System) is a **desktop-native digital coworker** that understands your intent, plans work, delegates execution, verifies results, and collaborates naturally with humans.

## 🚀 Vision

AIOS is NOT another chatbot or desktop assistant. It's a trusted engineering teammate that:

- **Understands** your goals in natural language
- **Plans** complex multi-step workflows
- **Delegates** execution to specialized plugins via SCR Runtime
- **Verifies** every action independently before reporting success
- **Collaborates** with clear communication and recovery suggestions

## 🏗️ Architecture

```
Human
  ↓
Bubble (UI)
  ↓
Coworker Engine (AIOS)
  ├── Intent Engine
  ├── Planning Engine
  ├── Verification Engine
  └── Plugin Dispatcher
      ↓
SCR Runtime (@scr-runtime/runtime)
  ├── Browser Automation
  ├── Filesystem Operations
  ├── Terminal Commands
  ├── Git/GitHub Actions
  └── Desktop Automation
      ↓
Desktop Studio (Debugger/Inspector)
```

### Key Principles

1. **AIOS coordinates** - Intent parsing, planning, decision making, memory management
2. **SCR Runtime executes** - All actual browser, filesystem, terminal, and desktop operations
3. **Desktop Studio observes** - Replay, metrics, timeline, execution graphs, developer tools

## ✨ Features

### Digital Coworker Capabilities

- **Intent Understanding**: Natural language parsing with domain classification
- **Workflow Planning**: Template-based planning for common engineering tasks
- **Verification-First**: Never claims success without independent verification
- **Recovery Strategies**: Automatic retry and rollback on failures
- **Approval System**: Human-in-the-loop for high-risk operations

### Engineering Workflows

- **Repository Operations**: Clone, branch, merge, resolve conflicts
- **Git Workflows**: Commit, push, pull, diff, tag, release
- **Development**: Run tests, linting, formatting, build, dev server
- **Package Management**: Install, update, audit, publish (npm, pip)
- **GitHub Integration**: PRs, issues, releases, changelog generation
- **Documentation**: Generate API docs, update READMEs, summarize changes
- **Deployment**: Build, package, deploy, verify, rollback

### Plugin Platform

Extensible architecture supporting:
- Browser automation (Playwright)
- Filesystem operations
- Terminal commands
- Git/GitHub actions
- Docker/Kubernetes
- Email, Calendar, Slack, Notion, Linear integrations

## 📦 Installation

### Requirements

- Python 3.10+
- Node.js 18+ (for SCR Runtime)
- Playwright browsers

### Quick Start

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

# Run AIOS
python app.py
```

## 💡 Usage Examples

### Basic Tasks

```python
from src import IntentEngine, PlanningEngine, VerificationEngine

# Initialize engines
intent_engine = IntentEngine()
planning_engine = PlanningEngine()
verification_engine = VerificationEngine()

# Parse user intent
intent = intent_engine.parse("Open github.com")
print(f"Domain: {intent.domain}")  # IntentDomain.BROWSER
print(f"Plugins: {intent.required_plugins}")  # ['browser']

# Create execution plan
plan = planning_engine.create_plan(intent)
print(f"Steps: {len(plan.steps)}")  # 1

# Execute and verify (via SCR Runtime)
# result = await runtime.execute(plan)
# verification = verification_engine.verify(result, expected={...})
```

### Engineering Workflows

**Publish npm Package:**
```
User: "Publish SCR Runtime to npm"

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

**Clone Repository:**
```
User: "Clone my project from GitHub"

AIOS Plan:
1. Extract repository URL
2. Clone to workspace directory
3. Verify directory exists
4. Check git remote configuration
5. Report success
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src tests/
```

## 📁 Project Structure

```
Aios/
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── src/
│   ├── __init__.py            # Package exports
│   ├── shared/
│   │   ├── __init__.py
│   │   └── types.py           # Core data models
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── intent_engine.py   # Natural language parsing
│   │   ├── planning_engine.py # Workflow planning
│   │   └── verification_engine.py  # Result verification
│   ├── adapters/              # Runtime/browser adapters
│   ├── controllers/           # Application controllers
│   ├── services/              # Business logic services
│   ├── storage/               # Persistence layer
│   └── ui/                    # User interface components
└── tests/                     # Test suite
```

## 🔌 Plugin Development

Create a new plugin by implementing the plugin interface:

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

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run linters
ruff check src/
black --check src/

# Run type checking
mypy src/

# Run tests
pytest
```

## 📄 License

MIT License - see LICENSE file for details.

## 🛣️ Roadmap

### Phase 1 (v1.0.0-beta) ✅
- [x] Intent Engine
- [x] Planning Engine
- [x] Verification Engine
- [x] Core type system
- [x] Workflow templates

### Phase 2 (v1.1.0)
- [ ] Memory & Context Engine
- [ ] Workspace & Session Manager
- [ ] Multi-Agent Coordination
- [ ] Proactive Coworker features

### Phase 3 (v1.2.0)
- [ ] Plugin Marketplace
- [ ] Automation Library
- [ ] Advanced Decision Engine
- [ ] Production hardening

## 🆘 Support

- **Documentation**: See `/docs` folder
- **Issues**: https://github.com/harshitgavita-07/Aios/issues
- **Discussions**: https://github.com/harshitgavita-07/Aios/discussions

---

**AIOS** - Your Desktop-Native Digital Coworker
