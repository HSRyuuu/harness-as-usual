"""Audit JSONL read/write helpers for topic-log."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from .constants import (
    ACTORS,
    AUDIT_STATUSES,
    LEGACY_NEXT_ACTION_ALIASES,
    LEGACY_PHASE_ALIASES,
    NEXT_ACTIONS,
    PHASES,
    ROUTES,
    JsonObject,
)
from .paths import audit_path
from .validation import validate_enum


def current_timestamp() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="milliseconds")


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
