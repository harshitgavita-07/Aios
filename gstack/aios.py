#!/usr/bin/env python3
"""AIOS command-line interface for local gstack skills."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

<<<<<<< HEAD
from gstack.aios_core import AIOS
=======
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gstack.aios_core import AIOS
from gstack.core.skills import SKILLS
>>>>>>> 76f6944 (Ground AIOS as a local-first operating runtime)


def main():
    parser = argparse.ArgumentParser(
        prog="aios",
        description="AIOS - local AI operating system powered by Ollama and gstack skills",
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Skill command (/plan-ceo-review) or natural language task",
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task description when using an explicit command",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="llama3",
        help="Ollama model to use (default: llama3)",
    )
    parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Stream output tokens as they arrive",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show recent task history",
    )
    parser.add_argument(
        "--list-skills",
        action="store_true",
        help="List available gstack skills",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")

    if args.status:
        try:
            aios = AIOS(model=args.model)
            status = aios.status()
        except RuntimeError as e:
            print(f"[FAIL] {e}", file=sys.stderr)
            sys.exit(1)

        print("\n== AIOS Status ==")
        print(f"  Ollama running:   {status['ollama_running']}")
        print(f"  Current model:    {status['current_model']}")
        print(f"  Model available:  {status['model_available']}")
        print(f"  Installed models: {', '.join(status['installed_models']) or 'none'}")
        print(f"  Available skills: {len(status['available_skills'])}")
        print(f"  Tasks completed:  {status['task_count']}")
        return

    if args.history:
        try:
            aios = AIOS(model=args.model)
            tasks = aios.history(n=10)
        except RuntimeError as e:
            print(f"[FAIL] {e}", file=sys.stderr)
            sys.exit(1)

        if not tasks:
            print("No tasks in history yet.")
            return

        print("\n== Recent Tasks ==")
        for task in tasks:
            print(f"  [{task['ts_human']}] /{task['skill']} - {task['input'][:60]}...")
        return

    if args.list_skills:
<<<<<<< HEAD
        from gstack.core.skills import SKILLS
        print("\n── Available gstack Skills ────────────────────")
=======
        print("\n== Available gstack Skills ==")
>>>>>>> 76f6944 (Ground AIOS as a local-first operating runtime)
        for name, skill in sorted(SKILLS.items()):
            print(f"  /{name:25}  {skill.role}: {skill.description}")
        return

    if not args.command:
        parser.print_help()
        return

    try:
        aios = AIOS(model=args.model)
    except RuntimeError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(1)

    result = aios.run(
        args.command,
        task=args.task,
        stream=args.stream,
    )

    if not args.stream:
        print(f"\n== [{result.role}] ==")
        print(result.output)
        print(f"\nTask ID: {result.task_id} | Skill: /{result.skill} | Model: {result.model}")

    if not result.success:
        print(f"\n[FAIL] Error: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
