"""Execution command handlers for topic-log."""

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


def cmd_approve_execution(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="approval.execution",
        actor=args.actor,
        phase="executing",
        artifacts=["topic.md", "audit.jsonl", "plan.md"],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or "Execution approved.",
        next_action="execute",
        data={"approvedBy": args.approved_by, "source": args.source},
    )

def cmd_approve_high_risk(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    summary = args.summary or args.description or f"Approved high-risk operation: {args.operation_id}."
    append_audit(
        topic,
        event="approval.high_risk",
        actor=args.actor,
        phase="executing",
        artifacts=split_csv(args.artifacts),
        notes=summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=summary,
        next_action="execute",
        data={
            "operationId": args.operation_id,
            "description": args.description,
            "approvedBy": args.approved_by,
            "rollback": args.rollback,
        },
    )

def cmd_complete_task(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    if args.mode not in TASK_COMPLETION_MODES:
        allowed = ", ".join(sorted(TASK_COMPLETION_MODES))
        raise SystemExit(f"Unsupported task mode: {args.mode or '<empty>'}. Allowed modes: {allowed}")
    if args.mode == "test-required":
        if not args.test_target:
            raise SystemExit("test-required task requires a test target.")
        if not args.green_evidence:
            raise SystemExit("test-required task requires passing-test evidence (--green-evidence).")
        # Regression RED evidence (--red-evidence) is required for bug fixes only;
        # that requirement is enforced by the plan and review, not this gate.
    if args.mode == "no-test":
        if not args.no_test_reason:
            raise SystemExit("no-test task requires a recorded reason (--no-test-reason).")
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="task.completed",
        actor=args.actor,
        phase="executing",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Completed task: {args.task}.",
        next_action="execute",
        data={
            "task": args.task,
            "verification": args.verification,
            "mode": args.mode,
            "testTarget": args.test_target,
            "redEvidence": args.red_evidence,
            "greenEvidence": args.green_evidence,
            "expectedResult": args.expected_result,
            "result": args.result,
            "noTestReason": args.no_test_reason,
            "artifacts": split_csv(args.artifacts),
        },
    )

def cmd_complete_execution(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    status = derive_status(topic)
    if status.get("taskFindings"):
        finding_ids = ", ".join(finding["id"] for finding in status["taskFindings"])
        raise SystemExit(f"Cannot complete execution with unresolved task findings: {finding_ids}")
    append_audit(
        topic,
        event="execution.completed",
        actor=args.actor,
        phase="execution-complete",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or "Execution completed.",
        next_action="review-execution",
        data={"verification": args.verification, "result": args.result},
    )

def cmd_dispatch_task(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("execution mode", args.mode, EXECUTION_MODES)
    validate_enum("task role", args.role, TASK_ROLES)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="task.dispatched",
        actor=args.actor,
        phase="executing",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Dispatched {args.role} for {args.task}.",
        next_action="execute",
        data={
            "task": args.task,
            "mode": args.mode,
            "role": args.role,
            "context": split_csv(args.context),
            "artifacts": split_csv(args.artifacts),
        },
    )

def cmd_record_task_review(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("task review type", args.review_type, TASK_REVIEW_TYPES)
    validate_enum("task review status", args.status, REVIEW_STATUSES)
    finding_ids = split_csv(args.finding_ids)
    finding_count = args.critical + args.important + args.minor
    if args.status in {"findings", "blocked"} and finding_count > 0 and not finding_ids:
        raise SystemExit("Task review findings require finding ids via --finding-ids.")
    topic = require_existing_topic_dir(args.topic_dir)
    next_action = "execute" if args.status == "passed" else "address-review-findings"
    append_audit(
        topic,
        event="task.review_completed",
        actor=args.actor,
        phase="executing",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"{args.review_type} review {args.status} for {args.task}.",
        next_action=next_action,
        data={
            "task": args.task,
            "reviewType": args.review_type,
            "status": args.status,
            "critical": args.critical,
            "important": args.important,
            "minor": args.minor,
            "findingIds": finding_ids,
            "artifacts": split_csv(args.artifacts),
        },
    )

def cmd_record_task_fix(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("task fix status", args.status, TASK_FIX_STATUSES)
    topic = require_existing_topic_dir(args.topic_dir)
    event = "task.fix_completed" if args.status == "completed" else "task.fix_requested"
    append_audit(
        topic,
        event=event,
        actor=args.actor,
        phase="executing",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Task fix {args.status}: {args.finding_id}.",
        next_action="execute",
        data={
            "task": args.task,
            "findingId": args.finding_id,
            "status": args.status,
            "artifacts": split_csv(args.artifacts),
        },
    )

def cmd_record_task_commit(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="task.commit_recorded",
        actor=args.actor,
        phase="executing",
        artifacts=[],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Recorded commit for {args.task}: {args.sha}.",
        next_action="execute",
        data={"task": args.task, "sha": args.sha},
    )

def cmd_record_sweep(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_enum("sweep kind", args.kind, SWEEP_KINDS)
    validate_enum("audit status", args.status, AUDIT_STATUSES)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="sweep.completed",
        actor=args.actor,
        phase=args.phase or "executing",
        artifacts=split_csv(args.artifacts),
        notes=args.summary,
        status=args.status,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"{args.kind} sweep completed.",
        next_action=args.next_action or "execute",
        data={
            "kind": args.kind,
            "command": args.command,
            "result": args.result,
            "artifacts": split_csv(args.artifacts),
        },
    )
