#![cfg_attr(feature = "rust-for-linux", no_std)]
#![cfg_attr(feature = "rust-for-linux", feature(allocator_api))]

//! Rust-for-Linux boundary for AIOS device and intent telemetry.
//!
//! The module is intentionally small. It should expose kernel-observed signals
//! to userspace and leave inference, orchestration, and policy decisions to the
//! Python AIOS runtime.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SignalPriority {
    Background = 1,
    Normal = 3,
    Elevated = 5,
    Critical = 7,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AiosSignal<'a> {
    pub source: &'a str,
    pub name: &'a str,
    pub value: &'a str,
    pub priority: SignalPriority,
}

impl<'a> AiosSignal<'a> {
    pub const fn resource_pressure(value: &'a str) -> Self {
        Self {
            source: "kernel",
            name: "resource_pressure",
            value,
            priority: SignalPriority::Elevated,
        }
    }

    pub const fn session_activity(value: &'a str) -> Self {
        Self {
            source: "kernel",
            name: "session_activity",
            value,
            priority: SignalPriority::Normal,
        }
    }
}

pub fn encode_jsonl(signal: &AiosSignal<'_>, output: &mut [u8]) -> Option<usize> {
    let priority = signal.priority as u8;
    let prefix = b"{\"source\":\"";
    let middle_a = b"\",\"name\":\"";
    let middle_b = b"\",\"value\":\"";
    let middle_c = b"\",\"priority\":";
    let suffix = b"}\n";

    let mut cursor = 0usize;
    cursor = copy(output, cursor, prefix)?;
    cursor = copy(output, cursor, signal.source.as_bytes())?;
    cursor = copy(output, cursor, middle_a)?;
    cursor = copy(output, cursor, signal.name.as_bytes())?;
    cursor = copy(output, cursor, middle_b)?;
    cursor = copy(output, cursor, signal.value.as_bytes())?;
    cursor = copy(output, cursor, middle_c)?;
    cursor = write_digit(output, cursor, priority)?;
    cursor = copy(output, cursor, suffix)?;
    Some(cursor)
}

fn copy(output: &mut [u8], cursor: usize, bytes: &[u8]) -> Option<usize> {
    let end = cursor.checked_add(bytes.len())?;
    if end > output.len() {
        return None;
    }
    output[cursor..end].copy_from_slice(bytes);
    Some(end)
}

fn write_digit(output: &mut [u8], cursor: usize, digit: u8) -> Option<usize> {
    if digit > 9 || cursor >= output.len() {
        return None;
    }
    output[cursor] = b'0' + digit;
    Some(cursor + 1)
}

#[cfg(feature = "rust-for-linux")]
mod kernel_module {
    use kernel::prelude::*;

    module! {
        type: AiosIntentModule,
        name: "aios_intent",
        author: "AIOS Contributors",
        description: "AIOS local telemetry boundary",
        license: "MIT",
    }

    struct AiosIntentModule;

    impl kernel::Module for AiosIntentModule {
        fn init(_module: &'static ThisModule) -> Result<Self> {
            pr_info!("aios_intent loaded\n");
            Ok(Self)
        }
    }

    impl Drop for AiosIntentModule {
        fn drop(&mut self) {
            pr_info!("aios_intent unloaded\n");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{encode_jsonl, AiosSignal};

    #[test]
    fn encodes_resource_signal() {
        let signal = AiosSignal::resource_pressure("cpu=0.42");
        let mut output = [0u8; 128];
        let len = encode_jsonl(&signal, &mut output).expect("signal should fit");
        let encoded = core::str::from_utf8(&output[..len]).expect("valid utf8");

        assert_eq!(
            encoded,
            "{\"source\":\"kernel\",\"name\":\"resource_pressure\",\"value\":\"cpu=0.42\",\"priority\":5}\n"
        );
    }
}

