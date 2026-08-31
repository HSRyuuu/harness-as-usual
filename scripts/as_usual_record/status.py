"""Derived state for a work unit.

Current state is never remembered, only derived: phase, next action, blockers,
approvals, verification, and links all come from the append-only record.
"""

from __future__ import annotations

from pathlib import Path

from .constants import CLOSING_LIFECYCLE_EVENTS, MOVE_BLOCKING_FILES, JsonObject
from .records import (
    current_unit,
    latest_of_kind,
    open_blockers,
    open_verifications,
    read_events,
)


TRACKED_ARTIFACTS = MOVE_BLOCKING_FILES + (
    "contexts.md",
    "verification.md",
    "review.md",
    "report.md",
)


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
        "latestVerification": _latest_verification(events),
        "openVerifications": _open_verifications(events),
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
    return [_summarize(entry) for entry in open_blockers(events)]


def _approvals(events: list[JsonObject]) -> list[JsonObject]:
    return [
        {
            "seq": entry.get("seq"),
            "action": entry.get("data", {}).get("action"),
            "actor": entry.get("actor"),
            "summary": entry.get("summary"),
        }
        for entry in events
        if entry.get("kind") == "approval"
    ]


def _verification(events: list[JsonObject]) -> JsonObject | None:
    """The verdict that stands for the unit, not merely the newest one.

    A completion claim rests on every criterion, so while any FAIL or
    INCONCLUSIVE is still unresolved this reads INCONCLUSIVE however the last
    run went — the state `templates/verification.md` says cannot be PASS. The
    newest event itself stays available as `latestVerification`; the two answer
    different questions and a reader should not have to reconstruct the first
    from `openVerifications`.
    """
    latest = _latest_verification(events)
    if latest is None:
        return None
    unresolved = open_verifications(events)
    if not unresolved:
        return latest
    return {
        "seq": latest["seq"],
        "verdict": "INCONCLUSIVE",
        "summary": latest["summary"],
        "downgradedBy": [entry.get("seq") for entry in unresolved],
    }


def _latest_verification(events: list[JsonObject]) -> JsonObject | None:
    latest = latest_of_kind(events, "verification")
    if latest is None:
        return None
    return {
        "seq": latest.get("seq"),
        "verdict": latest.get("data", {}).get("verdict"),
        "summary": latest.get("summary"),
    }


def _open_verifications(events: list[JsonObject]) -> list[JsonObject]:
    """Built here rather than through _summarize, which lastEvent and blockers share."""
    return [
        {
            "seq": entry.get("seq"),
            "verdict": entry.get("data", {}).get("verdict"),
            "summary": entry.get("summary"),
        }
        for entry in open_verifications(events)
    ]


def _status_changes(events: list[JsonObject], state: str) -> list[JsonObject]:
    """Confirmed or cancelled entries, readable without opening the log.

    The bare target seq used to be the whole answer, which meant a superseded
    decision could only be understood by going back to `audit.jsonl` for the text
    it replaced. What was reversed, and why, is the part a resuming session needs.
    """
    changes: list[JsonObject] = []
    for entry in events:
        if entry.get("kind") != "status-change":
            continue
        data = entry.get("data", {})
        if data.get("to") != state:
            continue
        target = data.get("target")
        if not isinstance(target, int) or isinstance(target, bool):
            continue
        changes.append(
            {
                "seq": target,
                "by": entry.get("seq"),
                "summary": _target_summary(events, target),
                "why": data.get("reason") or data.get("evidence"),
            }
        )
    return changes


def _target_summary(events: list[JsonObject], seq: int) -> str | None:
    for entry in events:
        if entry.get("seq") == seq:
            summary = entry.get("summary")
            return summary if isinstance(summary, str) else None
    return None


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
