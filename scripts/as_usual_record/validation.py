"""Structural validation of an existing record file.

`validate` is an after-the-fact audit of what the append gates should already
have prevented. It exists to catch hand-editing and concurrent writes.
"""

from __future__ import annotations

from pathlib import Path

from .constants import (
    ACTORS,
    APPROVAL_ACTIONS,
    AUDITABLE_KINDS,
    AUDITABLE_LIFECYCLE_EVENTS,
    CLOSING_LIFECYCLE_EVENTS,
    NEXT_ACTION_SPECIALS,
    PHASES,
    STATUS_CHANGE_STATES,
    STATUSES,
    UNIT_PHASES,
    UNITS,
    VERDICTS,
    JsonObject,
)
from .contexts import read_declared_unit
from .paths import RecordError, audit_path, contexts_path
from .records import current_unit, read_events


REQUIRED_FIELDS = ("seq", "ts", "actor", "unit", "kind", "status", "summary")


def validate_record(work_dir: Path) -> list[str]:
    problems: list[str] = []
    events = read_events(work_dir)
    path = audit_path(work_dir)

    if not events:
        return [f"{path}: record is empty"]

    seen: set[int] = set()
    previous = 0
    closed_at: int | None = None

    for index, entry in enumerate(events, start=1):
        where = f"{path}:{index}"
        for field in REQUIRED_FIELDS:
            if field not in entry:
                problems.append(f"{where}: missing {field}")
        seq = entry.get("seq")
        if not isinstance(seq, int) or isinstance(seq, bool):
            problems.append(f"{where}: seq must be an integer")
        else:
            if seq in seen:
                problems.append(f"{where}: duplicate seq {seq}")
            if seq <= previous:
                problems.append(f"{where}: seq {seq} is not increasing")
            seen.add(seq)
            previous = max(previous, seq)

        problems.extend(_check_vocabulary(entry, where))
        problems.extend(_check_payload(entry, where))

        if closed_at is not None:
            is_link = entry.get("kind") == "lifecycle" and _event(entry) == "linked"
            if not is_link:
                problems.append(
                    f"{where}: appended after the record was closed at seq {closed_at}"
                )
        if entry.get("kind") == "lifecycle" and _event(entry) in CLOSING_LIFECYCLE_EVENTS:
            if closed_at is None and isinstance(seq, int):
                closed_at = seq

    problems.extend(_check_declared_unit(work_dir, events))
    return problems


def _check_declared_unit(work_dir: Path, events: list[JsonObject]) -> list[str]:
    """`contexts.md` and the record must name the same unit.

    The append gates cannot catch this: the two files are written by different
    paths, and a folder re-created around a surviving `contexts.md` ends up with
    a document claiming one unit and a record claiming another.
    """
    try:
        recorded = current_unit(events)
    except RecordError:
        # Missing `unit` fields are already reported per entry above.
        return []

    where = contexts_path(work_dir)
    declared = read_declared_unit(work_dir)
    if declared is None:
        return [
            f"{where}: does not declare a unit. add `unit: {recorded}` to the frontmatter"
        ]
    if declared != recorded:
        return [
            f"{where}: declares unit {declared}, but the record says {recorded}. "
            "one of the two was edited by hand — correct the document, or `move` the "
            "folder so both agree"
        ]
    return []


def _event(entry: JsonObject) -> str | None:
    data = entry.get("data")
    if isinstance(data, dict):
        value = data.get("event")
        return value if isinstance(value, str) else None
    return None


def _check_vocabulary(entry: JsonObject, where: str) -> list[str]:
    problems: list[str] = []
    unit = entry.get("unit")
    checks = (
        ("unit", unit, UNITS),
        ("kind", entry.get("kind"), AUDITABLE_KINDS),
        ("actor", entry.get("actor"), ACTORS),
        ("status", entry.get("status"), STATUSES),
    )
    for name, value, allowed in checks:
        if isinstance(value, str) and value not in allowed:
            problems.append(f"{where}: invalid {name} {value}")

    phase = entry.get("phase")
    if isinstance(phase, str) and phase:
        if phase not in PHASES:
            problems.append(f"{where}: invalid phase {phase}")
        elif isinstance(unit, str) and unit in UNIT_PHASES and phase not in UNIT_PHASES[unit]:
            problems.append(f"{where}: phase {phase} is not used by unit {unit}")

    next_action = entry.get("nextAction")
    if isinstance(next_action, str) and next_action:
        if next_action not in PHASES | NEXT_ACTION_SPECIALS:
            problems.append(f"{where}: invalid nextAction {next_action}")

    return problems


def _check_payload(entry: JsonObject, where: str) -> list[str]:
    problems: list[str] = []
    kind = entry.get("kind")
    data = entry.get("data")
    data = data if isinstance(data, dict) else {}

    if kind == "verification":
        verdict = data.get("verdict")
        if verdict not in VERDICTS:
            problems.append(f"{where}: verification requires a valid verdict")
    elif kind == "lifecycle":
        event = data.get("event")
        if event not in AUDITABLE_LIFECYCLE_EVENTS:
            problems.append(f"{where}: invalid lifecycle event {event}")
    elif kind == "approval":
        if data.get("action") not in APPROVAL_ACTIONS:
            problems.append(f"{where}: invalid approval action {data.get('action')}")
    elif kind == "status-change":
        if data.get("to") not in STATUS_CHANGE_STATES:
            problems.append(f"{where}: invalid status-change target state {data.get('to')}")
        if not isinstance(data.get("target"), int) or isinstance(data.get("target"), bool):
            problems.append(f"{where}: status-change requires an integer target")
        if data.get("to") == "confirmed" and not data.get("evidence"):
            problems.append(f"{where}: confirmed status-change requires evidence")

    return problems
