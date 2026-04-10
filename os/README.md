# AIOS OS Substrate

This directory contains the Linux-side scaffolding for AIOS as an AI-native
operating environment.

## Contents

- `rust-kernel-modules/aios-intent/` - Rust-for-Linux kernel module scaffold
  that publishes AIOS device and intent telemetry.
- `userspace/aiosd.py` - local daemon that normalizes kernel/userland signals
  and serves JSONL events to the Python AI runtime over a Unix domain socket.

## Design Rules

- Keep model inference and natural-language parsing in userspace.
- Keep kernel modules small, deterministic, and telemetry-focused.
- Prefer explicit JSON contracts between layers.
- Default to offline, local-only behavior.
- Treat privileged actions as policy decisions in userspace, not kernel logic.

## Development Notes

The Rust module targets Rust-for-Linux infrastructure and is not expected to
compile against a stock Python development environment. Build it inside a Linux
kernel tree with Rust support enabled.

The userspace daemon has no third-party Python dependencies and can be tested on
ordinary Linux hosts. On non-Linux systems it can still run in `--once` mode for
contract validation, but it will not create the default Unix socket.

