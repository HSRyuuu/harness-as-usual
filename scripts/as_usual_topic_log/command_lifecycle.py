"""Lifecycle and routing command handlers for topic-log."""

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
    validate_question_filename,
    validate_topic_invariants,
)


def cmd_init(args: argparse.Namespace) -> None:
    timestamp = args.timestamp or current_timestamp()
    validate_enum("actor", args.actor, ACTORS)
    runtime_host = args.host or (args.actor if args.actor in HOSTS else "")
    if runtime_host:
        validate_enum("runtime.host", runtime_host, HOSTS)
    topic = topic_dir(args.topic_dir)
    if topic_md_path(topic).exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing topic.md: {topic_md_path(topic)}")
    if audit_path(topic).exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing audit: {audit_path(topic)}")

    audit_path(topic).write_text("", encoding="utf-8")
    topic_md_path(topic).write_text(
        render_topic_md(args.topic, args.initial_request, args.summary or "", timestamp, args.actor),
        encoding="utf-8",
    )
    append_audit(
        topic,
        event="topic.created",
        actor=args.actor,
        phase="start-work",
        artifacts=["topic.md", "audit.jsonl"],
        route="",
        initial_request_ref="topic.md#Initial Request",
        notes=args.notes or "Topic created and initial request recorded in topic.md.",
        timestamp=timestamp,
        summary=args.summary or "Topic created.",
        next_action="route",
        data={
            "schemaVersion": SCHEMA_VERSION,
            "topic": args.topic,
            "initialRequest": args.initial_request,
            "runtimeHost": runtime_host,
            "sessionId": args.session_id,
        },
    )

def cmd_audit(args: argparse.Namespace) -> None:
    if args.actor:
        validate_enum("actor", args.actor, ACTORS)
    if args.phase:
        validate_enum("phase", args.phase, PHASES | set(LEGACY_PHASE_ALIASES))
    if args.route:
        validate_enum("route", args.route, ROUTES)
    if args.next_action:
        validate_enum("nextAction", args.next_action, NEXT_ACTIONS | set(LEGACY_NEXT_ACTION_ALIASES))
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event=args.event,
        actor=args.actor,
        phase=args.phase or "",
        artifacts=split_csv(args.artifacts),
        route=args.route or "",
        initial_request_ref=args.initial_request_ref or "",
        notes=args.notes or "",
        status=args.status,
        summary=args.summary or args.notes or args.event,
        next_action=args.next_action or "",
        error_kind=args.error_kind or "",
        retry_hint=args.retry_hint or "",
        stop_condition=args.stop_condition or "",
        timestamp=args.timestamp or current_timestamp(),
        data={},
    )

def cmd_artifact(args: argparse.Namespace) -> None:
    if args.actor:
        validate_enum("actor", args.actor, ACTORS)
    if args.phase:
        validate_enum("phase", args.phase, PHASES)
    if args.next_action:
        validate_enum("nextAction", args.next_action, NEXT_ACTIONS)
    if args.name not in ARTIFACT_KEYS:
        raise SystemExit(f"Unknown artifact field: {args.name}")
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="artifact.recorded",
        actor=args.actor,
        phase=args.phase or "",
        artifacts=[args.value],
        notes=args.notes or f"Recorded {args.name} artifact: {args.value}",
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Recorded {args.name} artifact.",
        next_action=args.next_action or "",
        data={"artifactName": args.name, "artifactValue": args.value, "append": args.append},
    )

def cmd_route_start_work(args: argparse.Namespace) -> None:
    validate_enum("route", args.route, ROUTES)
    validate_enum("actor", args.actor, ACTORS)
    topic = require_existing_topic_dir(args.topic_dir)
    timestamp = args.timestamp or current_timestamp()
    next_action = args.next_action or ROUTE_NEXT_ACTIONS[args.route]
    validate_enum("nextAction", next_action, NEXT_ACTIONS)
    # find-cause routes the topic out to a separate issue work unit; the topic
    # parks at routed-to-find-cause until the investigation's conclusion feeds it.
    phase = "routed-to-find-cause" if args.route == "find-cause" else "start-work"
    append_audit(
        topic,
        event="start_work.routed",
        actor=args.actor,
        phase=phase,
        artifacts=["topic.md", "audit.jsonl"],
        route=args.route,
        initial_request_ref="topic.md#Initial Request",
        notes=args.reason,
        timestamp=timestamp,
        summary=args.reason or f"Routed to {args.route}.",
        next_action=next_action,
        data={
            "skippedGates": args.skipped_gates,
            "verificationPlan": args.verification_plan,
        },
    )

def cmd_record_question(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_question_filename(args.question)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="question.created",
        actor=args.actor,
        phase="define-requirements",
        artifacts=[args.question],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Created requirements question file {args.question}.",
        next_action="answer-questions",
        data={"question": args.question},
    )

def cmd_answer_question(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_question_filename(args.question)
    if args.next_action:
        validate_enum("nextAction", args.next_action, NEXT_ACTIONS)
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="question.answered",
        actor=args.actor,
        phase="define-requirements",
        artifacts=[args.question],
        notes=args.notes,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or f"Recorded answers for {args.question}.",
        next_action=args.next_action or "answer-questions",
        data={"question": args.question, "source": args.source},
    )

def cmd_complete_requirements(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_canonical_filename("requirements", args.requirements, "requirements.md")
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="requirements.completed",
        actor=args.actor,
        phase="requirements-complete",
        artifacts=[args.requirements, "topic.md", "audit.jsonl"],
        initial_request_ref="topic.md#Initial Request",
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or "Requirements completed.",
        next_action="approve-plan",
        data={
            "inputArtifacts": ["topic.md", "audit.jsonl"],
            "outputArtifacts": [args.requirements],
        },
    )

def cmd_complete_plan(args: argparse.Namespace) -> None:
    validate_enum("actor", args.actor, ACTORS)
    validate_canonical_filename("plan", args.plan, "plan.md")
    topic = require_existing_topic_dir(args.topic_dir)
    append_audit(
        topic,
        event="plan.completed",
        actor=args.actor,
        phase="plan-review",
        artifacts=[args.plan, "topic.md", "audit.jsonl"],
        notes=args.summary,
        timestamp=args.timestamp or current_timestamp(),
        summary=args.summary or "Plan completed.",
        next_action="approve-execute",
        data={
            "inputArtifacts": ["topic.md", "audit.jsonl", "requirements.md"],
            "outputArtifacts": [args.plan],
        },
    )
