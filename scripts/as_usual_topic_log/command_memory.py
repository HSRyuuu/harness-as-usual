"""Memory and skill command handlers for topic-log."""

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


def cmd_record_memory_candidate(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="memory.candidate",
        actor=args.actor,
        summary=args.summary,
        status="success",
        data={
            "sourcePhase": args.source_phase or None,
            "proposedTarget": args.proposed_target or "undecided",
        },
    )

def cmd_record_memory(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    files = split_csv(args.files) if args.files else []
    append_audit(
        topic,
        event="memory.recorded",
        actor=args.actor,
        summary=args.summary,
        status="success",
        data={"memoryFiles": files},
    )

def cmd_record_skill(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    event = "skill.created" if args.state == "created" else "skill.candidate"
    append_audit(
        topic,
        event=event,
        actor=args.actor,
        summary=args.summary,
        status="success",
        data={
            "kind": args.kind,
            "patchTarget": args.patch_target or None,
            "dest": args.dest or None,
            "rationale": args.rationale or None,
            "brief": args.brief or None,
        },
    )
