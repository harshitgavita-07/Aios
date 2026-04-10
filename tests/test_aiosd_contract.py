import importlib.util
import json
import sys
from pathlib import Path


def load_aiosd():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "os" / "userspace" / "aiosd.py"
    spec = importlib.util.spec_from_file_location("aiosd", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_kernel_event_normalizes_json_payload():
    aiosd = load_aiosd()

    signal = aiosd.parse_kernel_event(
        '{"source":"kernel","name":"resource_pressure","value":{"cpu":0.5},"priority":99}'
    )

    assert signal.source == "kernel"
    assert signal.name == "resource_pressure"
    assert signal.value == {"cpu": 0.5}
    assert signal.priority == 9
    assert signal.timestamp > 0


def test_parse_kernel_event_preserves_unstructured_lines():
    aiosd = load_aiosd()

    signal = aiosd.parse_kernel_event("thermal-throttle")

    assert signal.source == "kernel"
    assert signal.name == "raw_event"
    assert signal.value == {"line": "thermal-throttle"}


def test_encode_signal_uses_jsonl_device_signal_envelope():
    aiosd = load_aiosd()
    signal = aiosd.DeviceSignal(
        source="userspace",
        name="runtime_host_snapshot",
        value={"pid": 7},
        priority=3,
        timestamp=1.0,
    )

    payload = json.loads(aiosd.encode_signal(signal).decode("utf-8"))

    assert payload["kind"] == "device_signal"
    assert payload["source"] == "userspace"
    assert payload["name"] == "runtime_host_snapshot"
    assert payload["value"] == {"pid": 7}
