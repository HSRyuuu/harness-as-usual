#!/usr/bin/env python3
"""Manage AsUsual topic.md and audit.jsonl.

AsUsual runtime state is audit-first. This helper appends structured
audit.jsonl events, derives current status from those events, and writes
low-churn topic.md resume context only when durable context changes.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as _dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = "as-usual.audit.v1"

STATUSES = {"active", "blocked", "complete", "follow-up-needed", "cancelled"}

PHASES = {
    "start-work",
    "define-requirements",
    "requirements-complete",
    "writing-plan",
    "plan-review",
    "executing",
    "execution-complete",
    "review-execution",
    "review-complete",
    "review-fixes-needed",
    "cleanup-code",
    "cleanup-complete",
    "finalized",
    "git-action",
    "git-action-complete",
    "direct-execute-complete",
    "blocked",
}

LEGACY_PHASE_ALIASES = {
    "simplify-execution": "cleanup-code",
    "simplify-complete": "cleanup-complete",
}

NEXT_ACTIONS = {
    "",
    "route",
    "answer-questions",
    "write-requirements",
    "approve-plan",
    "write-plan",
    "approve-execute",
    "execute",
    "review-execution",
    "address-review-findings",
    "decide-code-cleanup",
    "cleanup-code",
    "finalize",
    "git-action-decision",
    "git-action",
    "none",
}

LEGACY_NEXT_ACTION_ALIASES = {
    "decide-simplify": "decide-code-cleanup",
    "simplify-execution": "cleanup-code",
}

CODE_CLEANUP_DECISION_EVENTS = {
    "code_cleanup.skipped",
    "code_cleanup.completed",
    "simplify.skipped",
    "simplify.completed",
}

ACTORS = {"codex", "claude", "user", "system"}
HOSTS = {"codex", "claude"}
REVIEW_MODES = {"independent", "self", "local-prompt"}
REVIEW_STATUSES = {"passed", "findings", "blocked"}
AUDIT_STATUSES = {"success", "warning", "error"}
GIT_ACTIONS = {"none", "commit", "commit + push", "commit + push + PR"}
ROUTES = {"requirements", "plan", "execute", "direct-execute"}
EXECUTION_MODES = {"inline", "subagent-driven", "mixed"}
TASK_REVIEW_TYPES = {"requirements", "quality"}
TASK_ROLES = {"implementer", "requirements-reviewer", "quality-reviewer", "controller"}
TASK_FIX_STATUSES = {"requested", "completed"}
SWEEP_KINDS = {"final", "stale-reference", "mirror", "verification", "custom"}
TASK_COMPLETION_MODES = {"tdd", "approved-tdd-exception"}
TDD_EXCEPTION_CATEGORIES = {"throwaway-prototype", "generated-code", "configuration"}
ROUTE_NEXT_ACTIONS = {
    "requirements": "answer-questions",
    "plan": "write-plan",
    "execute": "execute",
    "direct-execute": "execute",
}
ARTIFACT_KEYS = {"question", "requirements", "plan", "codeReviewReport", "report", "audit", "topic"}
ARTIFACT_FIELD_BY_FILE = {
    "requirements.md": "requirements",
    "plan.md": "plan",
    "code-review-report.md": "codeReviewReport",
    "report.md": "report",
    "topic.md": "topic",
    "audit.jsonl": "audit",
}

JsonObject = dict[str, Any]


def current_timestamp() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


def topic_dir(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_topic_dir(value: str) -> Path:
    return Path(value).expanduser().resolve()


def require_existing_topic_dir(value: str) -> Path:
    topic = resolve_topic_dir(value)
    if not topic_md_path(topic).exists():
        raise SystemExit(f"Missing required file: {topic_md_path(topic)}")
    if not audit_path(topic).exists():
        raise SystemExit(f"Missing required file: {audit_path(topic)}")
    return topic


def topic_md_path(topic: Path) -> Path:
    return topic / "topic.md"


def audit_path(topic: Path) -> Path:
    return topic / "audit.jsonl"


@contextmanager
def topic_lock(topic: Path):
    digest = hashlib.sha256(str(topic).encode("utf-8")).hexdigest()
    lock_path = Path(tempfile.gettempdir()) / f"as-usual-topic-log-{digest}.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_enum(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise SystemExit(f"Invalid {name}: {value}. Allowed values: {allowed_values}")


def validate_canonical_filename(name: str, value: str, expected: str) -> None:
    if value != expected:
        raise SystemExit(f"Invalid {name}: {value}. {name} must be {expected}")


def render_topic_md(topic_name: str, initial_request: str, summary: str, timestamp: str, actor: str) -> str:
    boundary = summary or "Not narrowed beyond the initial request yet."
    return (
        "# Topic\n\n"
        "## Initial Request\n\n"
        f"{initial_request or 'Not recorded.'}\n\n"
        "## Topic Boundary\n\n"
        f"{boundary}\n\n"
        "## Agent Resume Notes\n\n"
        "- Read `topic.md` first for durable context.\n"
        "- Use `audit.jsonl` and `scripts/topic-log.py status --json` for current phase, next action, and evidence.\n\n"
        "## Durable Decisions\n\n"
        "- None recorded yet.\n\n"
        "## Constraints\n\n"
        "- Do not treat this file as a progress ledger.\n"
        "- Record high-churn progress and verification in `audit.jsonl` through `scripts/topic-log.py`.\n\n"
        "## Artifact Index\n\n"
        "- `topic.md`: low-churn agent resume context.\n"
        "- `audit.jsonl`: canonical append-only event history.\n"
        "- `question-cN.md`: durable requirements question cycles when needed.\n"
        "- `requirements.md`: approved requirements definition.\n"
        "- `plan.md`: approved execution plan.\n"
        "- `code-review-report.md`: execution review findings when present.\n"
        "- `report.md`: final user-facing handoff summary.\n\n"
        "## Created\n\n"
        f"- Topic: `{topic_name}`\n"
        f"- Actor: `{actor}`\n"
        f"- Timestamp: `{timestamp}`\n"
    )


def next_audit_seq(topic: Path) -> int:
    path = audit_path(topic)
    if not path.exists():
        return 1
    last_seq = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            seq = entry.get("seq")
            if isinstance(seq, int):
                last_seq = max(last_seq, seq)
    return last_seq + 1


def require_invariant(condition: Any, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def append_audit(
    topic: Path,
    *,
    event: str,
    actor: str,
    phase: str = "",
    artifacts: list[str] | None = None,
    route: str = "",
    initial_request_ref: str = "",
    notes: str = "",
    timestamp: str = "",
    status: str = "success",
    summary: str = "",
    next_action: str = "",
    error_kind: str = "",
    retry_hint: str = "",
    stop_condition: str = "",
    data: JsonObject | None = None,
) -> None:
    if actor:
        validate_enum("actor", actor, ACTORS)
    if phase:
        validate_enum("phase", phase, PHASES | set(LEGACY_PHASE_ALIASES))
    if status:
        validate_enum("audit status", status, AUDIT_STATUSES)
    if next_action:
        validate_enum("nextAction", next_action, NEXT_ACTIONS | set(LEGACY_NEXT_ACTION_ALIASES))
    if route:
        validate_enum("route", route, ROUTES)
    timestamp = timestamp or current_timestamp()
    entry: JsonObject = {
        "seq": next_audit_seq(topic),
        "timestamp": timestamp,
        "event": event,
        "actor": actor,
        "status": status or "success",
        "summary": summary or notes or event,
        "phase": phase or None,
        "nextAction": next_action or None,
        "artifacts": artifacts or [],
        "route": route or None,
        "task": data.get("task") if data else None,
        "command": data.get("command") if data else None,
        "result": data.get("result") if data else None,
        "stopCondition": stop_condition or None,
        "errorKind": error_kind or None,
        "retryHint": retry_hint or None,
        "notes": notes or "",
        "data": data or {},
    }
    if initial_request_ref:
        entry["initialRequestRef"] = initial_request_ref
    path = audit_path(topic)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def audit_events(topic: Path) -> list[JsonObject]:
    path = audit_path(topic)
    if not path.exists():
        return []
    events: list[JsonObject] = []
    with path.open("r", encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL in {path}:{index}: {exc}") from exc
            if not isinstance(entry, dict):
                raise SystemExit(f"Audit line must be a JSON object: {path}:{index}")
            events.append(entry)
    return events


def _record_artifact(status: JsonObject, artifact: str, artifact_name: str = "") -> None:
    artifacts = status["artifacts"]
    field = artifact_name or ARTIFACT_FIELD_BY_FILE.get(artifact, "")
    if field == "question" or artifact.startswith("question-c"):
        questions = artifacts["questions"]
        if artifact not in questions:
            questions.append(artifact)
        return
    if field in {"requirements", "plan", "codeReviewReport", "report", "topic", "audit"}:
        artifacts[field] = artifact


def derive_status(topic: Path) -> JsonObject:
    events = audit_events(topic)
    status: JsonObject = {
        "topic": topic.name,
        "status": "active",
        "phase": "",
        "nextAction": "",
        "lastEventSeq": 0,
        "lastEvent": "",
        "artifacts": {
            "questions": [],
            "requirements": None,
            "plan": None,
            "codeReviewReport": None,
            "report": None,
            "topic": "topic.md" if topic_md_path(topic).exists() else None,
            "audit": "audit.jsonl" if audit_path(topic).exists() else None,
        },
        "blockers": [],
        "openItems": [],
        "approvals": [],
        "verification": [],
        "review": None,
        "tasks": {},
        "taskFindings": [],
        "sweeps": [],
    }
    blockers: dict[str, JsonObject] = {}
    task_findings: dict[str, JsonObject] = {}
    for event in events:
        if event.get("status") == "error":
            continue
        seq = event.get("seq")
        name = event.get("event")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if name == "topic.created" and data.get("topic"):
            status["topic"] = data["topic"]
        if isinstance(seq, int):
            status["lastEventSeq"] = seq
        if name:
            status["lastEvent"] = name
        if event.get("phase"):
            status["phase"] = LEGACY_PHASE_ALIASES.get(event["phase"], event["phase"])
        if event.get("nextAction"):
            status["nextAction"] = LEGACY_NEXT_ACTION_ALIASES.get(event["nextAction"], event["nextAction"])
        if name == "topic.finalized":
            status["status"] = data.get("status", "complete")
        for artifact in event.get("artifacts") or []:
            if isinstance(artifact, str):
                _record_artifact(status, artifact)
        if name == "artifact.recorded" and data.get("artifactName") and data.get("artifactValue"):
            _record_artifact(status, data["artifactValue"], data["artifactName"])
        if name == "blocker.recorded":
            blocker_id = data.get("id") or event.get("summary") or str(seq)
            blockers[blocker_id] = {"id": blocker_id, "summary": event.get("summary"), "data": data}
        elif name == "blocker.resolved":
            blocker_id = data.get("id") or event.get("summary")
            if blocker_id in blockers:
                blockers.pop(blocker_id)
        elif str(name).startswith("approval."):
            status["approvals"].append(event)
        elif name == "verification.recorded":
            status["verification"].append(event)
        elif name == "task.completed":
            if data.get("verification"):
                status["verification"].append(data)
            if data.get("task"):
                task = status["tasks"].setdefault(
                    data["task"],
                    {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
                )
                task["completed"] = data
        elif name == "task.dispatched" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["mode"] = data.get("mode") or task.get("mode")
            task["dispatches"].append(data)
        elif name == "task.review_completed" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["reviews"].append(data)
            if data.get("status") in {"findings", "blocked"}:
                for finding_id in data.get("findingIds") or []:
                    task_findings[finding_id] = {
                        "id": finding_id,
                        "task": data.get("task"),
                        "reviewType": data.get("reviewType"),
                        "status": data.get("status"),
                        "critical": data.get("critical"),
                        "important": data.get("important"),
                        "minor": data.get("minor"),
                        "summary": event.get("summary"),
                    }
        elif name in {"task.fix_requested", "task.fix_completed"} and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["fixes"].append(data)
            if name == "task.fix_completed" and data.get("findingId") in task_findings:
                task_findings.pop(data["findingId"])
        elif name == "task.commit_recorded" and data.get("task"):
            task = status["tasks"].setdefault(
                data["task"],
                {"dispatches": [], "reviews": [], "fixes": [], "commits": []},
            )
            task["commits"].append(data)
        elif name == "sweep.completed":
            status["sweeps"].append(data)
        elif name == "review.completed":
            status["review"] = data
    status["blockers"] = list(blockers.values())
    status["taskFindings"] = list(task_findings.values())
    if status["blockers"] and status["status"] == "active":
        status["status"] = "blocked"
    return status


def append_durable_topic_note(topic: Path, heading: str, summary: str, timestamp: str, actor: str, source: str = "") -> None:
    path = topic_md_path(topic)
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    detail = f"- {summary}"
    if source:
        detail += f" (source: {source})"
    detail += f" [{actor}, {timestamp}]"
    text = path.read_text(encoding="utf-8")
    marker = f"## {heading}"
    if marker not in text:
        text = text.rstrip() + f"\n\n{marker}\n\n{detail}\n"
    else:
        head, tail = text.split(marker, 1)
        next_heading = tail.find("\n## ")
        if next_heading == -1:
            section = tail.rstrip()
            tail_rest = ""
        else:
            section = tail[:next_heading].rstrip()
            tail_rest = tail[next_heading:]
        if "- None recorded yet." in section:
            section = section.replace("- None recorded yet.", detail)
        else:
            section = section + "\n" + detail
        text = head + marker + section + tail_rest
        if not text.endswith("\n"):
            text += "\n"
    path.write_text(text, encoding="utf-8")


def validate_audit(topic: Path) -> None:
    events = audit_events(topic)
    previous_seq = 0
    seen_seq: set[int] = set()
    for index, entry in enumerate(events, start=1):
        for key in ("seq", "timestamp", "event", "actor", "status", "summary", "artifacts", "data"):
            if key not in entry:
                raise SystemExit(f"Audit line missing {key}: {audit_path(topic)}:{index}")
        seq = entry.get("seq")
        if not isinstance(seq, int):
            raise SystemExit(f"Audit line seq must be an integer: {audit_path(topic)}:{index}")
        if seq in seen_seq:
            raise SystemExit(f"Audit seq values must be unique at event {index}")
        if seq <= previous_seq:
            raise SystemExit(f"Audit seq values must be monotonic at event {index}")
        seen_seq.add(seq)
        previous_seq = seq
        if not isinstance(entry.get("timestamp"), str) or not entry.get("timestamp"):
            raise SystemExit(f"Audit line timestamp must be a non-empty string: {audit_path(topic)}:{index}")
        if not isinstance(entry.get("event"), str) or not entry.get("event"):
            raise SystemExit(f"Audit line event must be a non-empty string: {audit_path(topic)}:{index}")
        if not isinstance(entry.get("summary"), str) or not entry.get("summary"):
            raise SystemExit(f"Audit line summary must be a non-empty string: {audit_path(topic)}:{index}")
        validate_enum(f"audit actor at {audit_path(topic)}:{index}", str(entry.get("actor")), ACTORS)
        status = entry.get("status")
        if status is not None:
            validate_enum(f"audit status at {audit_path(topic)}:{index}", str(status), AUDIT_STATUSES)
        phase = entry.get("phase")
        if phase:
            validate_enum(
                f"audit phase at {audit_path(topic)}:{index}",
                str(phase),
                PHASES | set(LEGACY_PHASE_ALIASES),
            )
        next_action = entry.get("nextAction")
        if next_action:
            validate_enum(
                f"audit nextAction at {audit_path(topic)}:{index}",
                str(next_action),
                NEXT_ACTIONS | set(LEGACY_NEXT_ACTION_ALIASES),
            )
        route = entry.get("route")
        if route:
            validate_enum(f"audit route at {audit_path(topic)}:{index}", str(route), ROUTES)
        artifacts = entry.get("artifacts")
        if not isinstance(artifacts, list):
            raise SystemExit(f"Audit line artifacts must be a list: {audit_path(topic)}:{index}")
        data = entry.get("data")
        if not isinstance(data, dict):
            raise SystemExit(f"Audit line data must be a JSON object: {audit_path(topic)}:{index}")


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
    append_audit(
        topic,
        event="start_work.routed",
        actor=args.actor,
        phase="start-work",
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
    if args.mode == "tdd":
        if not args.test_target:
            raise SystemExit("TDD task requires test target evidence.")
        if not args.red_evidence:
            raise SystemExit("TDD task requires RED evidence before implementation.")
        if not args.green_evidence:
            raise SystemExit("TDD task requires GREEN evidence after implementation.")
    if args.mode == "approved-tdd-exception":
        if args.exception_category not in TDD_EXCEPTION_CATEGORIES:
            allowed = ", ".join(sorted(TDD_EXCEPTION_CATEGORIES))
            raise SystemExit(
                f"Invalid TDD exception category: {args.exception_category or '<empty>'}. Allowed categories: {allowed}"
            )
        if not args.exception_approval:
            raise SystemExit("TDD exception requires human approval source.")
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
            "exceptionCategory": args.exception_category,
            "exceptionApproval": args.exception_approval,
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
        data={"status": args.status, "report": args.report},
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
        data={"command": args.command, "result": args.result},
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


def validate_topic_invariants(topic: Path) -> None:
    require_invariant(topic_md_path(topic).exists(), "topic requires topic.md")
    require_invariant(audit_path(topic).exists(), "topic requires audit.jsonl")
    events = audit_events(topic)
    require_invariant(events, "topic requires at least one audit event")
    previous_seq = 0
    seen_seq: set[int] = set()
    for index, event in enumerate(events, start=1):
        seq = event.get("seq")
        require_invariant(isinstance(seq, int), f"audit event {index} requires integer seq")
        require_invariant(seq not in seen_seq, f"audit seq values must be unique at event {index}")
        require_invariant(seq > previous_seq, f"audit seq values must be monotonic at event {index}")
        seen_seq.add(seq)
        previous_seq = seq
        for key in ("timestamp", "event", "actor", "status", "summary"):
            require_invariant(key in event, f"audit event {index} missing {key}")
    status = derive_status(topic)
    finalized_events = [event for event in events if event.get("event") == "topic.finalized"]
    if finalized_events:
        require_invariant(status["artifacts"].get("report"), "finalized topic requires report.md artifact")
        review_events = [event for event in events if event.get("event") == "review.completed"]
        require_invariant(
            review_events,
            "finalized topic requires review.completed audit event",
        )
        require_invariant(
            any(event.get("event") in CODE_CLEANUP_DECISION_EVENTS for event in events),
            "finalized topic requires code cleanup decision audit event",
        )
        finalized_data = finalized_events[-1].get("data") or {}
        finalized_status = finalized_data.get("status")
        if finalized_status in {"complete", "follow-up-needed"}:
            latest_review_data = review_events[-1].get("data") or {}
            require_invariant(
                latest_review_data.get("status") == "passed",
                "finalized complete/follow-up-needed topic requires latest review.completed status must be passed",
            )
            require_invariant(
                int(latest_review_data.get("critical") or 0) == 0 and int(latest_review_data.get("important") or 0) == 0,
                "finalized complete/follow-up-needed topic requires no unresolved critical or important review findings",
            )


def cmd_validate(args: argparse.Namespace) -> None:
    topic = require_existing_topic_dir(args.topic_dir)
    validate_audit(topic)
    validate_topic_invariants(topic)
    sys.stdout.write("OK\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage AsUsual topic.md and audit.jsonl.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize topic.md and audit.jsonl.")
    init.add_argument("--topic-dir", required=True)
    init.add_argument("--topic", required=True)
    init.add_argument("--initial-request", default="")
    init.add_argument("--summary", default="")
    init.add_argument("--actor", default="codex")
    init.add_argument("--host", default="")
    init.add_argument("--session-id", default="")
    init.add_argument("--notes", default="")
    init.add_argument("--timestamp", default="")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    audit = sub.add_parser("audit", help="Append one audit.jsonl event.")
    audit.add_argument("--topic-dir", required=True)
    audit.add_argument("--event", required=True)
    audit.add_argument("--actor", default="codex")
    audit.add_argument("--phase", default="")
    audit.add_argument("--artifacts", default="")
    audit.add_argument("--route", default="")
    audit.add_argument("--initial-request-ref", default="")
    audit.add_argument("--notes", default="")
    audit.add_argument("--status", choices=sorted(AUDIT_STATUSES), default="success")
    audit.add_argument("--summary", default="")
    audit.add_argument("--next-action", default="")
    audit.add_argument("--error-kind", default="")
    audit.add_argument("--retry-hint", default="")
    audit.add_argument("--stop-condition", default="")
    audit.add_argument("--timestamp", default="")
    audit.set_defaults(func=cmd_audit)

    artifact = sub.add_parser("artifact", help="Record one artifact event.")
    artifact.add_argument("--topic-dir", required=True)
    artifact.add_argument("--name", required=True)
    artifact.add_argument("--value", required=True)
    artifact.add_argument("--append", action="store_true")
    artifact.add_argument("--actor", default="codex")
    artifact.add_argument("--phase", default="")
    artifact.add_argument("--summary", default="")
    artifact.add_argument("--notes", default="")
    artifact.add_argument("--next-action", default="")
    artifact.add_argument("--timestamp", default="")
    artifact.set_defaults(func=cmd_artifact)

    route = sub.add_parser("route-start-work", help="Append start-work routing event.")
    route.add_argument("--topic-dir", required=True)
    route.add_argument("--route", required=True, choices=sorted(ROUTES))
    route.add_argument("--reason", default="")
    route.add_argument("--next-action", default="")
    route.add_argument("--skipped-gates", default="")
    route.add_argument("--verification-plan", default="")
    route.add_argument("--actor", default="codex")
    route.add_argument("--timestamp", default="")
    route.set_defaults(func=cmd_route_start_work)

    complete_requirements = sub.add_parser("complete-requirements", help="Append requirements completion event.")
    complete_requirements.add_argument("--topic-dir", required=True)
    complete_requirements.add_argument("--requirements", default="requirements.md")
    complete_requirements.add_argument("--summary", default="")
    complete_requirements.add_argument("--actor", default="codex")
    complete_requirements.add_argument("--timestamp", default="")
    complete_requirements.set_defaults(func=cmd_complete_requirements)

    complete_plan = sub.add_parser("complete-plan", help="Append plan completion event.")
    complete_plan.add_argument("--topic-dir", required=True)
    complete_plan.add_argument("--plan", default="plan.md")
    complete_plan.add_argument("--summary", default="")
    complete_plan.add_argument("--actor", default="codex")
    complete_plan.add_argument("--timestamp", default="")
    complete_plan.set_defaults(func=cmd_complete_plan)

    approve_execution = sub.add_parser("approve-execution", help="Append execution approval event.")
    approve_execution.add_argument("--topic-dir", required=True)
    approve_execution.add_argument("--summary", default="")
    approve_execution.add_argument("--approved-by", default="user")
    approve_execution.add_argument("--source", default="chat")
    approve_execution.add_argument("--actor", default="user")
    approve_execution.add_argument("--timestamp", default="")
    approve_execution.set_defaults(func=cmd_approve_execution)

    approve_high_risk = sub.add_parser("approve-high-risk", help="Append high-risk approval event.")
    approve_high_risk.add_argument("--topic-dir", required=True)
    approve_high_risk.add_argument("--operation-id", required=True)
    approve_high_risk.add_argument("--description", default="")
    approve_high_risk.add_argument("--approved-by", default="user")
    approve_high_risk.add_argument("--rollback", default="")
    approve_high_risk.add_argument("--summary", default="")
    approve_high_risk.add_argument("--artifacts", default="")
    approve_high_risk.add_argument("--actor", default="user")
    approve_high_risk.add_argument("--timestamp", default="")
    approve_high_risk.set_defaults(func=cmd_approve_high_risk)

    complete_task = sub.add_parser("complete-task", help="Append task completion event.")
    complete_task.add_argument("--topic-dir", required=True)
    complete_task.add_argument("--task", required=True)
    complete_task.add_argument("--summary", default="")
    complete_task.add_argument("--verification", default="")
    complete_task.add_argument("--mode", default="")
    complete_task.add_argument("--test-target", default="")
    complete_task.add_argument("--red-evidence", default="")
    complete_task.add_argument("--green-evidence", default="")
    complete_task.add_argument("--expected-result", default="")
    complete_task.add_argument("--result", default="")
    complete_task.add_argument("--exception-category", default="")
    complete_task.add_argument("--exception-approval", default="")
    complete_task.add_argument("--artifacts", default="")
    complete_task.add_argument("--actor", default="codex")
    complete_task.add_argument("--timestamp", default="")
    complete_task.set_defaults(func=cmd_complete_task)

    complete_execution = sub.add_parser("complete-execution", help="Append execution completion event.")
    complete_execution.add_argument("--topic-dir", required=True)
    complete_execution.add_argument("--summary", default="")
    complete_execution.add_argument("--verification", default="")
    complete_execution.add_argument("--result", default="")
    complete_execution.add_argument("--artifacts", default="")
    complete_execution.add_argument("--actor", default="codex")
    complete_execution.add_argument("--timestamp", default="")
    complete_execution.set_defaults(func=cmd_complete_execution)

    dispatch_task = sub.add_parser("dispatch-task", help="Append task dispatch event.")
    dispatch_task.add_argument("--topic-dir", required=True)
    dispatch_task.add_argument("--task", required=True)
    dispatch_task.add_argument("--mode", required=True, choices=sorted(EXECUTION_MODES))
    dispatch_task.add_argument("--role", default="implementer", choices=sorted(TASK_ROLES))
    dispatch_task.add_argument("--context", default="")
    dispatch_task.add_argument("--summary", default="")
    dispatch_task.add_argument("--artifacts", default="")
    dispatch_task.add_argument("--actor", default="codex")
    dispatch_task.add_argument("--timestamp", default="")
    dispatch_task.set_defaults(func=cmd_dispatch_task)

    task_review = sub.add_parser("record-task-review", help="Append task-level review event.")
    task_review.add_argument("--topic-dir", required=True)
    task_review.add_argument("--task", required=True)
    task_review.add_argument("--review-type", required=True, choices=sorted(TASK_REVIEW_TYPES))
    task_review.add_argument("--status", required=True, choices=sorted(REVIEW_STATUSES))
    task_review.add_argument("--critical", type=int, default=0)
    task_review.add_argument("--important", type=int, default=0)
    task_review.add_argument("--minor", type=int, default=0)
    task_review.add_argument("--finding-ids", default="")
    task_review.add_argument("--summary", default="")
    task_review.add_argument("--artifacts", default="")
    task_review.add_argument("--actor", default="codex")
    task_review.add_argument("--timestamp", default="")
    task_review.set_defaults(func=cmd_record_task_review)

    task_fix = sub.add_parser("record-task-fix", help="Append task fix request or completion event.")
    task_fix.add_argument("--topic-dir", required=True)
    task_fix.add_argument("--task", required=True)
    task_fix.add_argument("--finding-id", required=True)
    task_fix.add_argument("--status", required=True, choices=sorted(TASK_FIX_STATUSES))
    task_fix.add_argument("--summary", default="")
    task_fix.add_argument("--artifacts", default="")
    task_fix.add_argument("--actor", default="codex")
    task_fix.add_argument("--timestamp", default="")
    task_fix.set_defaults(func=cmd_record_task_fix)

    task_commit = sub.add_parser("record-task-commit", help="Append task commit boundary event.")
    task_commit.add_argument("--topic-dir", required=True)
    task_commit.add_argument("--task", required=True)
    task_commit.add_argument("--sha", required=True)
    task_commit.add_argument("--summary", default="")
    task_commit.add_argument("--actor", default="codex")
    task_commit.add_argument("--timestamp", default="")
    task_commit.set_defaults(func=cmd_record_task_commit)

    sweep = sub.add_parser("record-sweep", help="Append final or task sweep evidence event.")
    sweep.add_argument("--topic-dir", required=True)
    sweep.add_argument("--kind", required=True, choices=sorted(SWEEP_KINDS))
    sweep.add_argument("--command", required=True)
    sweep.add_argument("--result", required=True)
    sweep.add_argument("--summary", default="")
    sweep.add_argument("--status", choices=sorted(AUDIT_STATUSES), default="success")
    sweep.add_argument("--phase", default="")
    sweep.add_argument("--next-action", default="")
    sweep.add_argument("--artifacts", default="")
    sweep.add_argument("--actor", default="codex")
    sweep.add_argument("--timestamp", default="")
    sweep.set_defaults(func=cmd_record_sweep)

    record_review = sub.add_parser("record-review", help="Append execution review event.")
    record_review.add_argument("--topic-dir", required=True)
    record_review.add_argument("--mode", required=True, choices=sorted(REVIEW_MODES))
    record_review.add_argument("--status", required=True, choices=sorted(REVIEW_STATUSES))
    record_review.add_argument("--critical", type=int, default=0)
    record_review.add_argument("--important", type=int, default=0)
    record_review.add_argument("--minor", type=int, default=0)
    record_review.add_argument("--reason", default="")
    record_review.add_argument("--report", default="")
    record_review.add_argument("--actor", default="codex")
    record_review.add_argument("--timestamp", default="")
    record_review.set_defaults(func=cmd_record_review)

    skip_code_cleanup = sub.add_parser("skip-code-cleanup", help="Append code cleanup skipped event.")
    skip_code_cleanup.add_argument("--topic-dir", required=True)
    skip_code_cleanup.add_argument("--reason", default="")
    skip_code_cleanup.add_argument("--actor", default="codex")
    skip_code_cleanup.add_argument("--timestamp", default="")
    skip_code_cleanup.set_defaults(func=cmd_skip_code_cleanup)

    skip_simplify = sub.add_parser("skip-simplify", help="Deprecated alias for skip-code-cleanup.")
    skip_simplify.add_argument("--topic-dir", required=True)
    skip_simplify.add_argument("--reason", default="")
    skip_simplify.add_argument("--actor", default="codex")
    skip_simplify.add_argument("--timestamp", default="")
    skip_simplify.set_defaults(func=cmd_skip_code_cleanup)

    finalize_topic = sub.add_parser("finalize-topic", help="Append topic finalization event.")
    finalize_topic.add_argument("--topic-dir", required=True)
    finalize_topic.add_argument("--status", required=True, choices=sorted(STATUSES - {"active"}))
    finalize_topic.add_argument("--summary", default="")
    finalize_topic.add_argument("--report", default="report.md")
    finalize_topic.add_argument("--actor", default="codex")
    finalize_topic.add_argument("--timestamp", default="")
    finalize_topic.set_defaults(func=cmd_finalize_topic)

    select_git_action = sub.add_parser("select-git-action", help="Append selected git action event.")
    select_git_action.add_argument("--topic-dir", required=True)
    select_git_action.add_argument("--action", required=True, choices=sorted(GIT_ACTIONS))
    select_git_action.add_argument("--summary", default="")
    select_git_action.add_argument("--actor", default="user")
    select_git_action.add_argument("--timestamp", default="")
    select_git_action.set_defaults(func=cmd_select_git_action)

    rec_mem_cand = sub.add_parser("record-memory-candidate")
    rec_mem_cand.add_argument("--topic-dir", required=True)
    rec_mem_cand.add_argument("--summary", required=True)
    rec_mem_cand.add_argument("--source-phase", default="")
    rec_mem_cand.add_argument("--proposed-target", choices=["memory", "skill", "undecided"], default="undecided")
    rec_mem_cand.add_argument("--actor", default="codex")
    rec_mem_cand.set_defaults(func=cmd_record_memory_candidate)

    rec_mem = sub.add_parser("record-memory")
    rec_mem.add_argument("--topic-dir", required=True)
    rec_mem.add_argument("--summary", required=True)
    rec_mem.add_argument("--files", default="")
    rec_mem.add_argument("--actor", default="codex")
    rec_mem.set_defaults(func=cmd_record_memory)

    rec_skill = sub.add_parser("record-skill")
    rec_skill.add_argument("--topic-dir", required=True)
    rec_skill.add_argument("--state", choices=["created", "candidate"], required=True)
    rec_skill.add_argument("--summary", required=True)
    rec_skill.add_argument("--kind", choices=["new", "patch"], required=True)
    rec_skill.add_argument("--patch-target", default="")
    rec_skill.add_argument("--dest", default="")
    rec_skill.add_argument("--rationale", default="")
    rec_skill.add_argument("--brief", default="")
    rec_skill.add_argument("--actor", default="codex")
    rec_skill.set_defaults(func=cmd_record_skill)

    note = sub.add_parser("note", help="Append note event.")
    note.add_argument("--topic-dir", required=True)
    note.add_argument("--summary", required=True)
    note.add_argument("--durable-topic-note", action="store_true")
    note.add_argument("--phase", default="")
    note.add_argument("--next-action", default="")
    note.add_argument("--actor", default="codex")
    note.add_argument("--timestamp", default="")
    note.set_defaults(func=cmd_note)

    decision = sub.add_parser("decision", help="Append decision event.")
    decision.add_argument("--topic-dir", required=True)
    decision.add_argument("--summary", required=True)
    decision.add_argument("--source", required=True)
    decision.add_argument("--durable-topic-note", action="store_true")
    decision.add_argument("--phase", default="")
    decision.add_argument("--next-action", default="")
    decision.add_argument("--actor", default="codex")
    decision.add_argument("--timestamp", default="")
    decision.set_defaults(func=cmd_decision)

    blocker = sub.add_parser("blocker", help="Append blocker event.")
    blocker.add_argument("--topic-dir", required=True)
    blocker.add_argument("--summary", required=True)
    blocker.add_argument("--id", required=True)
    blocker.add_argument("--next-action", default="none")
    blocker.add_argument("--actor", default="codex")
    blocker.add_argument("--timestamp", default="")
    blocker.set_defaults(func=cmd_blocker)

    verification = sub.add_parser("verification", help="Append verification event.")
    verification.add_argument("--topic-dir", required=True)
    verification.add_argument("--summary", required=True)
    verification.add_argument("--command", required=True)
    verification.add_argument("--result", required=True)
    verification.add_argument("--phase", default="")
    verification.add_argument("--next-action", default="")
    verification.add_argument("--artifacts", default="")
    verification.add_argument("--actor", default="codex")
    verification.add_argument("--timestamp", default="")
    verification.set_defaults(func=cmd_verification)

    status = sub.add_parser("status", help="Print derived topic status.")
    status.add_argument("--topic-dir", required=True)
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    validate = sub.add_parser("validate", help="Validate topic.md and audit.jsonl.")
    validate.add_argument("--topic-dir", required=True)
    validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "topic_dir"):
        topic = resolve_topic_dir(args.topic_dir)
        with topic_lock(topic):
            args.func(args)
    else:
        args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
