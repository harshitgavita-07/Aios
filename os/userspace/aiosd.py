"""AIOS Linux userspace daemon.

The daemon normalizes local OS and kernel-module signals into a narrow JSONL
protocol for the Python AIOS runtime. It has no third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import stat
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator

DEFAULT_SOCKET = Path("/run/aios/intent.sock")
DEFAULT_KERNEL_EVENTS = Path("/proc/aios_intent/events")


@dataclass(frozen=True)
class DeviceSignal:
    source: str
    name: str
    value: dict[str, Any]
    priority: int = 3
    timestamp: float = 0.0

    def normalized(self) -> "DeviceSignal":
        priority = min(max(int(self.priority), 1), 9)
        timestamp = self.timestamp or time.time()
        return DeviceSignal(
            source=self.source.strip() or "userspace",
            name=self.name.strip() or "unknown",
            value=dict(self.value),
            priority=priority,
            timestamp=timestamp,
        )


def parse_kernel_event(line: str) -> DeviceSignal | None:
    line = line.strip()
    if not line:
        return None

    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return DeviceSignal(
            source="kernel",
            name="raw_event",
            value={"line": line},
            priority=2,
        ).normalized()

    value = payload.get("value", {})
    if not isinstance(value, dict):
        value = {"raw": value}

    return DeviceSignal(
        source=str(payload.get("source", "kernel")),
        name=str(payload.get("name", "unknown")),
        value=value,
        priority=int(payload.get("priority", 3)),
        timestamp=float(payload.get("timestamp", 0.0) or 0.0),
    ).normalized()


def collect_userspace_snapshot() -> DeviceSignal:
    load_average = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
    return DeviceSignal(
        source="userspace",
        name="runtime_host_snapshot",
        value={
            "pid": os.getpid(),
            "load_1m": load_average[0],
            "load_5m": load_average[1],
            "load_15m": load_average[2],
        },
        priority=3,
    ).normalized()


def read_kernel_events(path: Path = DEFAULT_KERNEL_EVENTS) -> Iterator[DeviceSignal]:
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as event_file:
        for line in event_file:
            signal = parse_kernel_event(line)
            if signal is not None:
                yield signal


def encode_signal(signal: DeviceSignal) -> bytes:
    envelope = {
        "kind": "device_signal",
        **asdict(signal.normalized()),
    }
    return (json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def event_stream(kernel_events: Path = DEFAULT_KERNEL_EVENTS) -> Iterator[DeviceSignal]:
    yield collect_userspace_snapshot()
    yield from read_kernel_events(kernel_events)


def ensure_socket_directory(socket_path: Path) -> None:
    socket_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    if socket_path.exists():
        mode = socket_path.stat().st_mode
        if stat.S_ISSOCK(mode):
            socket_path.unlink()
        else:
            raise RuntimeError(f"Refusing to replace non-socket path: {socket_path}")


def serve(socket_path: Path, kernel_events: Path, poll_seconds: float) -> None:
    ensure_socket_directory(socket_path)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(socket_path))
        server.listen(8)

        while True:
            connection, _ = server.accept()
            with connection:
                for signal in event_stream(kernel_events):
                    connection.sendall(encode_signal(signal))
                time.sleep(poll_seconds)


def run_once(kernel_events: Path) -> Iterable[bytes]:
    for signal in event_stream(kernel_events):
        yield encode_signal(signal)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AIOS local signal daemon")
    parser.add_argument("--socket", type=Path, default=DEFAULT_SOCKET)
    parser.add_argument("--kernel-events", type=Path, default=DEFAULT_KERNEL_EVENTS)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--once", action="store_true", help="print one event batch")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.once:
        for encoded in run_once(args.kernel_events):
            print(encoded.decode("utf-8"), end="")
        return 0

    serve(args.socket, args.kernel_events, args.poll_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

