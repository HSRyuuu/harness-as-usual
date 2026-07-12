"""CLI parser and entrypoint for journal-log."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import (
    REASONING_KINDS,
    JournalError,
    append_entry,
    build_entry,
    find_reasoning_entry,
    init_issue,
    read_entries,
)


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


def cmd_add(args: argparse.Namespace) -> int:
    if args.kind not in REASONING_KINDS:
        raise JournalError(
            f"invalid kind: {args.kind} (allowed: {sorted(REASONING_KINDS)})"
        )
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind=args.kind,
        status="added",
        content=args.content,
        evidence=args.evidence,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"]})


def cmd_approve(args: argparse.Namespace) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="approval",
        status="added",
        content=args.content,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"]})


def _status_change(args: argparse.Namespace, *, status: str, **fields) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    find_reasoning_entry(entries, args.target)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="status-change",
        status=status,
        target=args.target,
        **fields,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"], "target": args.target, "status": status})


def cmd_confirm(args: argparse.Namespace) -> int:
    return _status_change(args, status="confirmed", evidence=args.evidence)


def cmd_cancel(args: argparse.Namespace) -> int:
    return _status_change(args, status="cancelled", reason=args.reason)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="journal-log")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create an issue folder, journal, and problem.md")
    init_parser.add_argument("--issue-dir", required=True)
    init_parser.add_argument("--initial-request", required=True)
    init_parser.add_argument("--actor", required=True)
    init_parser.set_defaults(func=cmd_init)

    add_parser = subparsers.add_parser("add", help="append a reasoning entry")
    add_parser.add_argument("--issue-dir", required=True)
    add_parser.add_argument("--kind", required=True)
    add_parser.add_argument("--content", required=True)
    add_parser.add_argument("--evidence")
    add_parser.add_argument("--actor", default="claude")
    add_parser.set_defaults(func=cmd_add)

    approve_parser = subparsers.add_parser("approve", help="record a user approval")
    approve_parser.add_argument("--issue-dir", required=True)
    approve_parser.add_argument("--content", required=True)
    approve_parser.add_argument("--actor", default="user")
    approve_parser.set_defaults(func=cmd_approve)

    confirm_parser = subparsers.add_parser("confirm", help="mark an entry confirmed")
    confirm_parser.add_argument("--issue-dir", required=True)
    confirm_parser.add_argument("--target", required=True, type=int)
    confirm_parser.add_argument("--evidence")
    confirm_parser.add_argument("--actor", default="claude")
    confirm_parser.set_defaults(func=cmd_confirm)

    cancel_parser = subparsers.add_parser("cancel", help="mark an entry cancelled")
    cancel_parser.add_argument("--issue-dir", required=True)
    cancel_parser.add_argument("--target", required=True, type=int)
    cancel_parser.add_argument("--reason", required=True)
    cancel_parser.add_argument("--actor", default="claude")
    cancel_parser.set_defaults(func=cmd_cancel)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except JournalError as exc:
        return fail(str(exc))
