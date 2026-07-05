"""Notes, decisions, blockers, verification, status, and validation command handlers for topic-log."""

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
    TDD_EXCEPTION_CATEGORIES,
    VERIFICATION_VERDICTS,
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


def cmd_note(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    timestamp = args.timestamp or current_timestamp()
    if args.durable_topic_note:
        append_durable_topic_note(topic, "Agent Resume Notes", args.summary, timestamp, args.actor)
    append_audit(
        topic,
        event="note.recorded",
        actor=args.actor,
        phase=args.phase or "",
        artifacts=["topic.md"] if args.durable_topic_note else [],
        notes=args.summary,
        timestamp=timestamp,
        summary=args.summary,
        next_action=args.next_action or "",
        data={"durableTopicNote": args.durable_topic_note},
    )

def cmd_decision(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    timestamp = args.timestamp or current_timestamp()
    if args.durable_topic_note:
        append_durable_topic_note(topic, "Durable Decisions", args.summary, timestamp, args.actor, args.source)
    append_audit(
        topic,
        event="decision.recorded",
        actor=args.actor,
        phase=args.phase or "",
        artifacts=["topic.md"] if args.durable_topic_note else [],
        notes=args.summary,
        timestamp=timestamp,
        summary=args.summary,
        next_action=args.next_action or "",
        data={"source": args.source, "durableTopicNote": args.durable_topic_note},
    )

def cmd_blocker(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    if args.next_action:
        validate_enum("nextAction", args.next_action, NEXT_ACTIONS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="blocker.recorded",
        actor=args.actor,
        phase="blocked",
        artifacts=[],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary,
        next_action=args.next_action or "none",
        data={"id": args.id},
    )

def cmd_verification(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("verification verdict", args.verdict, VERIFICATION_VERDICTS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="verification.recorded",
        actor=args.actor,
        phase=args.phase or "",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary,
        next_action=args.next_action or "",
        data={"command": args.command, "result": args.result, "verdict": args.verdict},
    )

def cmd_status(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    validate_audit(topic)
    status = derive_status(topic)
    if args.json:
        sys.stdout.write(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
        return
    sys.stdout.write(
        "\n".join(
            [
                f"topic: {status['topic']}",
                f"status: {status['status']}",
                f"phase: {status['phase']}",
                f"nextAction: {status['nextAction']}",
            ]
        )
        + "\n"
    )

def cmd_validate(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    validate_audit(topic)
    validate_topic_invariants(topic)
    sys.stdout.write("OK\n")
