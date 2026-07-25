#!/usr/bin/env node
/**
 * scr_bridge.mjs
 *
 * The ONLY file in AIOS that imports @scr-runtime/runtime directly.
 *
 * AIOS is a Python application; SCR Runtime is a TypeScript/Node package.
 * This script is a thin, one-purpose bridge between the two: it speaks
 * newline-delimited JSON over stdin/stdout so the Python side
 * (adapters/scr_adapter.py) never has to shell out, spawn Playwright,
 * or touch the filesystem/terminal itself -- that all stays inside SCR.
 *
 * Protocol (one JSON object per line, both directions):
 *   -> {"type": "run", "command": "<shell command>"}
 *   <- {"type": "result", "command": ..., "stdout": ..., "stderr": ..., "exitCode": ..., "durationMs": ...}
 *   -> {"type": "shutdown"}
 *   <- {"type": "shutdown_ack"}   (then the process exits)
 *
 * On startup this prints exactly one line: {"type": "ready", ...} or
 * {"type": "error", ...} if SCR Runtime failed to initialize.
 *
 * No logic here decides *what* command to run, or interprets results --
 * that belongs to AIOS orchestration on the Python side. This file only
 * ever calls real, existing SCR Runtime APIs (createScrRuntime,
 * createTerminalTarget) -- nothing here is simulated.
 */

import { createInterface } from 'node:readline';
import { createScrRuntime } from '@scr-runtime/runtime/runtime';
import { createTerminalTarget } from '@scr-runtime/runtime/targets/terminal';

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

async function main() {
  let runtime;
  let terminal;

  try {
    runtime = await createScrRuntime({ appName: 'aios', logLevel: 'error' });
    terminal = createTerminalTarget();
    await terminal.start();
  } catch (error) {
    send({
      type: 'error',
      phase: 'startup',
      message: error instanceof Error ? error.message : String(error),
    });
    process.exitCode = 1;
    return;
  }

  send({ type: 'ready', runtimeStatus: runtime.status, terminalStatus: terminal.status });

  const rl = createInterface({ input: process.stdin, terminal: false });

  for await (const line of rl) {
    if (!line.trim()) continue;

    let message;
    try {
      message = JSON.parse(line);
    } catch (error) {
      send({ type: 'error', phase: 'parse', message: `Invalid JSON on stdin: ${line}` });
      continue;
    }

    if (message.type === 'run') {
      try {
        const result = await terminal.run(message.command);
        send({ type: 'result', ...result });
      } catch (error) {
        send({
          type: 'error',
          phase: 'execute',
          command: message.command,
          message: error instanceof Error ? error.message : String(error),
        });
      }
      continue;
    }

    if (message.type === 'shutdown') {
      await terminal.stop();
      send({ type: 'shutdown_ack' });
      process.exit(0);
    }
  }

  // stdin closed without an explicit shutdown -- clean up anyway.
  await terminal.stop();
}

main().catch((error) => {
  send({
    type: 'error',
    phase: 'fatal',
    message: error instanceof Error ? error.message : String(error),
  });
  process.exitCode = 1;
});
