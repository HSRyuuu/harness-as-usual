"""CLI parser and entrypoint for journal-log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import JournalError, init_issue


def emit(receipt: dict) -> int:
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 1


def cmd_init(args: argparse.Namespace) -> int:
    entry = init_issue(
        Path(args.issue_dir),
        initial_request=args.initial_request,
        actor=args.actor,
    )
    return emit({"ok": True, "seq": entry["seq"], "issueDir": args.issue_dir})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="journal-log")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create an issue folder, journal, and problem.md")
    init_parser.add_argument("--issue-dir", required=True)
    init_parser.add_argument("--initial-request", required=True)
    init_parser.add_argument("--actor", required=True)
    init_parser.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except JournalError as exc:
        return fail(str(exc))
