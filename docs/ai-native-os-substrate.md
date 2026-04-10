# AIOS Linux Substrate

AIOS is organized as a Linux-based AI-native operating environment. The Python
runtime remains the agent, workflow, memory, and LLM layer. The Linux substrate
adds a small, auditable boundary for device signals, resource pressure, and
intent events that need OS-level visibility.

## Goals

- Keep all AI execution on-device by default.
- Expose OS signals through a narrow local protocol instead of ad hoc shell
  scraping.
- Let Rust kernel modules publish safe telemetry and intent events without
  running model logic in kernel space.
- Keep the Python AI/ML runtime responsible for planning, local LLM calls,
  tool execution, and multi-agent orchestration.

## Layer Model

```text
AIOS Workspace
  PySide UI, agent widgets, workflow panels, intent input

Python AI/ML Runtime
  agent mesh, workflow engine, memory, RAG, local LLM backends

AIOS Userspace Daemon
  local Unix socket protocol, device-signal normalization, policy checks

Linux Substrate
  Rust kernel modules, procfs/debugfs exports, cgroup/system telemetry
```

## Kernel Boundary

Kernel modules must not run LLM inference, parse untrusted natural language, or
perform network I/O. Their job is to expose small structured events:

- resource pressure snapshots
- foreground task hints
- input/session activity signals
- model-device availability hints
- power and thermal state changes

The userspace daemon converts those events into JSON messages for the Python
runtime.

## Local Protocol

The daemon owns a Unix domain socket at `/run/aios/intent.sock` by default. Each
message is one JSON object followed by a newline.

```json
{"kind":"device_signal","source":"kernel","name":"resource_pressure","value":{"cpu":0.42},"priority":4}
```

All messages are local-only. Remote control surfaces must be added through a
separate authenticated API; this protocol intentionally does not expose one.

## First Production Milestones

1. Build and load the Rust telemetry module on a Rust-for-Linux kernel tree.
2. Run `os/userspace/aiosd.py --once` to validate event normalization without a
   loaded module.
3. Connect the Python runtime to the daemon socket and feed device signals into
   the existing context engine.
4. Add policy gates for privileged actions before agents can request OS-level
   changes.
5. Package the substrate as an optional Linux profile so the desktop assistant
   still runs on non-Linux developer machines.

