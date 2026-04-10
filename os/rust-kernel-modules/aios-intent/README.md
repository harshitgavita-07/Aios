# aios-intent

`aios-intent` is the Rust-for-Linux kernel module boundary for AIOS. It is a
telemetry and event source only; it does not run LLMs or execute agent plans.

## Responsibilities

- expose resource and session signals to userspace
- keep event payloads small and structured
- fail closed when kernel facilities are unavailable
- avoid policy decisions that belong to the AIOS userspace daemon

## Build Target

This crate is designed for a Linux kernel tree with Rust support enabled. The
`kernel` crate path in `Cargo.toml` is a placeholder for in-tree Rust-for-Linux
builds and should be adjusted by the kernel build system.

## Userspace Contract

The module should publish line-oriented events under a kernel-owned interface
such as procfs/debugfs:

```json
{"source":"kernel","name":"resource_pressure","value":{"cpu":0.37},"priority":4}
```

`os/userspace/aiosd.py` consumes and normalizes those events before forwarding
them to the Python runtime.

