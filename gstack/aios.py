#!/usr/bin/env python3
"""
aios.py — AIOS command-line interface

Usage:
    python aios.py "build a NLP library for Hindi"
    python aios.py /plan-ceo-review "build BharatLang"
    python aios.py /review "check the auth module"
    python aios.py /ship "pre-ship checklist for v1.0"
    python aios.py --status
    python aios.py --history
    python aios.py --list-skills
"""

from __future__ import annotations

import argparse
import sys
import logging

from aios_core import AIOS


def main():
    parser = argparse.ArgumentParser(
        prog="aios",
        description="AIOS — Local AI Operating System powered by Ollama + gstack skills",
    )
    parser.add_argument(
        "command",
        nargs="?",
        help="Skill command (/plan-ceo-review) or natural language task",
    )
    parser.add_argument(
        "task",
        nargs="?",
        help="Task description (when using explicit command)",
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3",
        help="Ollama model to use (default: llama3)",
    )
    parser.add_argument(
        "--stream", "-s",
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
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s %(levelname)s %(message)s")

    # ── Status ──────────────────────────────────────────────────────────
    if args.status:
        try:
            aios = AIOS(model=args.model)
            status = aios.status()
            print("\n── AIOS Status ────────────────────────────────")
            print(f"  Ollama running:   {status['ollama_running']}")
            print(f"  Current model:    {status['current_model']}")
            print(f"  Model available:  {status['model_available']}")
            print(f"  Installed models: {', '.join(status['installed_models']) or 'none'}")
            print(f"  Available skills: {len(status['available_skills'])}")
            print(f"  Tasks completed:  {status['task_count']}")
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ── History ─────────────────────────────────────────────────────────
    if args.history:
        try:
            aios = AIOS(model=args.model)
            tasks = aios.history(n=10)
            if not tasks:
                print("No tasks in history yet.")
                return
            print("\n── Recent Tasks ───────────────────────────────")
            for t in tasks:
                print(f"  [{t['ts_human']}] /{t['skill']} — {t['input'][:60]}...")
        except RuntimeError as e:
            print(f"❌ {e}", file=sys.stderr)
            sys.exit(1)
        return

    # ── List skills ──────────────────────────────────────────────────────
    if args.list_skills:
        from core.skills import SKILLS
        print("\n── Available gstack Skills ────────────────────")
        for name, skill in sorted(SKILLS.items()):
            print(f"  /{name:25}  {skill.role}: {skill.description}")
        return

    # ── Run task ─────────────────────────────────────────────────────────
    if not args.command:
        parser.print_help()
        return

    try:
        aios = AIOS(model=args.model)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    result = aios.run(
        args.command,
        task=args.task,
        stream=args.stream,
    )

    if not args.stream:
        # Print result
        print(f"\n── [{result.role}] ─────────────────────────────────")
        print(result.output)
        print(f"\n── Task ID: {result.task_id} | Skill: /{result.skill} | Model: {result.model}")

    if not result.success:
        print(f"\n❌ Error: {result.error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
