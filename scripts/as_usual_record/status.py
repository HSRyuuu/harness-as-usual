"""Derived state for a work unit.

Current state is never remembered, only derived: phase, next action, blockers,
approvals, verification, and links all come from the append-only record.
"""

from __future__ import annotations

from pathlib import Path

from .constants import CLOSING_LIFECYCLE_EVENTS, MOVE_BLOCKING_FILES, JsonObject
from .records import current_unit, read_events


TRACKED_ARTIFACTS = MOVE_BLOCKING_FILES + ("contexts.md", "review.md", "report.md")


def derive_status(work_dir: Path) -> JsonObject:
    events = read_events(work_dir)
    unit = current_unit(events)

    phase = _latest_field(events, "phase")
    next_action = _latest_field(events, "nextAction")
    lifecycle = _lifecycle_state(events)

    return {
        "dir": str(work_dir),
        "unit": unit,
        "state": lifecycle,
        "phase": phase,
        "nextAction": next_action,
        "eventCount": len(events),
        "lastEvent": _summarize(events[-1]) if events else None,
        "blockers": _open_blockers(events),
        "approvals": _approvals(events),
        "verification": _verification(events),
        "confirmed": _status_changes(events, "confirmed"),
        "cancelled": _status_changes(events, "cancelled"),
        "links": _links(events),
        "artifacts": [name for name in TRACKED_ARTIFACTS if (work_dir / name).exists()],
        "moveAllowed": not any((work_dir / name).exists() for name in MOVE_BLOCKING_FILES),
    }


def _latest_field(events: list[JsonObject], field: str) -> str | None:
    for entry in reversed(events):
        value = entry.get(field)
        if isinstance(value, str) and value:
            return value
    return None


def _lifecycle_state(events: list[JsonObject]) -> str:
    for entry in events:
        if entry.get("kind") != "lifecycle":
            continue
        event = entry.get("data", {}).get("event")
        if event in CLOSING_LIFECYCLE_EVENTS:
            return "finalized" if event == "finalized" else "cancelled"
    return "open"


def _summarize(entry: JsonObject) -> JsonObject:
    return {
        "seq": entry.get("seq"),
        "kind": entry.get("kind"),
        "status": entry.get("status"),
        "summary": entry.get("summary"),
    }


def _open_blockers(events: list[JsonObject]) -> list[JsonObject]:
    resolved: set[int] = set()
    for entry in events:
        if entry.get("kind") != "blocker":
            continue
        target = entry.get("data", {}).get("resolves")
        if isinstance(target, int) and not isinstance(target, bool):
            resolved.add(target)
    return [
        _summarize(entry)
        for entry in events
        if entry.get("kind") == "blocker"
        and entry.get("seq") not in resolved
        and not entry.get("data", {}).get("resolves")
    ]


def _approvals(events: list[JsonObject]) -> list[JsonObject]:
    return [
        {
            "seq": entry.get("seq"),
            "action": entry.get("data", {}).get("action"),
            "summary": entry.get("summary"),
        }
        for entry in events
        if entry.get("kind") == "approval"
    ]


def _verification(events: list[JsonObject]) -> JsonObject | None:
    latest = None
    for entry in events:
        if entry.get("kind") == "verification":
            latest = entry
    if latest is None:
        return None
    return {
        "seq": latest.get("seq"),
        "verdict": latest.get("data", {}).get("verdict"),
        "summary": latest.get("summary"),
    }


def _status_changes(events: list[JsonObject], state: str) -> list[int]:
    return [
        entry["data"]["target"]
        for entry in events
        if entry.get("kind") == "status-change"
        and entry.get("data", {}).get("to") == state
        and isinstance(entry.get("data", {}).get("target"), int)
    ]


def _links(events: list[JsonObject]) -> list[str]:
    links: list[str] = []
    for entry in events:
        if entry.get("kind") != "lifecycle":
            continue
        data = entry.get("data", {})
        if data.get("event") != "linked":
            continue
        target = data.get("to")
        if isinstance(target, str) and target and target not in links:
            links.append(target)
    return links
