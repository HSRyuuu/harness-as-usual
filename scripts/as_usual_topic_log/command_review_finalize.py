"""Review, cleanup, finalize, and git action command handlers for topic-log."""

from __future__ import annotations

import argparse
import json
import sys

from .audit import append_audit, current_timestamp
from .constants import (
    ACTORS,
    ARTIFACT_KEYS,
    AUDIT_STATUSES,
    EXECUTION_MODES,
    GIT_ACTIONS,
    HOSTS,
    LEGACY_NEXT_ACTION_ALIASES,
    LEGACY_PHASE_ALIASES,
    NEXT_ACTIONS,
    PHASES,
    REVIEW_MODES,
    REVIEW_STATUSES,
    ROUTE_NEXT_ACTIONS,
    ROUTES,
    SCHEMA_VERSION,
    STATUSES,
    SWEEP_KINDS,
    TASK_COMPLETION_MODES,
    TASK_FIX_STATUSES,
    TASK_REVIEW_TYPES,
    TASK_ROLES,
)
from .paths import audit_path, require_existing_topic_dir, topic_dir, topic_md_path
from .status import derive_status
from .topic_md import append_durable_topic_note, render_topic_md
from .utils import split_csv
from .validation import (
    validate_audit,
    validate_canonical_filename,
    validate_enum,
    validate_topic_invariants,
)


def cmd_record_review(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("review mode", args.mode, REVIEW_MODES)
    validate_enum("review status", args.status, REVIEW_STATUSES)
    if args.report:
        validate_canonical_filename("codeReviewReport", args.report, "code-review-report.md")
    topic = require_existing_topic_dir(args.topic_dir)
    phase = "review-complete" if args.status == "passed" else "review-fixes-needed"
    next_action = "decide-code-cleanup" if args.status == "passed" else "address-review-findings"
    artifacts = [args.report] if args.report else []
    append_audit(
        topic,
        event="review.completed",
        actor=args.actor,
        phase=phase,
        artifacts=artifacts,
        notes=args.reason,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.reason or f"Review {args.status}.",
        next_action=next_action,
        data={
            "mode": args.mode,
            "status": args.status,
            "critical": args.critical,
            "important": args.important,
            "minor": args.minor,
            "reason": args.reason,
            "report": args.report,
        },
    )

def cmd_skip_code_cleanup(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="code_cleanup.skipped",
        actor=args.actor,
        phase="review-complete",
        artifacts=[],
        notes=args.reason,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.reason or "Code cleanup skipped.",
        next_action="finalize",
        data={"reason": args.reason},
    )

def cmd_finalize_topic(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("topic status", args.status, STATUSES)
    if args.report:
        validate_canonical_filename("report", args.report, "report.md")
    topic = require_existing_topic_dir(args.topic_dir)
    data = {"status": args.status, "report": args.report}
    if args.status == "cancelled":
        data["cancellationReason"] = args.summary
    append_audit(
        topic,
        event="topic.finalized",
        actor=args.actor,
        phase="finalized",
        artifacts=[args.report] if args.report else [],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or "Topic finalized.",
        next_action="git-action-decision",
        data=data,
    )

def cmd_select_git_action(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("git action", args.action, GIT_ACTIONS)
    topic = require_existing_topic_dir(args.topic_dir)
    phase = "git-action-complete" if args.action == "none" else "git-action"
    next_action = "none" if args.action == "none" else "git-action"
    append_audit(
        topic,
        event="git_action.selected",
        actor=args.actor,
        phase=phase,
        artifacts=[],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Selected git action: {args.action}.",
        next_action=next_action,
        data={"action": args.action},
    )
