"""CLI parser and entrypoint for the AsUsual record helper."""

from __future__ import annotations

import argparse
import sys

from .commands import (
    cmd_add,
    cmd_init,
    cmd_link,
    cmd_move,
    cmd_status,
    cmd_validate,
    resolve_lock_dir,
)
from .constants import (
    ACTORS,
    APPROVAL_ACTIONS,
    KINDS,
    MOVE_TARGETS,
    STATUS_CHANGE_STATES,
    STATUSES,
    UNITS,
    VERDICTS,
)
from .paths import RecordError, work_lock


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="as-usual-record",
        description="Append-only record helper for AsUsual work units (topic, direct-work, issue).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a work folder with contexts.md and audit.jsonl.")
    init.add_argument("--dir", required=True)
    init.add_argument("--unit", required=True, choices=sorted(UNITS))
    init.add_argument("--request", required=True, help="The user's initial request, verbatim.")
    init.add_argument("--actor", required=True, choices=sorted(ACTORS))
    init.set_defaults(func=cmd_init)

    add = sub.add_parser("add", help="Append one event.")
    add.add_argument("--dir", required=True)
    add.add_argument("--kind", required=True, choices=sorted(KINDS))
    add.add_argument("--summary", required=True)
    add.add_argument("--actor", default="claude", choices=sorted(ACTORS))
    add.add_argument("--status", default="success", choices=sorted(STATUSES))
    add.add_argument("--phase")
    add.add_argument("--next-action", dest="next_action")
    add.add_argument("--event", help="lifecycle event name")
    add.add_argument("--verdict", choices=sorted(VERDICTS), help="verification verdict")
    add.add_argument("--action", choices=sorted(APPROVAL_ACTIONS), help="approval action")
    add.add_argument("--target", type=int, help="status-change target seq")
    add.add_argument("--to", choices=sorted(STATUS_CHANGE_STATES), help="status-change new state")
    add.add_argument("--evidence", help="evidence for a confirmed status-change")
    add.add_argument(
        "--reason",
        help="reason for a cancelled status-change, or for finalizing on a non-PASS verdict",
    )
    add.add_argument("--resolves", type=int, help="seq of the blocker this entry resolves")
    add.add_argument("--data", action="append", metavar="KEY=VALUE")
    add.set_defaults(func=cmd_add)

    move = sub.add_parser("move", help="Relabel an unstarted work folder into another unit.")
    move.add_argument("--dir", required=True)
    move.add_argument("--to", required=True, choices=sorted(MOVE_TARGETS))
    move.add_argument("--slug", help="Rename the folder while moving.")
    move.add_argument("--actor", default="claude", choices=sorted(ACTORS))
    move.set_defaults(func=cmd_move)

    link = sub.add_parser("link", help="Link two work units in both directions.")
    link.add_argument("--dir", required=True)
    link.add_argument("--to-dir", dest="to_dir", required=True)
    link.add_argument("--summary")
    link.add_argument("--actor", default="claude", choices=sorted(ACTORS))
    link.set_defaults(func=cmd_link)

    status = sub.add_parser("status", help="Print derived state.")
    status.add_argument("--dir", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="Check record structure after the fact.")
    validate.add_argument("--dir", required=True)
    validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with work_lock(resolve_lock_dir(args)):
            return args.func(args)
    except RecordError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
