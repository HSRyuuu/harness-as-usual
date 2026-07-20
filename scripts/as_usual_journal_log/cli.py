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
    derive_status,
    ensure_open,
    find_reasoning_entry,
    init_issue,
    read_entries,
    render_markdown,
    validate_entries,
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
    ensure_open(entries)
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
    ensure_open(entries)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="approval",
        status="added",
        content=args.content,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"]})


def _status_change(
    args: argparse.Namespace, *, status: str, require_evidence: bool = False, **fields
) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    ensure_open(entries)
    find_reasoning_entry(entries, args.target)
    if require_evidence and not fields.get("evidence"):
        raise JournalError(
            "confirm requires --evidence: record reproduction evidence or an "
            "explicit 'could not reproduce because ...' judgment"
        )
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
    return _status_change(
        args, status="confirmed", require_evidence=True, evidence=args.evidence
    )


def cmd_cancel(args: argparse.Namespace) -> int:
    return _status_change(args, status="cancelled", reason=args.reason)


def cmd_status(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    return emit(derive_status(entries))


def cmd_conclude(args: argparse.Namespace) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    derived = derive_status(entries)
    if derived["issueStatus"] != "open":
        raise JournalError(f"issue already {derived['issueStatus']}")
    if args.status == "concluded" and not derived["confirmed"]:
        if not args.force_without_confirmed:
            raise JournalError(
                "no confirmed entry: confirm a hypothesis first, or pass "
                "--force-without-confirmed with --reason"
            )
        if not args.reason:
            raise JournalError("--force-without-confirmed requires --reason")
    if args.status == "concluded" and not (issue_dir / "conclusion.md").exists():
        raise JournalError(
            "conclusion.md not found: write it from templates/conclusion.md "
            "before recording closure (not required for --status cancelled)"
        )
    if args.status == "cancelled" and not args.reason:
        raise JournalError(
            "conclude --status cancelled requires --reason: record why the "
            "investigation was abandoned"
        )
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="lifecycle",
        status="added",
        event=args.status,
        content=args.summary,
        followUp=args.follow_up,
        reason=args.reason,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"], "issueStatus": args.status})


def cmd_link_follow_up(args: argparse.Namespace) -> int:
    issue_dir = Path(args.issue_dir)
    entries = read_entries(issue_dir)
    entry = build_entry(
        entries,
        actor=args.actor,
        kind="lifecycle",
        status="added",
        event="follow-up-linked",
        content=f"follow-up topic linked: {args.topic_dir}",
        followUp=args.topic_dir,
    )
    append_entry(issue_dir, entry)
    return emit({"ok": True, "seq": entry["seq"], "followUp": args.topic_dir})


def cmd_view(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    if args.md:
        print(render_markdown(entries))
        return 0
    return emit({"derived": derive_status(entries), "entries": entries})


def cmd_validate(args: argparse.Namespace) -> int:
    entries = read_entries(Path(args.issue_dir))
    problems = validate_entries(entries)
    emit({"ok": not problems, "problems": problems})
    return 1 if problems else 0


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

    status_parser = subparsers.add_parser("status", help="derive issue status from the journal")
    status_parser.add_argument("--issue-dir", required=True)
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=cmd_status)

    conclude_parser = subparsers.add_parser("conclude", help="close the issue")
    conclude_parser.add_argument("--issue-dir", required=True)
    conclude_parser.add_argument("--summary", required=True)
    conclude_parser.add_argument("--status", default="concluded", choices=["concluded", "cancelled"])
    conclude_parser.add_argument("--follow-up", dest="follow_up")
    conclude_parser.add_argument("--force-without-confirmed", action="store_true")
    conclude_parser.add_argument("--reason")
    conclude_parser.add_argument("--actor", default="claude")
    conclude_parser.set_defaults(func=cmd_conclude)

    link_follow_up_parser = subparsers.add_parser(
        "link-follow-up", help="link a follow-up coding topic to this issue"
    )
    link_follow_up_parser.add_argument("--issue-dir", required=True)
    link_follow_up_parser.add_argument("--topic-dir", required=True)
    link_follow_up_parser.add_argument("--actor", default="claude")
    link_follow_up_parser.set_defaults(func=cmd_link_follow_up)

    view_parser = subparsers.add_parser("view", help="render the journal")
    view_parser.add_argument("--issue-dir", required=True)
    view_parser.add_argument("--md", action="store_true")
    view_parser.set_defaults(func=cmd_view)

    validate_parser = subparsers.add_parser("validate", help="validate journal structure")
    validate_parser.add_argument("--issue-dir", required=True)
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except JournalError as exc:
        return fail(str(exc))
