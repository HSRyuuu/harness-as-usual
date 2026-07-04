"""Validation helpers for topic-log audit artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import (
    ACTORS,
    AUDIT_STATUSES,
    CODE_CLEANUP_DECISION_EVENTS,
    LEGACY_NEXT_ACTION_ALIASES,
    LEGACY_PHASE_ALIASES,
    NEXT_ACTIONS,
    PHASES,
    ROUTES,
)
from .paths import audit_path, topic_md_path


def validate_enum(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise SystemExit(f"Invalid {name}: {value}. Allowed values: {allowed_values}")


def validate_canonical_filename(name: str, value: str, expected: str) -> None:
    if value != expected:
        raise SystemExit(f"Invalid {name}: {value}. {name} must be {expected}")


def require_invariant(condition: Any, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def validate_audit(topic: Path) -> None:
    from .audit import audit_events

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


def validate_topic_invariants(topic: Path) -> None:
    from .audit import audit_events
    from .status import derive_status

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
        finalized_data = finalized_events[-1].get("data") or {}
        finalized_status = finalized_data.get("status")
        if finalized_status == "cancelled":
            # A cancelled topic may be closed from any phase, including before
            # execution/review. It is exempt from report/review/cleanup evidence,
            # but the explicit cancellation reason summary is required.
            require_invariant(
                (finalized_data.get("cancellationReason") or "").strip(),
                "finalized cancelled topic requires a cancellation reason summary",
            )
        else:
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
